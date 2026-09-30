import os
import subprocess
import sys

BACKUP_FILE = os.path.expanduser("~/.config/xsettings-clean.txt")
XSETTINGSD_CONF = os.path.expanduser("~/.xsettingsd")

def get_clean_settings():
    settings = {}
    try:
        result = subprocess.run(["dump_xsettings"], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line or line.startswith('#') or ' ' not in line:
                    continue
                parts = line.split(maxsplit=1)
                settings[parts[0]] = parts[1].strip('"')
    except:
        pass
    return settings

def save_and_sync(settings):
    try:
        if "Gtk/ThemeName" in settings:
            settings["Net/ThemeName"] = settings["Gtk/ThemeName"]
        if "Gtk/IconThemeName" in settings:
            settings["Net/IconThemeName"] = settings["Gtk/IconThemeName"]

        with open(BACKUP_FILE, "w") as f:
            for k, v in sorted(settings.items()):
                f.write(f"{k}={v}\n")
        
        with open(XSETTINGSD_CONF, "w") as f:
            for k, v in sorted(settings.items()):
                f.write(f"{k} {v}\n" if v.isdigit() else f'{k} "{v}"\n')
    except Exception as e:
        print(f"[ERRO] XSettings Sync: {e}", file=sys.stderr, flush=True)
