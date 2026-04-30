#!/usr/bin/env bash

__run() {
	eval $@
	if [[ $? -ne 0 ]]; then
		echo "error: $1 failed"
		exit 1
	fi
}

setup_sys__gdmlogin() {
	read -r -d "" PROFILE <<-EOM
		user-db:user
		system-db:gdm
		file-db:/usr/share/gdm/greeter-dconf-defaults
	EOM

	if [[ ! -f /etc/dconf/profile/gdm ]]; then
		echo "info: creating \"gdm\" dconf profile"
		echo "$PROFILE" >/etc/dconf/profile/gdm
	fi

	read -r -d "" SETTINGS <<-EOM
		[org/gnome/desktop/interface]
		clock-format='24h'
		clock-show-weekday=true
		color-scheme='prefer-dark'
		font-name='Cascadia Code Regular 11'
		gtk-theme='Adwaita-dark'
		icon-theme='Papirus'
		text-scaling-factor=1.0

		[org/gnome/desktop/peripherals/touchpad]
		tap-to-click=true

		[org/gnome/settings-daemon/plugins/color]
		night-light-enabled=false
	EOM

	if [[ ! -f /etc/dconf/db/gdm.d/95-settings ]]; then
		echo "info: writing \"gdm\" dconf settings"
		echo "$SETTINGS" >/etc/dconf/db/gdm.d/95-settings
		dconf update
	fi

	cp "$(getent passwd "${SUDO_USER:-$(id -un $PKEXEC_UID)}" | cut -d: -f6)/.config/monitors.xml" /etc/xdg/monitors.xml
}

setup_sys__journals() {
	__run journalctl --vacuum-time 0
}

setup_sys__packages() {
	__run "pkcon -y refresh force || [[ \$? -eq 5 ]]"
	__run "pkcon -y update || [[ \$? -eq 5 ]]"

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
	__run dnf -y install gimp
	__run dnf -y autoremove
	__run dnf -y clean all
}

setup_sys__timedate() {
	__run timedatectl set-local-rtc false
	__run timedatectl set-ntp true
}

if [[ $EUID -ne 0 ]]; then
	echo "error: retry with sudo"
	exit 1
fi

setup_sys__packages
setup_sys__timedate
setup_sys__gdmlogin
setup_sys__journals

echo "info: reboot before continuing"
read -n 1 -s -r -p "press any key to continue"
