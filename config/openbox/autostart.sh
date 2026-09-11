#!/bin/env bash

# Settings
nippy-settings-daemon &

# Wallpaper
bash $HOME/.fehbg &

## Mate Polkit
/usr/libexec/polkit-mate-authentication-agent-1 &
/usr/libexec/gvfsd &

if [ -z "$XDG_RUNTIME_DIR" ]; then
	export XDG_RUNTIME_DIR=/run/user/$(id -u)
fi

# Pipewire
pipewire &

## Picom
picom &

## Polybar
polybar -r &

## Conky
conky &

## Clippy
nippy-clippy-daemon &
