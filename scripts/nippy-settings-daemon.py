#!/usr/bin/env python3
import os
import subprocess
import sys
import threading
import time
from Xlib import X, display

BACKUP_FILE = os.path.expanduser("~/.config/xsettings-clean.txt")
XSETTINGSD_CONF = os.path.expanduser("~/.xsettingsd")
PIPE_FILE = os.path.expanduser("~/.config/xsettings-control")

current_settings = {}

def get_clean_settings():
    """Lê as configurações atuais expostas no servidor X via dump_xsettings."""
    settings = {}
    try:
		## Rodando o dump_xsettings para ler as configurações do X
        result = subprocess.run(["dump_xsettings"], capture_output=True, text=True, check=True)
        
        ## Separando as Strings em uma Lista de Linhas
        for line in result.stdout.splitlines():
            line = line.strip()
            
            if not line or line.startswith('#'):
                continue
            parts = line.split(maxsplit=1)
            
            if len(parts) == 2:
                key, val = parts[0], parts[1].strip('"')
                settings[key] = val
    except Exception as e:
        print(f"[ERROR] Failed to execute dump_xsettings: {e}", file=sys.stderr, flush=True)
    return settings

def save_and_sync(settings):
    """Salva o backup limpo e atualiza o arquivo de configuração do xsettingsd."""
    try:
        with open(BACKUP_FILE, "w") as f:
            for key, val in sorted(settings.items()):
                f.write(f"{key}={val}\n")
        
        with open(XSETTINGSD_CONF, "w") as f:
            for key, val in sorted(settings.items()):
                if not val.isdigit():
                    f.write(f'{key} "{val}"\n')
                else:
                    f.write(f'{key} {val}\n')
    except Exception as e:
        print(f"[ERROR] Failed to write configuration files: {e}", file=sys.stderr, flush=True)

def apply_saved_settings():
    """Restaura o XSettings no início da sessão do Openbox."""
    if not os.path.exists(BACKUP_FILE):
        print("[INFO] No backup found to restore", flush=True)
        return

    print("[INFO] Restoring saved settings...", flush=True)
    subprocess.run(["killall", "-HUP", "xsettingsd"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.Popen(["xsettingsd"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def check_and_log_changes():
    """Compara o estado antigo com o novo e exibe as alterações no terminal."""
    global current_settings
    new_settings = get_clean_settings()
    
    if not current_settings:
        current_settings = new_settings
        print("[INFO] Daemon started. Monitoring XSettings...", flush=True)
        save_and_sync(new_settings)
        return

    changes_detected = False
    for key, value in new_settings.items():
        if key not in current_settings:
            print(f"[CHANGE] Configuration added -> {key}: {value}", flush=True)
            changes_detected = True
        elif current_settings[key] != value:
            print(f"[CHANGE] {key}: '{current_settings[key]}' -> '{value}'", flush=True)
            changes_detected = True

    for key in list(current_settings.keys()):
        if key not in new_settings:
            print(f"[CHANGE] Configuration removed -> {key}", flush=True)
            changes_detected = True

    if changes_detected:
        current_settings = new_settings
        save_and_sync(new_settings)

def listen_for_commands():
    """Thread secundária que escuta comandos externos vindos do Named Pipe."""
    # Cria o Named Pipe se ele não existir
    if os.path.exists(PIPE_FILE):
        os.remove(PIPE_FILE)
    os.mkfifo(PIPE_FILE)
    
    print(f"[INFO] Listening for changes in: {PIPE_FILE}", flush=True)
    
    while True:
        # O open() em um FIFO bloqueia a execução até que alguém envie dados
        with open(PIPE_FILE, "r") as fifo:
            for line in fifo:
                line = line.strip()
                if not line or "=" in line or " " not in line:
                    continue
                
                # Suporta formatos "Chave Valor" ou "Chave=Valor" mudando o separador se necessário
                parts = line.split(maxsplit=1)
                key, val = parts[0], parts[1].strip('"')
                
                print(f"[COMMAND] Remote change requested -> {key}: {val}", flush=True)
                
                # Atualiza nosso mapa local na memória
                current_settings[key] = val
                
                # Salva nos arquivos do sistema (~/.xsettingsd e backup)
                save_and_sync(current_settings)
                
                # Recarrega o daemon xsettingsd para aplicar a mudança visual imediatamente
                subprocess.run(["killall", "-HUP", "xsettingsd"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    if not os.environ.get("DISPLAY"):
        print("[ERROR] DISPLAY variable not found in the environment.", file=sys.stderr, flush=True)
        sys.exit(1)

    # 1. Aplica as configurações do último boot
    apply_saved_settings()
    check_and_log_changes()

    # 2. Inicia a thread que ouve o terminal/comandos externos
    cmd_thread = threading.Thread(target=listen_for_commands, daemon=True)
    cmd_thread.start()

    # 3. Mantém o loop principal escutando alterações nativas do X11
    d = display.Display()
    root = d.screen().root
    root.change_attributes(event_mask=X.PropertyChangeMask)
    
    while True:
        ev = d.next_event()
        if ev.type == X.PropertyNotify and ev.atom == d.get_atom('_XSETTINGS_SETTINGS'):
            check_and_log_changes()

if __name__ == "__main__":
    main()
