#!/usr/bin/env python3
"""
powerd - daemon de energia para Linux (fase 1: monitor de bateria).

* Lê as baterias pelo UPower (barramento de SISTEMA).
* Avisa o usuário via org.freedesktop.Notifications (barramento de SESSÃO).
* Funciona com 0, 1, 2 (ou mais) baterias: a carga total é calculada somando
  a energia (Wh) de todas as baterias presentes, e baterias que entram/saem
  em tempo real (hot-swap) são tratadas pelos sinais DeviceAdded/DeviceRemoved.

Como precisa do barramento de sessão para notificar, ele deve rodar como
serviço de USUÁRIO: systemd (powerd.service) ou runit (runit/powerd/run).

Dependência:  dbus-next (pip) ou o fork compatível dbus-fast
              (Void Linux: xbps-install python3-dbus-fast)
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys
from dataclasses import dataclass
from enum import IntEnum

try:
    from dbus_next import BusType, Variant
    from dbus_next.aio import MessageBus
    from dbus_next.errors import DBusError
except ImportError:  # fork compatível e mantido (pacote python3-dbus-fast no Void)
    from dbus_fast import BusType, Variant
    from dbus_fast.aio import MessageBus
    from dbus_fast.errors import DBusError

log = logging.getLogger("powerd")

# --------------------------------------------------------------------- D-Bus
UPOWER_BUS = "org.freedesktop.UPower"
UPOWER_PATH = "/org/freedesktop/UPower"
UPOWER_IFACE = "org.freedesktop.UPower"
DEVICE_IFACE = "org.freedesktop.UPower.Device"
PROPS_IFACE = "org.freedesktop.DBus.Properties"

NOTIF_BUS = "org.freedesktop.Notifications"
NOTIF_PATH = "/org/freedesktop/Notifications"
NOTIF_IFACE = "org.freedesktop.Notifications"

UP_DEVICE_KIND_BATTERY = 2  # UpDeviceKind: 2 = bateria
URGENCIA_NORMAL = 1
URGENCIA_CRITICA = 2


class Nivel(IntEnum):
    NORMAL = 0
    BAIXA = 1
    CRITICA = 2


@dataclass
class Resumo:
    """Visão agregada de todas as baterias."""
    percentual: float
    na_bateria: bool                      # True = sem carregador (UPower OnBattery)
    tempo_restante: int                   # segundos; 0 = desconhecido
    detalhes: list[tuple[str, float]]     # [(nome, %), ...] de cada bateria


def formatar_duracao(segundos: int) -> str:
    minutos = max(1, round(segundos / 60))
    horas, minutos = divmod(minutos, 60)
    return f"{horas} h {minutos:02d} min" if horas else f"{minutos} min"


# ------------------------------------------------------------------- Bateria
class Bateria:
    """Uma bateria física exposta pelo UPower, mantida atualizada por sinais."""

    def __init__(self, path: str, props, ao_mudar):
        self.path = path
        self._props = props
        self._ao_mudar = ao_mudar
        self.dados: dict = {}
        # Guardamos a referência: o mesmo objeto é usado em on_/off_.
        self._callback = self._propriedades_mudaram

    @classmethod
    async def abrir(cls, bus: MessageBus, path: str, ao_mudar) -> "Bateria | None":
        """Retorna a bateria, ou None se o dispositivo não for uma bateria do sistema."""
        intro = await bus.introspect(UPOWER_BUS, path)
        obj = bus.get_proxy_object(UPOWER_BUS, path, intro)
        props = obj.get_interface(PROPS_IFACE)

        bateria = cls(path, props, ao_mudar)
        await bateria.recarregar()
        if not bateria.eh_bateria_do_sistema:
            return None
        props.on_properties_changed(bateria._callback)
        return bateria

    async def recarregar(self) -> None:
        bruto = await self._props.call_get_all(DEVICE_IFACE)
        self.dados = {chave: valor.value for chave, valor in bruto.items()}

    def _propriedades_mudaram(self, interface, alteradas, invalidadas) -> None:
        if interface != DEVICE_IFACE:
            return
        for chave, valor in alteradas.items():
            self.dados[chave] = valor.value
        self._ao_mudar()

    def fechar(self) -> None:
        try:
            self._props.off_properties_changed(self._callback)
        except Exception:  # o dispositivo pode já ter sumido do barramento
            pass

    # -- atalhos para as propriedades do UPower
    @property
    def eh_bateria_do_sistema(self) -> bool:
        # Ignora baterias de periféricos (mouse, teclado, celular...)
        return (self.dados.get("Type") == UP_DEVICE_KIND_BATTERY
                and bool(self.dados.get("PowerSupply", False)))

    @property
    def nome(self) -> str:
        return self.dados.get("NativePath") or self.path.rsplit("/", 1)[-1]

    @property
    def presente(self) -> bool:
        return bool(self.dados.get("IsPresent", False))

    @property
    def energia(self) -> float:          # Wh atuais
        return float(self.dados.get("Energy", 0.0))

    @property
    def energia_cheia(self) -> float:    # Wh com a bateria cheia
        return float(self.dados.get("EnergyFull", 0.0))

    @property
    def taxa(self) -> float:             # W (consumo ou carga)
        return float(self.dados.get("EnergyRate", 0.0))

    @property
    def percentual(self) -> float:
        return float(self.dados.get("Percentage", 0.0))


# ------------------------------------------------------------- Notificações
class Notificador:
    """Envia notificações pelo barramento de SESSÃO, reaproveitando o mesmo balão.

    A conexão é feita (e refeita, se cair) só na hora de notificar. Assim o
    daemon pode subir antes de o barramento de sessão ou o servidor de
    notificações (dunst, mako...) estarem prontos.
    """

    def __init__(self):
        self._bus: MessageBus | None = None
        self._iface = None
        self._id = 0

    async def _interface(self):
        if self._iface is None:
            if self._bus is None:
                self._bus = await MessageBus(bus_type=BusType.SESSION).connect()
            intro = await self._bus.introspect(NOTIF_BUS, NOTIF_PATH)
            obj = self._bus.get_proxy_object(NOTIF_BUS, NOTIF_PATH, intro)
            self._iface = obj.get_interface(NOTIF_IFACE)
        return self._iface

    def encerrar(self) -> None:
        """Descarta a conexão; a próxima notificação reconecta."""
        if self._bus is not None:
            try:
                self._bus.disconnect()
            except Exception:
                pass
        self._bus = self._iface = None

    async def enviar(self, titulo: str, corpo: str, urgencia: int, icone: str) -> bool:
        """Retorna True se a notificação foi entregue ao servidor."""
        try:
            iface = await self._interface()
            self._id = await iface.call_notify(
                "powerd", self._id, icone, titulo, corpo, [],
                {"urgency": Variant("y", urgencia),
                 "category": Variant("s", "device")},
                0 if urgencia == URGENCIA_CRITICA else 10_000,  # 0 = não expira
            )
            return True
        except Exception as e:
            log.warning("Não foi possível enviar a notificação: %s", e)
            self.encerrar()
            return False

    async def fechar(self) -> None:
        if not self._id:
            return
        try:
            iface = await self._interface()
            await iface.call_close_notification(self._id)
        except Exception as e:
            log.debug("Falha ao fechar notificação: %s", e)
        self._id = 0


# ------------------------------------------------------------------- Monitor
class Monitor:
    def __init__(self, sistema: MessageBus, notificador: Notificador,
                 limiar_baixa: int = 20, limiar_critica: int = 10,
                 histerese: int = 3):
        self.sistema = sistema
        self.notificador = notificador
        self.limiar_baixa = limiar_baixa
        self.limiar_critica = limiar_critica
        self.histerese = histerese

        self.baterias: dict[str, Bateria] = {}
        self.na_bateria = False
        self.nivel = Nivel.NORMAL

        self._upower = None
        self._upower_props = None
        self._abrindo: set[str] = set()
        self._tarefas: set[asyncio.Future] = set()
        self._lock = asyncio.Lock()

    # -- inicialização -------------------------------------------------------
    async def iniciar(self) -> None:
        intro = await self.sistema.introspect(UPOWER_BUS, UPOWER_PATH)
        obj = self.sistema.get_proxy_object(UPOWER_BUS, UPOWER_PATH, intro)
        self._upower = obj.get_interface(UPOWER_IFACE)
        self._upower_props = obj.get_interface(PROPS_IFACE)

        self.na_bateria = bool(await self._upower.get_on_battery())

        self._upower_props.on_properties_changed(self._upower_mudou)
        self._upower.on_device_added(self._dispositivo_adicionado)
        self._upower.on_device_removed(self._dispositivo_removido)

        for path in await self._upower.call_enumerate_devices():
            await self._adicionar(path)

        if self.baterias:
            log.info("%d bateria(s) monitorada(s): %s", len(self.baterias),
                     ", ".join(sorted(b.nome for b in self.baterias.values())))
        else:
            log.info("Nenhuma bateria encontrada; aguardando (desktop ou bateria removida).")
        await self._avaliar()

    # -- eventos do UPower ---------------------------------------------------
    def _upower_mudou(self, interface, alteradas, invalidadas) -> None:
        if interface == UPOWER_IFACE and "OnBattery" in alteradas:
            self.na_bateria = bool(alteradas["OnBattery"].value)
            log.info("Fonte de energia: %s",
                     "bateria" if self.na_bateria else "carregador")
            self._agendar(self._avaliar())

    def _dispositivo_adicionado(self, path: str) -> None:
        self._agendar(self._adicionar(path, avaliar=True))

    def _dispositivo_removido(self, path: str) -> None:
        bateria = self.baterias.pop(path, None)
        if bateria:
            bateria.fechar()
            log.info("Bateria removida: %s", bateria.nome)
            self._agendar(self._avaliar())

    def _bateria_mudou(self) -> None:
        self._agendar(self._avaliar())

    async def _adicionar(self, path: str, avaliar: bool = False) -> None:
        if path in self.baterias or path in self._abrindo:
            return
        self._abrindo.add(path)
        try:
            bateria = await Bateria.abrir(self.sistema, path, self._bateria_mudou)
        except (DBusError, OSError) as e:  # o dispositivo pode sumir durante a leitura
            log.debug("Ignorando %s: %s", path, e)
            return
        finally:
            self._abrindo.discard(path)

        if bateria is None:
            return
        self.baterias[path] = bateria
        log.info("Bateria detectada: %s (%.0f%%)", bateria.nome, bateria.percentual)
        if avaliar:
            await self._avaliar()

    # -- lógica --------------------------------------------------------------
    def _resumo(self) -> Resumo | None:
        presentes = sorted((b for b in self.baterias.values() if b.presente),
                           key=lambda b: b.nome)
        if not presentes:
            return None

        energia = sum(b.energia for b in presentes)
        cheia = sum(b.energia_cheia for b in presentes)
        if cheia > 0:
            # Soma de Wh: correto mesmo com baterias de capacidades diferentes
            # (ex.: ThinkPad com bateria interna de 24 Wh + externa de 72 Wh).
            percentual = 100.0 * energia / cheia
        else:
            percentual = sum(b.percentual for b in presentes) / len(presentes)

        taxa = sum(b.taxa for b in presentes)
        tempo = int(energia / taxa * 3600) if self.na_bateria and taxa > 0 else 0

        return Resumo(
            percentual=min(percentual, 100.0),
            na_bateria=self.na_bateria,
            tempo_restante=tempo,
            detalhes=[(b.nome, b.percentual) for b in presentes],
        )

    def _calcular_nivel(self, r: Resumo) -> Nivel:
        if not r.na_bateria:
            return Nivel.NORMAL
        # Histerese: para "sair" de um nível é preciso subir alguns pontos,
        # evitando avisos repetidos quando o valor oscila perto do limiar.
        h = self.histerese
        lim_critica = self.limiar_critica + (h if self.nivel == Nivel.CRITICA else 0)
        lim_baixa = self.limiar_baixa + (h if self.nivel >= Nivel.BAIXA else 0)
        if r.percentual <= lim_critica:
            return Nivel.CRITICA
        if r.percentual <= lim_baixa:
            return Nivel.BAIXA
        return Nivel.NORMAL

    async def _avaliar(self) -> None:
        async with self._lock:
            resumo = self._resumo()
            if resumo is None:
                self.nivel = Nivel.NORMAL
                return

            novo = self._calcular_nivel(resumo)
            log.debug("carga=%.1f%% na_bateria=%s nivel=%s->%s",
                      resumo.percentual, resumo.na_bateria,
                      self.nivel.name, novo.name)
            anterior, self.nivel = self.nivel, novo

            if novo > anterior:                       # só avisa quando PIORA
                if not await self._notificar(novo, resumo):
                    self.nivel = anterior             # falhou: tenta de novo no próximo evento
            elif novo == Nivel.NORMAL and anterior != Nivel.NORMAL:
                await self.notificador.fechar()       # carregador conectado

    async def _notificar(self, nivel: Nivel, r: Resumo) -> bool:
        restante = f"{r.percentual:.0f}%"
        if r.tempo_restante:
            restante += f" (~{formatar_duracao(r.tempo_restante)})"
        corpo = f"Carga restante: {restante}."
        if len(r.detalhes) > 1:
            corpo += "\n" + " · ".join(f"{n}: {p:.0f}%" for n, p in r.detalhes)

        if nivel == Nivel.CRITICA:
            titulo, icone, urgencia = ("Bateria criticamente baixa",
                                       "battery-caution", URGENCIA_CRITICA)
            corpo += "\nConecte o carregador agora."
        else:
            titulo, icone, urgencia = ("Bateria baixa",
                                       "battery-low", URGENCIA_NORMAL)
            corpo += "\nConecte o carregador."

        log.info("%s - %.0f%%", titulo, r.percentual)
        return await self.notificador.enviar(titulo, corpo, urgencia, icone)

    # -- utilidades ----------------------------------------------------------
    def _agendar(self, coro) -> None:
        tarefa = asyncio.ensure_future(coro)
        self._tarefas.add(tarefa)
        tarefa.add_done_callback(self._tarefa_concluida)

    def _tarefa_concluida(self, tarefa: asyncio.Future) -> None:
        self._tarefas.discard(tarefa)
        if not tarefa.cancelled() and tarefa.exception():
            log.error("Erro em tarefa do monitor", exc_info=tarefa.exception())


# ---------------------------------------------------------------------- main
def analisar_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="powerd - daemon de energia")
    p.add_argument("--baixa", type=int, default=20,
                   help="%% para o aviso de bateria baixa (padrão: 20)")
    p.add_argument("--critica", type=int, default=10,
                   help="%% para o aviso de bateria crítica (padrão: 10)")
    p.add_argument("--debug", action="store_true", help="logs detalhados")
    args = p.parse_args()
    if not 0 < args.critica < args.baixa <= 100:
        p.error("é preciso respeitar: 0 < crítica < baixa <= 100")
    return args


async def principal(args: argparse.Namespace) -> int:
    notificador = Notificador()   # conecta ao barramento de sessão sob demanda
    try:
        sistema = await MessageBus(bus_type=BusType.SYSTEM).connect()
        monitor = Monitor(sistema, notificador,
                          limiar_baixa=args.baixa, limiar_critica=args.critica)
        await monitor.iniciar()
    except (DBusError, OSError) as e:
        log.error("Não foi possível falar com o UPower pelo barramento de sistema "
                  "(serviço dbus ativo? upower instalado?): %s", e)
        return 1

    parar = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sinal in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sinal, parar.set)

    await parar.wait()
    log.info("Encerrando.")
    sistema.disconnect()
    notificador.encerrar()
    return 0


if __name__ == "__main__":
    argumentos = analisar_args()
    logging.basicConfig(level=logging.DEBUG if argumentos.debug else logging.INFO,
                        format="%(levelname)s %(message)s")
    sys.exit(asyncio.run(principal(argumentos)))
