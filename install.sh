#! /bin/env bash
set -e

LightDMBack="Autumn Countryside Landscape.png"

if [[ "$1" == "chroot" ]]; then
	echo "## Chroot: YES"
	svFolder="/etc/runit/runsvdir/default"
else
	svFolder="/var/service"
fi

checkFolders () {
	echo -e "\n## Verificando Diretórios..."
	mkdir -p $HOME/.local/bin
	mkdir -p $HOME/.config
	mkdir -p $HOME/.themes/nippybox
	mkdir -p $HOME/.local/lib/python3.14/site-packages/
}

updateSys () {
	echo -e "\n## Atualizando os Pacotes do Sistema..."
	sudo xbps-install -Syu
}

installXlibre () {
	echo -e "\n## Instalando o Servidor Gráfico X11"
	sleep 2
	sudo mkdir -p /etc/xbps.d
	printf "repository=https://github.com/xlibre-void/xlibre/releases/latest/download/" | sudo tee /etc/xbps.d/99-repository-xlibre.conf
	sudo xbps-install -Sy
	sudo xbps-install -Su xlibre
}

installDesktop () {
	echo -e "\n## Instalando Pacotes Básicos do Nippybox..."
	sleep 2
	sudo xbps-install -y openbox obconf polybar rofi libnotify dunst feh picom xcompmgr xdg-user-dirs acpi pulsemixer bash-completion bluez-utils redshift curl qt5ct qt6ct noto-fonts-emoji void-repo-nonfree obmenu-generator polkit mate-polkit elogind psmisc cantarell-fonts xsettingsd xmodmap xinput setxkbmap xkeyboard-config

	echo -e "\n## Instalando dependências dos Scripts"
	sleep 2
	sudo xbps-install -y maim xclip slop ffmpeg playerctl brightnessctl xcolor

	echo -e "\n ## Instalando Pipewire..."
	sleep 2
	sudo xbps-install -y pipewire wireplumber pipewire-pulse alsa-utils
}

installApps () {
	echo -e "\n ## Instalando Aplicativos Básicos..."
	sleep 2
	sudo xbps-install -y nano fastfetch Thunar alacritty geany pavucontrol viewnior network-manager-applet blueman gvfs qterminal 
	
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
	
	echo "## Instalando Suporte ao Flatpak..."
	sleep 2
	sudo xbps-install -y flatpak xdg-desktop-portal-gtk 

	echo "## Instalando Outros Pacotes Extras..."
	sleep 2
	sudo xbps-install -y libgepub libgsf libopenraw poppler-glib freetype2 papirus-icon-theme starship

	echo "## Instalando Módulos do Python..."
	sleep 2
	sudo xbps-install -y python3-pip python3-pipx python3-Pillow python3-xlib python3-psutil
	sudo pipx install pyperclip dbus_next --global
	
	echo -e "\n## Instalando o LightDM..."
	sleep 2
	sudo xbps-install -y lightdm lightdm-gtk-greeter

}

installTLP () {
	if ! [ -z "$(ls /sys/class/power_supply/)" ]; then
		echo "## Instalando o TLP..."
		sudo xbps-install -y tlp tlp-pd	
		
		echo "## Ativando o TLP"
		sudo ln -s /etc/sv/tlp $svFolder/
	fi
}

installFonts () {
	echo -e "\n## Instalando as Fontes..."
	sudo cp fonts/* /usr/share/fonts
	sudo fc-cache -fv
}

copyConfigs () {
	echo -e "## Copiando as Configurações..."
	cp -r config/* $HOME/.config/
	cp -r home/* $HOME/

	echo "## Copiando Temas..."
	cp -r themes/* $HOME/.themes/
	tar -xzvf themes.tar.gz
	cp -r themes/Catppuccin* /usr/share/themes

	echo "## Copiando Scripts..."
	cp -r scripts/* $HOME/.local/bin/
	chmod +x $HOME/.local/bin/*
	
	echo "## Copiando Bibliotecas..."
	cp -r libs/* $HOME/.local/lib/python3.14/site-packages/
}

enableServices () {
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
	
	echo "## Ativando o Bluetooth"
	sudo ln -s /etc/sv/bluetoothd $svFolder/	
	
	echo "## Ativando o CUPS"
	sudo ln -s /etc/sv/cupsd $svFolder/
	
	echo "## Ativando o LightDM"
	sudo ln -s /etc/sv/lightdm $svFolder/
}

finalConfigs () {
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
	
	echo "## Gerando o .xinitrc..."
	{
		cat <<EOF
#!/bin/bash

XDG_SESSION_TYPE=x11
exec openbox-session

EOF
	} > $HOME/.xinitrc	
	
	echo "## Apagando Cache"
	sudo rm /var/cache/xbps/*	
}

checkFolders
updateSys
installXlibre
installDesktop
installApps
installFonts
enableServices
installTLP

copyConfigs
finalConfigs
