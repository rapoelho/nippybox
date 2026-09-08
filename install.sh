#!/usr/bin/env bash
set -e

LightDMBack="Autumn Countryside Landscape.png"
log="/tmp/log.txt"
xsettingsDaemon="$HOME/.config/xsettings-clean.txt"
xsettingsConfig="$HOME/.xsettingsd"

if [[ "$1" == "chroot" ]]; then
	echo "## Chroot: YES"
	svFolder="/etc/runit/runsvdir/default"
else
	svFolder="/var/service"
fi

OndeEstou=$(dirname "$0")
if [[ "$OndeEstou" == "." ]]; then
    OndeEstou=$(pwd)
fi

verificarDiretorios () {
	echo -e "\n## Verificando Diretórios..."
	mkdir -p $HOME/.local/bin
	mkdir -p $HOME/.local/share/plank/themes/Nippy
	mkdir -p $HOME/.config
	mkdir -p $HOME/.themes/nippybox
	mkdir -p $HOME/.local/lib/python3.14/site-packages
	
	echo "Diretorios=OK" > "$log"
}

instalarPacotes () {
	echo -e "\n## Atualizando os Pacotes do Sistema..."
	sudo xbps-install -Syu
	
	echo -e "\n## Instalando o Servidor Gráfico X11"
	sleep 2
	sudo mkdir -p /etc/xbps.d
	printf "repository=https://github.com/xlibre-void/xlibre/releases/latest/download/" | sudo tee /etc/xbps.d/99-repository-xlibre.conf
	sudo xbps-install -Sy
	sudo xbps-install -Su xlibre
	
	#sudo pacman -S xorg --noconfirm --needed
	
	echo -e "\n## Instalando Pacotes Básicos do Nippybox..."
	sleep 2
	sudo xbps-install -y openbox obconf polybar rofi libnotify dunst feh picom xcompmgr xdg-user-dirs acpi pulsemixer bash-completion bluez-utils redshift curl qt5ct qt6ct noto-fonts-emoji void-repo-nonfree obmenu-generator polkit mate-polkit elogind psmisc cantarell-fonts xsettingsd xmodmap xinput setxkbmap xkeyboard-config
	
	#~ sudo xbps-install -y xfce4-settings xfce4-power-manager xfce4-terminal
	
	echo -e "\n## Instalando dependências dos Scripts"
	sleep 2
	sudo xbps-install -y pywal maim xclip slop ffmpeg playerctl brightnessctl xcolor
	
	echo -e "\n ## Instalando Aplicativos Básicos..."
	sleep 2
	sudo xbps-install -y nano fastfetch Thunar alacritty geany pavucontrol viewnior network-manager-applet blueman gvfs qterminal 
	
	echo -e "\n ## Instalando Pipewire..."
	sleep 2
	sudo xbps-install -y pipewire wireplumber pipewire-pulse alsa-utils
	
	echo "PacotesBasicos=OK" >> "$log"
}

instalarExtras () {
	echo -e "\n## Instalando o LightDM..."
	sleep 2
	sudo xbps-install -y lightdm lightdm-gtk-greeter
	
	echo -e "\n## Instalando Aplicativos Extras..."
	sleep 2
	sudo xbps-install -y galculator xarchiver mpv mpv-mpris xreader firefox 
	
	echo -e "\n## Instalando Pacotes Extras para o Thunar..."
	sleep 2
	sudo xbps-install -y thunar-volman thunar-archive-plugin thunar-media-tags-plugin tumbler ffmpegthumbnailer webp-pixbuf-loader libwebp gvfs udisks2
	
	echo -e "\n## Instalando Codecs Multimídia..."
	sleep 2
	sudo xbps-install -y gst-plugins-ugly1 gst-plugins-good1 gst-plugins-base1 gst-plugins-bad1 gst-libav gstreamer 

	echo -e "\n## Instalando Suporte a Sistemas de Arquivos..."
	sleep 2
	sudo xbps-install -y ntfs-3g exfatprogs dosfstools
	
	echo -e "\n## Instalando o Suporte a Impressoras..."
	sleep 2
	sudo xbps-install -y cups sane libpoppler system-config-printer cups-pk-helper cups-filters foomatic-db foomatic-db-nonfree gutenprint

	echo -e "\n## Instalando o Suporte a Descompactadores de Arquivos..."
	sleep 2
	sudo xbps-install -y cpio lhasa lrzip lzip 7zip unzip unrar

	if ! [ -z "$(ls /sys/class/power_supply/)" ]; then
		echo "## Instalando o TLP..."
		sudo xbps-install -y tlp tlp-pd
	fi

	echo "## Instalando Suporte ao Flatpak..."
	sleep 2
	sudo xbps-install -y flatpak xdg-desktop-portal-gtk 

	echo "## Instalando Pacotes Outros Extras..."
	sleep 2
	sudo xbps-install -y libgepub libgsf libopenraw poppler-glib freetype2 papirus-icon-theme 

	echo "## Instalando Módulos do Python..."
	sleep 2
	sudo xbps-install -y python3-pip python3-pipx python3-Pillow python3-xlib python3-psutil
	sudo pipx install pyperclip dbus_next --global
	
	echo "PacotesExtras=OK" >> "$log"
}

instalarFontes () {
	echo -e "\n## Instalando as Fontes..."
	sudo cp fonts/* /usr/share/fonts
	sudo fc-cache -fv
	cd $ondeEstou
	
	echo "Fontes=OK" >> "$log"
}

copiarConfigs () {
	echo -e "## Copiando as Configurações..."
	cp -r $OndeEstou/config/* $HOME/.config/

	echo "## Copiando Temas..."
	cp -r $OndeEstou/themes/* $HOME/.themes/

	echo "## Copiando Scripts..."
	cp -r $OndeEstou/scripts/* $HOME/.local/bin/
	chmod +x $HOME/.local/bin/*
	
	echo "Configs=OK" >> "$log"
}

habilitandoServicos () {
	sleep 
	
	echo "## Apagando Cache"
	sudo rm /var/cache/xbps/*	
	
	echo "## Ativando o DBUS"
	sudo ln -s /etc/sv/dbus $svFolder/
	
	echo "## Ativando o Polkit"
	sudo ln -s /etc/sv/polkitd $svFolder/
	
	echo "## Ativando o elogind"
	sudo ln -s /etc/sv/elogind $svFolder/
	
	if [[ -f "/var/service/dhcpcd" ]]; then
		echo "## Desativando o DHCPCD"
		sudo rm $svFolder/dhcpcd
	fi
	
	if [[ -f "/var/service/wpa_supplicant" ]]; then
		echo "## Desativando o WPA Supplicant"
		sudo rm $svFolder/wpa_supplicant
	fi
	
	echo "## Ativando o Network Manager"
	sudo ln -s /etc/sv/NetworkManager $svFolder/
	
	echo "## Ativando o TLP"
	sudo ln -s /etc/sv/tlp $svFolder/
	
	echo "## Ativando o Bluetooth"
	sudo ln -s /etc/sv/bluetoothd $svFolder/	
	
	echo "## Ativando o CUPS"
	sudo ln -s /etc/sv/cupsd $svFolder/
	
	echo "## Ativando o LightDM"
	sudo ln -s /etc/sv/lightdm $svFolder/
}

finalizarConfig () {
	echo "## Adicionando os Usuários aos Grupos Necessários..."
	for u in $(awk -F: '$3 >= 1000 && $3 < 65534 {print $1}' /etc/passwd); do 
		sudo usermod -aG lpadmin,video,audio "$u"
	done
	
	echo "## Copiando Wallpapers para /usr/share/backgrounds..."
	sudo cp -r $OndeEstou/backgrounds /usr/share

	echo "## Definindo o Wallpaper do LightDM"
	sudo cp "/usr/share/backgrounds/$LightDMBack" /usr/share/pixmaps
	sudo mv "/usr/share/pixmaps/$LightDMBack" "/usr/share/pixmaps/background.png"
	sudo sed -i 's|^#\(background=.*\)|\1|' /etc/lightdm/lightdm-gtk-greeter.conf 
	sudo sed -i 's|^background=.*|background=/usr/share/pixmaps/background.png|' /etc/lightdm/lightdm-gtk-greeter.conf 
	
	echo "## Definindo o Tema do LightDM..."
	sudo sed -i 's|^#\(theme-name=.*\)|\1|' /etc/lightdm/lightdm-gtk-greeter.conf
	sudo sed -i 's|^theme-name=.*|theme-name=Catppuccin-Peach-Dark|' /etc/lightdm/lightdm-gtk-greeter.conf

	sudo sed -i 's|^#\(icon-theme-name=.*\)|\1|' /etc/lightdm/lightdm-gtk-greeter.conf
	sudo sed -i 's|^icon-theme-name=.*|icon-theme-name=Papirus-Dark|' /etc/lightdm/lightdm-gtk-greeter.conf
	
	echo "## Gerando as pastas do Usuário"
	xdg-user-dirs-update

	cat << EOF > "$xsettingsDaemon"
Gtk/CursorThemeName=Adwaita
Gtk/FontName=$FONTE_SISTEMA
Gtk/IconThemeName=$TEMA_ICONES
Gtk/ThemeName=$TEMA_GTK
Net/IconThemeName=$TEMA_ICONES
Net/ThemeName=$TEMA_GTK
EOF


	
	echo "## Aplicando Temas"
	#~ xfconf-query -c xsettings -p /Net/ThemeName -s "Dracula"
	#~ xfconf-query -c xsettings -p /Net/IconThemeName -s "Papirus-Dark"
	
	echo "## Aplicando Fonte"
	#~ xfconf-query -c xsettings -p /Gtk/FontName -s "Cantarell 9"

	echo "## Arrumando os Aplicativos dos Menus..."
	sudo sed -i '$a\Hidden=true' /usr/share/applications/rofi*
	sudo sed -i '$a\Hidden=true' /usr/share/applications/picom.desktop

	echo "## Gerando o .xinitrc..."
	{
		cat <<EOF
#!/bin/bash

XDG_SESSION_TYPE=x11
exec openbox-session

EOF
	} > $HOME/.xinitrc

	echo "ConfigsFinais=OK" >> "$log"
}

temaPlank () {
	{
		cat <<EOF
		
[PlankDrawingTheme]
TopRoundness=6
BottomRoundness=6
LineWidth=0
OuterStrokeColor=41;;41;;41;;255
FillStartColor=0;;0;;0;;217
FillEndColor=0;;0;;0;;217
InnerStrokeColor=255;;255;;255;;255

EOF
	} > $HOME/.local/share/plank/themes/Nippy/hover.theme

	echo "TemaPlank=OK" >> "$log"
}

creditos () {
	echo -e "\nCréditos ao Aditya Shakya, que foi o responsável pelas personalizações do Rofi, da Polybar e de alguns dos Scripts que foram implementados no Nippybox"
}

echo -e "\nBem-vindo ao instalador do Nippybox!\nO Nippybox é uma personalização do Openbox com o objetivo de ser simples de usar em que juntei algumas coisas legais por aí e que me agradaram."

if [ -e "$log" ]; then
	source "$log"
	
	if ! [[ "$Diretorios" == "OK" ]]; then
		verificarDiretorios
	else
		echo "# Diretórios: OK"
	fi
	
	if ! [[ "$PacotesBasicos" == "OK" ]]; then
		instalarPacotes
	else
		echo "# Pacotes Básicos: OK"
	fi
	
	if ! [[ "$PacotesExtras" == "OK" ]]; then
		instalarExtras
	else
		echo "# Pacotes Extras: OK"
	fi
		
	if ! [[ "$Fontes" == "OK" ]]; then
		instalarFontes		
	else
		echo "# Fontes do Sistema: OK"
	fi
		
	if ! [[ "$Configs" == "OK" ]]; then
		copiarConfigs
	else
		echo "# Configurações: OK"
	fi
		
	if ! [[ "$aurHelper=OK" == "OK" ]]; then
		aurHelper
	else
		echo "# AUR Helper: $aurHelperFound"
	fi
		
	if ! [[ "$ConfigsFinais" == "OK" ]]; then
		finalizarConfig
	else
		echo "# Configurações Finais: OK"
	fi
		
	if ! [[ "$TemaPlank" == "OK" ]]; then
		temaPlank
	else
		echo "# Tema da Plank: OK"
	fi	
else
	verificarDiretorios
	instalarPacotes
	instalarExtras
	instalarFontes
	copiarConfigs
	aurHelper
	finalizarConfig
	temaPlank
	creditos
	sleep 5
	reboot
fi
