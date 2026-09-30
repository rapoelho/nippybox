import os
import subprocess
import sys

PERIPHERALS_BACKUP = os.path.expanduser("~/.config/peripherals-current.txt")

def apply_mouse_settings():
    if not os.path.exists(PERIPHERALS_BACKUP):
        # Taxa de repetição padrão segura se não houver arquivo
        subprocess.run(["xset", "r", "rate", "250", "50"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
                    # Busca apenas o ID numérico do touchpad de forma limpa
                    cmd = "xinput list --id-only | while read id; do xinput list --name-only $id | grep -qi 'touchpad' && echo $id; done"
                    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    for device_id in res.stdout.splitlines():
                        device_id = device_id.strip()
                        if device_id:
                            # Tenta ativar via propriedade padrão do libinput
                            subprocess.run(["xinput", "set-prop", device_id, "libinput Tapping Enabled", val], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            # Fallback para drivers sinaptics antigos se aplicável
                            subprocess.run(["xinput", "set-prop", device_id, "Synaptics Tap Action", "1", "1", "1", "1", "1", "1", "1"] if val == "1" else ["xinput", "set-prop", device_id, "Synaptics Tap Action", "0", "0", "0", "0", "0", "0", "0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # 2. Modo Canhoto / Destro (Inversão física de botões pelo Xmodmap)
                elif key == "mouse/left_handed":
                    if val == "1":
                        print("[PERIFÉRICO - INTERNO] Alterando para Modo Canhoto", flush=True)
                        # Inverte o botão 1 (esquerdo) com o 3 (direito) mantendo o scroll (4 5) intocado
                        subprocess.run(["xmodmap", "-e", "pointer = 3 2 1 4 5 6 7 8 9 10 11 12"])
                    else:
                        print("[PERIFÉRICO - INTERNO] Alterando para Modo Destro", flush=True)
                        # Restaura a ordem padrão dos ponteiros do X11
                        subprocess.run(["xmodmap", "-e", "pointer = default"])

                # 3. Repetição do Teclado
                elif key == "keyboard/repeat":
                    if " " in val:
                        delay, rate = val.split()
                        subprocess.run(["xset", "r", "rate", delay, rate])
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
