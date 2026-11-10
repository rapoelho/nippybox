import os
import subprocess
import sys

PERIPHERALS_BACKUP = os.path.expanduser("~/.config/peripherals-current.txt")
CONFIG_FILE = os.path.expanduser("~/.config/nippybox/config")

TRUTHY_VALUES = ("1", "true", "yes", "on")


def run_command(command):
    """Executa um comando de hardware sem poluir o terminal."""
    try:
        return subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as e:
        print(f"[ERRO PERIFÉRICO] Falha ao executar {command[0]}: {e}", file=sys.stderr, flush=True)
        return None


def capture_command(command):
    """Executa um comando e devolve a saída, ou None em caso de erro."""
    try:
        return subprocess.run(command, capture_output=True, text=True)
    except OSError as e:
        print(f"[ERRO PERIFÉRICO] Falha ao executar {command[0]}: {e}", file=sys.stderr, flush=True)
        return None


def is_enabled(value):
    return value.strip().lower() in TRUTHY_VALUES


def get_touchpad_ids():
    """Lista os IDs dos dispositivos cujo nome contém 'touchpad'."""
    result = capture_command(["xinput", "list", "--id-only"])
    if result is None or result.returncode != 0:
        return []

    touchpads = []
    for device_id in result.stdout.split():
        name = capture_command(["xinput", "list", "--name-only", device_id])
        if name is None or name.returncode != 0:
            continue
        if "touchpad" in name.stdout.lower().replace(" ", ""):
            touchpads.append(device_id)
    return touchpads


def set_touchpad_tap(enabled):
    """Ativa/desativa o clique por toque no libinput ou no Synaptics."""
    value = "1" if enabled else "0"
    # Synaptics Tap Action: 7 botões; 1 dedo = botão esquerdo.
    synaptics = ["1", "0", "0", "0", "0", "0", "0"] if enabled else ["0"] * 7

    for device_id in get_touchpad_ids():
        result = run_command(
            ["xinput", "set-prop", device_id, "libinput Tapping Enabled", value]
        )
        if result is not None and result.returncode == 0:
            continue

        # Fallback para drivers Synaptics antigos.
        run_command(
            ["xinput", "set-prop", device_id, "Synaptics Tap Action"] + synaptics
        )


def sync_left_handed_config(enabled):
    """Mantém o lefthanded do config igual ao estado salvo pelo daemon."""
    value = "true" if enabled else "false"
    try:
        lines = []
        found = False

        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                lines = f.readlines()

        for index, line in enumerate(lines):
            if line.strip().startswith("lefthanded="):
                lines[index] = f"lefthanded={value}\n"
                found = True
                break

        if not found:
            lines.append(f"lefthanded={value}\n")

        with open(CONFIG_FILE, "w") as f:
            f.writelines(lines)
    except Exception as e:
        print(f"[ERRO PERIFÉRICO] Falha ao sincronizar lefthanded no config: {e}", file=sys.stderr, flush=True)


def apply_mouse_settings():
    if not os.path.exists(PERIPHERALS_BACKUP):
        # Taxa de repetição padrão segura se não houver arquivo
        run_command(["xset", "r", "rate", "250", "50"])
        return

    print("[PERIFÉRICO - INTERNO] Aplicando regras de hardware salvas...", flush=True)
    try:
        with open(PERIPHERALS_BACKUP, "r") as f:
            for line in f:
                if "=" not in line:
                    continue
                key, val = line.strip().split("=", 1)
                key = key.strip().lower()
                val = val.strip().strip('"')

                # 1. Ajuste do Touchpad (Clique por toque)
                if key == "mouse/touchpad_tap":
                    set_touchpad_tap(is_enabled(val))

                # 2. Modo Canhoto / Destro (Inversão física de botões pelo Xmodmap)
                elif key == "mouse/left_handed":
                    if is_enabled(val):
                        print("[PERIFÉRICO - INTERNO] Alterando para Modo Canhoto", flush=True)
                        # Inverte o botão 1 (esquerdo) com o 3 (direito) mantendo o scroll (4 5) intocado
                        run_command(["xmodmap", "-e", "pointer = 3 2 1"])
                    else:
                        print("[PERIFÉRICO - INTERNO] Alterando para Modo Destro", flush=True)
                        # Restaura a ordem padrão dos ponteiros do X11
                        run_command(["xmodmap", "-e", "pointer = 1 2 3"])

                # 3. Repetição do Teclado
                elif key == "keyboard/repeat":
                    parts = val.split()
                    if len(parts) == 2:
                        run_command(["xset", "r", "rate", parts[0], parts[1]])
                    else:
                        print(f"[ERRO PERIFÉRICO] Valor inválido para {key}: {val}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[ERRO PERIFÉRICO] Falha ao executar comandos de hardware: {e}", file=sys.stderr, flush=True)


def save_peripheral_state(key, val):
    state = {}
    key = key.strip().lower()
    val = val.strip().strip('"')

    if os.path.exists(PERIPHERALS_BACKUP):
        try:
            with open(PERIPHERALS_BACKUP, "r") as f:
                for line in f:
                    if "=" in line:
                        k, v = line.strip().split("=", 1)
                        state[k.strip().lower()] = v.strip()
        except Exception as e:
            print(f"[ERRO PERIFÉRICO] Falha ao ler histórico: {e}", file=sys.stderr, flush=True)

    state[key] = val
    try:
        with open(PERIPHERALS_BACKUP, "w") as f:
            for k, v in sorted(state.items()):
                f.write(f"{k}={v}\n")
    except Exception as e:
        print(f"[ERRO PERIFÉRICO] Falha ao gravar arquivo: {e}", file=sys.stderr, flush=True)

    # Mantém o lefthanded do config em sincronia com o estado salvo.
    if key == "mouse/left_handed":
        sync_left_handed_config(is_enabled(val))
