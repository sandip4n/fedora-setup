#!/usr/bin/env bash

__run() {
	eval $@
	if [[ $? -ne 0 ]]; then
		echo "error: $1 failed"
		exit 1
	fi
}

setup_sys__gdmlogin() {
	read -r -d "" CMD <<- EOM
	$(type -P gsettings) set org.gnome.desktop.interface clock-format "24h"
	$(type -P gsettings) set org.gnome.desktop.interface clock-show-weekday true
	$(type -P gsettings) set org.gnome.desktop.interface color-scheme "prefer-dark"
	$(type -P rpm) -q --quiet fira-code-fonts && $(type -P gsettings) set org.gnome.desktop.interface font-name "Fira Code Regular 11"
	$(type -P gsettings) set org.gnome.desktop.interface gtk-theme "Adwaita-dark"
	$(type -P rpm) -q --quiet papirus-icon-theme && $(type -P gsettings) set org.gnome.desktop.interface icon-theme "Papirus"
	$(type -P gsettings) set org.gnome.desktop.interface scaling-factor 1
	$(type -P gsettings) set org.gnome.desktop.interface text-scaling-factor "1.0"
	$(type -P gsettings) set org.gnome.desktop.peripherals.touchpad tap-to-click true
	$(type -P gsettings) set org.gnome.settings-daemon.plugins.color night-light-enabled false
	EOM

	sudo install -dpv -o gdm -g gdm /var/lib/gdm/.cache
	sudo install -dpv -o gdm -g gdm -m 0700 /var/lib/gdm/.config
	sudo install -dpv -o gdm -g gdm -m 0700 /var/lib/gdm/.local
	machinectl -q shell gdm@ $(type -P dbus-launch) $(type -P bash) -c "$CMD"
}

setup_sys__journals() {
	__run journalctl --vacuum-time 0
}

setup_sys__packages() {
	__run dnf -y upgrade --refresh

	__run dnf -y install \
		https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm \
		https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm

	__run dnf -y config-manager setopt fedora-cisco-openh264.enabled=1

	__run dnf -y update @core

	__run dnf -y install rpmfusion-\*-appstream-data

	__run dnf -y swap ffmpeg-free ffmpeg --allowerasing
	__run dnf -y update @multimedia --setopt="install_weak_deps=False" --exclude=PackageKit-gstreamer-plugin

	__run dnf -y install cascadia-code-fonts
	__run dnf -y install gnome-extensions-app gnome-shell-extension-dash-to-dock gnome-tweak-tool
	__run dnf -y install papirus-icon-theme
	__run dnf -y install p7zip p7zip-plugins
	__run dnf -y install systemd-container dbus-x11
	__run dnf -y autoremove
	__run dnf -y clean all
}

setup_sys__timedate() {
	__run timedatectl set-local-rtc false
	__run timedatectl set-ntp true
}

if [[ $EUID -ne 0 ]]; then
	echo "info: retrying with sudo"
	pkexec bash $(realpath "$0") $@
	exit $?
fi

setup_sys__packages
setup_sys__timedate
setup_sys__gdmlogin
setup_sys__journals

echo "info: reboot before continuing"
read -n 1 -s -r -p "press any key to continue"
