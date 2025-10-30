#!/usr/bin/env bash

__run() {
	eval $@
	if [[ $? -ne 0 ]]; then
		echo "error: $1 failed"
		exit 1
	fi
}

setup_usr__desktop() {
	# See https://gitlab.gnome.org/GNOME/gsettings-desktop-schemas/blob/main/schemas/org.gnome.desktop.background.gschema.xml.in
	gsettings set org.gnome.desktop.background picture-opacity 100
	gsettings set org.gnome.desktop.background picture-uri "file:///usr/share/backgrounds/gnome/blobs-l.svg"
	gsettings set org.gnome.desktop.background picture-uri-dark "file:///usr/share/backgrounds/gnome/blobs-d.svg"
	gsettings set org.gnome.desktop.background show-desktop-icons false

	# See https://gitlab.gnome.org/GNOME/gsettings-desktop-schemas/blob/main/schemas/org.gnome.desktop.datetime.gschema.xml.in
	gsettings set org.gnome.desktop.datetime automatic-timezone false

	# See https://gitlab.gnome.org/GNOME/gsettings-desktop-schemas/blob/main/schemas/org.gnome.desktop.interface.gschema.xml.in
	gsettings set org.gnome.desktop.interface clock-format "24h"
	gsettings set org.gnome.desktop.interface clock-show-weekday true
	gsettings set org.gnome.desktop.interface color-scheme "prefer-dark"
	rpm -q --quiet fira-code-fonts && gsettings set org.gnome.desktop.interface document-font-name "Fira Code Regular 11"
	rpm -q --quiet fira-code-fonts && gsettings set org.gnome.desktop.interface font-name "Fira Code Regular 11"
	rpm -q --quiet gnome-themes-extra && gsettings set org.gnome.desktop.interface gtk-theme "Adwaita-dark"
	rpm -q --quiet papirus-icon-theme && gsettings set org.gnome.desktop.interface icon-theme "Papirus"
	rpm -q --quiet fira-code-fonts && gsettings set org.gnome.desktop.interface monospace-font-name "Fira Code Medium 11"
	gsettings set org.gnome.desktop.interface scaling-factor 1
	gsettings set org.gnome.desktop.interface text-scaling-factor "1.0"

	# See https://gitlab.gnome.org/GNOME/gsettings-desktop-schemas/blob/main/schemas/org.gnome.desktop.peripherals.gschema.xml.in
	gsettings set org.gnome.desktop.peripherals.touchpad click-method "areas"
	gsettings set org.gnome.desktop.peripherals.touchpad tap-to-click true
	gsettings set org.gnome.desktop.peripherals.touchpad two-finger-scrolling-enabled true

	# See https://gitlab.gnome.org/GNOME/gsettings-desktop-schemas/-/blob/main/schemas/org.gnome.desktop.sound.gschema.xml.in
	gsettings set org.gnome.desktop.sound allow-volume-above-100-percent false
	gsettings set org.gnome.desktop.sound event-sounds false
	gsettings set org.gnome.desktop.sound input-feedback-sounds false

	# See https://gitlab.gnome.org/GNOME/gsettings-desktop-schemas/-/blob/main/schemas/org.gnome.desktop.wm.preferences.gschema.xml.in
	gsettings set org.gnome.desktop.wm.preferences button-layout "appmenu:minimize,maximize,close"

	# See https://gitlab.gnome.org/GNOME/mutter/-/blob/main/data/org.gnome.mutter.gschema.xml.in
	gsettings set org.gnome.mutter dynamic-workspaces true

	# See https://gitlab.gnome.org/GNOME/nautilus/-/blob/main/data/org.gnome.nautilus.gschema.xml
	gsettings set org.gnome.nautilus.preferences default-sort-order "name"
	gsettings set org.gnome.nautilus.preferences fts-enabled false
	gsettings set org.gnome.nautilus.preferences show-image-thumbnails "never"

	# See https://gitlab.gnome.org/GNOME/gnome-settings-daemon/-/blob/main/data/org.gnome.settings-daemon.plugins.housekeeping.gschema.xml.in
	gsettings set org.gnome.settings-daemon.plugins.housekeeping donation-reminder-enabled false
	gsettings set org.gnome.settings-daemon.plugins.housekeeping donation-reminder-last-shown 0

	# See https://gitlab.gnome.org/GNOME/gnome-settings-daemon/-/blob/main/data/org.gnome.settings-daemon.plugins.color.gschema.xml.in
	gsettings set org.gnome.settings-daemon.plugins.color night-light-enabled false

	gnome-extensions info -q background-logo@fedorahosted.org > /dev/null
	if [[ $? -eq 0 ]]; then
		# See https://pagure.io/background-logo-extension/blob/master/f/schemas/org.fedorahosted.background-logo-extension.gschema.xml
		gsettings set org.fedorahosted.background-logo-extension logo-always-visible true
		gsettings set org.fedorahosted.background-logo-extension logo-border 20

		gnome-extensions enable background-logo@fedorahosted.org
	fi

	gnome-extensions info -q dash-to-dock@micxgx.gmail.com > /dev/null
	if [[ $? -eq 0 ]]; then
		# See https://github.com/micheleg/dash-to-dock/blob/master/schemas/org.gnome.shell.extensions.dash-to-dock.gschema.xml
		gsettings set org.gnome.shell.extensions.dash-to-dock application-counter-overrides-notifications true
		gsettings set org.gnome.shell.extensions.dash-to-dock autohide true
		gsettings set org.gnome.shell.extensions.dash-to-dock autohide-in-fullscreen false
		gsettings set org.gnome.shell.extensions.dash-to-dock dash-max-icon-size 48
		gsettings set org.gnome.shell.extensions.dash-to-dock default-windows-preview-to-open false
		gsettings set org.gnome.shell.extensions.dash-to-dock disable-overview-on-startup false
		gsettings set org.gnome.shell.extensions.dash-to-dock dock-position "BOTTOM"
		gsettings set org.gnome.shell.extensions.dash-to-dock intellihide true
		gsettings set org.gnome.shell.extensions.dash-to-dock intellihide-mode "FOCUS_APPLICATION_WINDOWS"
		gsettings set org.gnome.shell.extensions.dash-to-dock isolate-locations true
		gsettings set org.gnome.shell.extensions.dash-to-dock isolate-monitors false
		gsettings set org.gnome.shell.extensions.dash-to-dock isolate-workspaces false
		gsettings set org.gnome.shell.extensions.dash-to-dock manualhide false
		gsettings set org.gnome.shell.extensions.dash-to-dock require-pressure-to-show true
		gsettings set org.gnome.shell.extensions.dash-to-dock running-indicator-dominant-color false
		gsettings set org.gnome.shell.extensions.dash-to-dock running-indicator-style "DASHES"
		gsettings set org.gnome.shell.extensions.dash-to-dock show-dock-urgent-notify true
		gsettings set org.gnome.shell.extensions.dash-to-dock show-favorites true
		gsettings set org.gnome.shell.extensions.dash-to-dock show-icons-emblems true
		gsettings set org.gnome.shell.extensions.dash-to-dock show-icons-notifications-counter true
		gsettings set org.gnome.shell.extensions.dash-to-dock show-mounts false
		gsettings set org.gnome.shell.extensions.dash-to-dock show-mounts-network false
		gsettings set org.gnome.shell.extensions.dash-to-dock show-mounts-only-mounted false
		gsettings set org.gnome.shell.extensions.dash-to-dock show-running true
		gsettings set org.gnome.shell.extensions.dash-to-dock show-show-apps-button false
		gsettings set org.gnome.shell.extensions.dash-to-dock show-trash false
		gsettings set org.gnome.shell.extensions.dash-to-dock show-windows-preview true

		gnome-extensions enable dash-to-dock@micxgx.gmail.com
	fi
}

setup_usr__flatpak() {
	__run flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
	__run flatpak update -y
	__run flatpak install -y --or-update flathub com.usebottles.bottles
	__run flatpak install -y --or-update flathub io.gitlab.librewolf-community

	__run flatpak override -u com.usebottles.bottles --device dri --filesystem host
}

setup_usr__privacy() {
	# See https://gitlab.gnome.org/GNOME/localsearch/-/blob/main/data/org.freedesktop.Tracker.Miner.Files.gschema.xml
	gsettings set org.freedesktop.Tracker3.Miner.Files enable-monitors false
	gsettings set org.freedesktop.Tracker3.Miner.Files index-on-battery false
	gsettings set org.freedesktop.Tracker3.Miner.Files index-on-battery-first-time false
	gsettings set org.freedesktop.Tracker3.Miner.Files index-optical-discs false
	gsettings set org.freedesktop.Tracker3.Miner.Files index-recursive-directories "[]"
	gsettings set org.freedesktop.Tracker3.Miner.Files index-removable-devices false
	gsettings set org.freedesktop.Tracker3.Miner.Files index-single-directories "[]"

	# See https://gitlab.gnome.org/GNOME/localsearch/-/blob/main/docs/man1/localsearch.1.txt
	localsearch reset -s

	# See https://gitlab.gnome.org/GNOME/gsettings-desktop-schemas/blob/main/schemas/org.gnome.desktop.media-handling.gschema.xml.in
	gsettings set org.gnome.desktop.media-handling autorun-never true

	# See https://gitlab.gnome.org/GNOME/gsettings-desktop-schemas/blob/main/schemas/org.gnome.desktop.privacy.gschema.xml.in
	gsettings set org.gnome.desktop.privacy disable-camera true
	gsettings set org.gnome.desktop.privacy disable-microphone true
	gsettings set org.gnome.desktop.privacy remember-app-usage false
	gsettings set org.gnome.desktop.privacy remember-recent-files false
	gsettings set org.gnome.desktop.privacy remove-old-temp-files true
	gsettings set org.gnome.desktop.privacy remove-old-trash-files true
	gsettings set org.gnome.desktop.privacy report-technical-problems false
	gsettings set org.gnome.desktop.privacy send-software-usage-stats false
	gsettings set org.gnome.desktop.privacy usb-protection true

	# See https://gitlab.gnome.org/GNOME/gnome-remote-desktop/-/blob/master/src/org.gnome.desktop.remote-desktop.gschema.xml.in
	gsettings set org.gnome.desktop.remote-desktop.rdp enable false
	gsettings set org.gnome.desktop.remote-desktop.vnc enable false

	# See https://gitlab.gnome.org/GNOME/gsettings-desktop-schemas/-/blob/main/schemas/org.gnome.desktop.search-providers.gschema.xml.in
	gsettings set org.gnome.desktop.search-providers disable-external true

	# See https://gitlab.gnome.org/GNOME/gsettings-desktop-schemas/-/blob/main/schemas/org.gnome.desktop.thumbnailers.gschema.xml.in
	gsettings set org.gnome.desktop.thumbnailers disable-all true

	# See https://gitlab.gnome.org/GNOME/gsettings-desktop-schemas/-/blob/master/schemas/org.gnome.system.location.gschema.xml.in
	gsettings set org.gnome.system.location enabled false
}

setup_usr__privacy
setup_usr__desktop
setup_usr__flatpak
