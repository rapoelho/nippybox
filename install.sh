#! /bin/env bash
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

whereIam=$(dirname "$0")
if [[ "$OndeEstou" == "." ]]; then
    whereIam=$(pwd)
fi

