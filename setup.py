#!/usr/bin/env python3

import argparse
import curses
import os
import re
import select
import shlex
import subprocess
import sys


def gset(schema, key, value):
    return "gsettings set %s %s %s" % (schema, key, shlex.quote(value))


def leaf(lid, label, desc, cmd, strict=False, deps=()):
    return {
        "kind": "leaf",
        "id": lid,
        "label": label,
        "desc": desc,
        "cmd": cmd,
        "strict": strict,
        "deps": list(deps),
    }


def group(label, children):
    return {"kind": "group", "label": label, "children": children}


def gs_group(prefix, label, schema, pairs):
    children = []
    for entry in pairs:
        key, value = entry[0], entry[1]
        deps = entry[2] if len(entry) > 2 else ()
        children.append(
            leaf(
                "%s.%s" % (prefix, key),
                key,
                value,
                gset(schema, key, value),
                False,
                deps,
            )
        )
    return group(label, children)


def dnf_leaf(lid, pkg, deps=()):
    return leaf(lid, pkg, pkg, "dnf -y install %s" % pkg, True, deps)


FONTS = ["fonts.cascadia"]
ICONS = ["icons.papirus"]
D2D = ["ext.dashtodock"]

FAVORITES = [
    ("org.mozilla.firefox.desktop", ("!fp.librewolf",)),
    ("io.gitlab.librewolf-community.desktop", ("fp.librewolf",)),
    ("net.thunderbird.Thunderbird.desktop", ()),
    ("org.gnome.Nautilus.desktop", ()),
    ("libreoffice-writer.desktop", ()),
    ("libreoffice-impress.desktop", ()),
    ("libreoffice-calc.desktop", ()),
    ("com.usebottles.bottles.desktop", ("fp.bottles",)),
    ("com.heroicgameslauncher.hgl.desktop", ("fp.heroic",)),
    ("gimp.desktop", ("tools.gimp",)),
    ("org.gnome.Ptyxis.desktop", ()),
    ("org.gnome.Software.desktop", ()),
    ("org.gnome.Settings.desktop", ()),
]


def favorites_value(selected):
    apps = []
    for app, deps in FAVORITES:
        need = {d for d in deps if not d.startswith("!")}
        block = {d[1:] for d in deps if d.startswith("!")}
        if need <= selected and not block & selected:
            apps.append(app)
    return "[%s]" % ", ".join("'%s'" % app for app in apps)


def favorites_cmd(selected):
    return gset("org.gnome.shell", "favorite-apps", favorites_value(selected))


DASH_TO_DOCK = [
    ("application-counter-overrides-notifications", "true"),
    ("autohide", "true"),
    ("autohide-in-fullscreen", "false"),
    ("dash-max-icon-size", "48"),
    ("default-windows-preview-to-open", "false"),
    ("disable-overview-on-startup", "false"),
    ("dock-position", "BOTTOM"),
    ("intellihide", "true"),
    ("intellihide-mode", "FOCUS_APPLICATION_WINDOWS"),
    ("isolate-locations", "true"),
    ("isolate-monitors", "false"),
    ("isolate-workspaces", "false"),
    ("manualhide", "false"),
    ("require-pressure-to-show", "true"),
    ("running-indicator-dominant-color", "false"),
    ("running-indicator-style", "DASHES"),
    ("show-dock-urgent-notify", "true"),
    ("show-favorites", "true"),
    ("show-icons-emblems", "true"),
    ("show-icons-notifications-counter", "true"),
    ("show-mounts", "false"),
    ("show-mounts-network", "false"),
    ("show-mounts-only-mounted", "false"),
    ("show-running", "true"),
    ("show-show-apps-button", "false"),
    ("show-trash", "false"),
    ("show-windows-preview", "true"),
]


def dash_to_dock_group():
    schema = "org.gnome.shell.extensions.dash-to-dock"
    children = [
        leaf("d2d.%s" % k, k, v, gset(schema, k, v), False, D2D)
        for k, v in DASH_TO_DOCK
    ]
    children.append(
        leaf(
            "d2d.enable",
            "enable",
            "dash-to-dock@micxgx.gmail.com",
            "gnome-extensions enable dash-to-dock@micxgx.gmail.com",
            False,
            D2D,
        )
    )
    return group("dash to dock", children)


def flatpak__user_install(app, overrides=None):
    cmd = "flatpak install --user --assumeyes --or-update flathub %s" % app
    if overrides:
        opts = " ".join(
            "--%s %s" % (key, value) for key, value in overrides.items()
        )
        cmd += " && flatpak override --user %s %s" % (app, opts)
    return cmd


def sysctl_cmd(key, value):
    return (
        "[ -f /etc/sysctl.d/99-sysctl.conf ] || "
        "install -m 0644 /dev/null /etc/sysctl.d/99-sysctl.conf\n"
        "grep -q '^%s' /etc/sysctl.d/99-sysctl.conf || "
        "echo '%s = %s' >> /etc/sysctl.d/99-sysctl.conf\n"
        "sysctl --system" % (key, key, value)
    )


USER = group(
    "User",
    [
        group(
            "Interface",
            [
                gs_group(
                    "bg",
                    "background",
                    "org.gnome.desktop.background",
                    [
                        ("picture-opacity", "100"),
                        (
                            "picture-uri",
                            "file:///usr/share/backgrounds/gnome/blobs-l.svg",
                        ),
                        (
                            "picture-uri-dark",
                            "file:///usr/share/backgrounds/gnome/blobs-d.svg",
                        ),
                        ("show-desktop-icons", "false"),
                    ],
                ),
                gs_group(
                    "if",
                    "interface",
                    "org.gnome.desktop.interface",
                    [
                        ("clock-format", "24h"),
                        ("clock-show-weekday", "true"),
                        ("color-scheme", "prefer-dark"),
                        (
                            "document-font-name",
                            "Cascadia Code Regular 11",
                            FONTS,
                        ),
                        ("font-name", "Cascadia Code Regular 11", FONTS),
                        ("icon-theme", "Papirus", ICONS),
                        (
                            "monospace-font-name",
                            "Cascadia Code Regular 11",
                            FONTS,
                        ),
                    ],
                ),
                gs_group(
                    "wm",
                    "window buttons",
                    "org.gnome.desktop.wm.preferences",
                    [
                        ("button-layout", "appmenu:minimize,maximize,close"),
                    ],
                ),
                gs_group(
                    "mutter",
                    "mutter",
                    "org.gnome.mutter",
                    [
                        ("dynamic-workspaces", "true"),
                        (
                            "experimental-features",
                            "['scale-monitor-framebuffer', 'xwayland-native-scaling']",
                        ),
                    ],
                ),
                gs_group(
                    "color",
                    "color",
                    "org.gnome.settings-daemon.plugins.color",
                    [
                        ("night-light-enabled", "false"),
                    ],
                ),
                gs_group(
                    "hk",
                    "housekeeping",
                    "org.gnome.settings-daemon.plugins.housekeeping",
                    [
                        ("donation-reminder-enabled", "false"),
                        ("donation-reminder-last-shown", "0"),
                    ],
                ),
                group(
                    "terminal",
                    [
                        leaf(
                            "term.palette",
                            "palette",
                            "Catppuccin Mocha",
                            (
                                "rpm -q --quiet ptyxis && gsettings set "
                                "org.gnome.Ptyxis.Profile:/org/gnome/Ptyxis/Profiles/"
                                '$(gsettings get org.gnome.Ptyxis default-profile-uuid | tr -d "\'")/ '
                                "palette 'Catppuccin Mocha'"
                            ),
                        ),
                    ],
                ),
                group(
                    "shell extensions",
                    [
                        group(
                            "background logo",
                            [
                                leaf(
                                    "bglogo.logo-always-visible",
                                    "logo-always-visible",
                                    "true",
                                    gset(
                                        "org.fedorahosted.background-logo-extension",
                                        "logo-always-visible",
                                        "true",
                                    ),
                                ),
                                leaf(
                                    "bglogo.logo-border",
                                    "logo-border",
                                    "20",
                                    gset(
                                        "org.fedorahosted.background-logo-extension",
                                        "logo-border",
                                        "20",
                                    ),
                                ),
                                leaf(
                                    "bglogo.enable",
                                    "enable",
                                    "background-logo@fedorahosted.org",
                                    "gnome-extensions enable background-logo@fedorahosted.org",
                                ),
                            ],
                        ),
                        dash_to_dock_group(),
                    ],
                ),
            ],
        ),
        group(
            "Devices",
            [
                gs_group(
                    "tp",
                    "touchpad",
                    "org.gnome.desktop.peripherals.touchpad",
                    [
                        ("click-method", "areas"),
                        ("tap-to-click", "true"),
                        ("two-finger-scrolling-enabled", "true"),
                    ],
                ),
                gs_group(
                    "snd",
                    "sound",
                    "org.gnome.desktop.sound",
                    [
                        ("allow-volume-above-100-percent", "false"),
                        ("event-sounds", "false"),
                        ("input-feedback-sounds", "false"),
                    ],
                ),
                group(
                    "bluetooth",
                    [
                        leaf(
                            "bt.off",
                            "power off",
                            "org.bluez adapter",
                            (
                                "if busctl --system introspect org.bluez /org/bluez/hci0 >/dev/null 2>&1; then "
                                "busctl --system set-property org.bluez /org/bluez/hci0 "
                                "org.bluez.Adapter1 Powered b false; fi"
                            ),
                        ),
                    ],
                ),
            ],
        ),
        group(
            "Power",
            [
                gs_group(
                    "session",
                    "blank screen",
                    "org.gnome.desktop.session",
                    [
                        ("idle-delay", "0"),
                    ],
                ),
                gs_group(
                    "power",
                    "suspend",
                    "org.gnome.settings-daemon.plugins.power",
                    [
                        ("sleep-inactive-ac-type", "nothing"),
                        ("sleep-inactive-battery-type", "nothing"),
                    ],
                ),
            ],
        ),
        group(
            "Files",
            [
                gs_group(
                    "nau",
                    "nautilus",
                    "org.gnome.nautilus.preferences",
                    [
                        ("default-sort-order", "name"),
                        ("fts-enabled", "false"),
                        ("show-image-thumbnails", "never"),
                    ],
                ),
            ],
        ),
        group(
            "Software",
            [
                group(
                    "flatpak",
                    [
                        leaf(
                            "fp.flathub",
                            "flathub",
                            "enable flathub repository for user flatpaks",
                            (
                                "flatpak remote-add --user --if-not-exists flathub "
                                "https://dl.flathub.org/repo/flathub.flatpakrepo && "
                                "flatpak remote-modify --user --enable flathub && "
                                "flatpak update --user --assumeyes"
                            ),
                            True,
                        ),
                        leaf(
                            "fp.librewolf",
                            "librewolf",
                            "install librewolf web browser",
                            flatpak__user_install(
                                "io.gitlab.librewolf-community"
                            ),
                            True,
                            ["fp.flathub"],
                        ),
                        leaf(
                            "fp.protonplus",
                            "protonplus",
                            "install protonplus to manage proton releases",
                            flatpak__user_install("com.vysp3r.ProtonPlus"),
                            True,
                            ["fp.flathub"],
                        ),
                        leaf(
                            "fp.bottles",
                            "bottles",
                            "install bottles",
                            flatpak__user_install(
                                "com.usebottles.bottles",
                                {"device": "dri", "filesystem": "host"},
                            ),
                            True,
                            ["fp.flathub"],
                        ),
                        leaf(
                            "fp.heroic",
                            "heroic",
                            "install heroic games launcher",
                            flatpak__user_install(
                                "com.heroicgameslauncher.hgl",
                                {"device": "dri", "filesystem": "host"},
                            ),
                            True,
                            ["fp.flathub"],
                        ),
                    ],
                ),
                group(
                    "favorites",
                    [
                        leaf(
                            "fav.favorite-apps",
                            "favorite-apps",
                            favorites_value,
                            favorites_cmd,
                        ),
                    ],
                ),
            ],
        ),
        group(
            "Privacy",
            [
                gs_group(
                    "trk",
                    "file indexing",
                    "org.freedesktop.Tracker3.Miner.Files",
                    [
                        ("enable-monitors", "false"),
                        ("index-on-battery", "false"),
                        ("index-on-battery-first-time", "false"),
                        ("index-optical-discs", "false"),
                        ("index-recursive-directories", "[]"),
                        ("index-removable-devices", "false"),
                        ("index-single-directories", "[]"),
                    ],
                ),
                group(
                    "localsearch",
                    [
                        leaf(
                            "trk.reset",
                            "reset",
                            "localsearch reset -s",
                            "localsearch reset -s",
                        ),
                    ],
                ),
                gs_group(
                    "media",
                    "removable media",
                    "org.gnome.desktop.media-handling",
                    [
                        ("autorun-never", "true"),
                    ],
                ),
                gs_group(
                    "prv",
                    "privacy",
                    "org.gnome.desktop.privacy",
                    [
                        ("disable-camera", "true"),
                        ("disable-microphone", "true"),
                        ("remember-app-usage", "false"),
                        ("remember-recent-files", "false"),
                        ("remove-old-temp-files", "true"),
                        ("remove-old-trash-files", "true"),
                        ("report-technical-problems", "false"),
                        ("send-software-usage-stats", "false"),
                        ("usb-protection", "true"),
                    ],
                ),
                group(
                    "remote desktop",
                    [
                        leaf(
                            "rd.rdp",
                            "rdp",
                            "false",
                            gset(
                                "org.gnome.desktop.remote-desktop.rdp",
                                "enable",
                                "false",
                            ),
                        ),
                        leaf(
                            "rd.vnc",
                            "vnc",
                            "false",
                            gset(
                                "org.gnome.desktop.remote-desktop.vnc",
                                "enable",
                                "false",
                            ),
                        ),
                    ],
                ),
                gs_group(
                    "sp",
                    "search providers",
                    "org.gnome.desktop.search-providers",
                    [
                        ("disable-external", "true"),
                    ],
                ),
                gs_group(
                    "thumb",
                    "thumbnails",
                    "org.gnome.desktop.thumbnailers",
                    [
                        ("disable-all", "true"),
                    ],
                ),
                gs_group(
                    "loc",
                    "location",
                    "org.gnome.system.location",
                    [
                        ("enabled", "false"),
                    ],
                ),
            ],
        ),
        group(
            "Date & Time",
            [
                gs_group(
                    "dt",
                    "auto timezone",
                    "org.gnome.desktop.datetime",
                    [
                        ("automatic-timezone", "false"),
                    ],
                ),
            ],
        ),
    ],
)


SYSTEM = group(
    "System",
    [
        group(
            "Software",
            [
                leaf(
                    "sw.upgrade",
                    "upgrade",
                    "refresh and upgrade all packages",
                    (
                        "pkcon -y refresh force || [ $? -eq 5 ]\n"
                        "pkcon -y update || [ $? -eq 5 ]"
                    ),
                    True,
                ),
                group(
                    "codecs",
                    [
                        leaf(
                            "cod.rpmfusion",
                            "rpm-fusion",
                            "codec repositories",
                            (
                                "dnf -y install "
                                "https://mirrors.rpmfusion.org/free/fedora/"
                                "rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm "
                                "https://mirrors.rpmfusion.org/nonfree/fedora/"
                                "rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm && "
                                "dnf -y install 'rpmfusion-*-appstream-data'"
                            ),
                            True,
                        ),
                        leaf(
                            "cod.openh264",
                            "open-h264",
                            "cisco open-h264 codec",
                            "dnf -y config-manager setopt fedora-cisco-openh264.enabled=1",
                            True,
                        ),
                        leaf(
                            "cod.multimedia",
                            "multimedia",
                            "gstreamer and ffmpeg add-ons",
                            "dnf -y swap ffmpeg-free ffmpeg --allowerasing && "
                            "dnf -y update @multimedia "
                            "--setopt=install_weak_deps=False "
                            "--exclude=PackageKit-gstreamer-plugin",
                            True,
                            ["cod.rpmfusion"],
                        ),
                    ],
                ),
                group(
                    "fonts",
                    [
                        dnf_leaf("fonts.cascadia", "cascadia-code-fonts"),
                    ],
                ),
                group(
                    "extensions",
                    [
                        dnf_leaf(
                            "ext.dashtodock",
                            "gnome-shell-extension-dash-to-dock",
                        ),
                    ],
                ),
                group(
                    "icons",
                    [
                        dnf_leaf("icons.papirus", "papirus-icon-theme"),
                    ],
                ),
                group(
                    "tools",
                    [
                        dnf_leaf(
                            "tools.gnome-extensions-app", "gnome-extensions-app"
                        ),
                        dnf_leaf("tools.gnome-tweaks", "gnome-tweak-tool"),
                        dnf_leaf("tools.p7zip", "p7zip"),
                        dnf_leaf("tools.p7zip-plugins", "p7zip-plugins"),
                        dnf_leaf(
                            "tools.systemd-container", "systemd-container"
                        ),
                        dnf_leaf("tools.dbus-x11", "dbus-x11"),
                        dnf_leaf("tools.gimp", "gimp"),
                    ],
                ),
            ],
        ),
        group(
            "Performance",
            [
                group(
                    "memory",
                    [
                        leaf(
                            "mem.zram",
                            "zram",
                            "size=ram, zstd",
                            (
                                "install -m 0644 /dev/null /etc/systemd/zram-generator.conf\n"
                                "cat > /etc/systemd/zram-generator.conf <<'EOF'\n"
                                "[zram0]\n"
                                "zram-size = ram\n"
                                "compression-algorithm = zstd\n"
                                "EOF\n"
                                "systemctl daemon-reload\n"
                                "systemctl restart systemd-zram-setup@zram0.service"
                            ),
                            True,
                        ),
                        leaf(
                            "mem.swappiness",
                            "vm.swappiness",
                            "150",
                            sysctl_cmd("vm.swappiness", "150"),
                            True,
                        ),
                        leaf(
                            "mem.page-cluster",
                            "vm.page-cluster",
                            "0",
                            sysctl_cmd("vm.page-cluster", "0"),
                            True,
                        ),
                    ],
                ),
            ],
        ),
        group(
            "Login",
            [
                leaf(
                    "login.greeter",
                    "greeter settings",
                    "gdm dconf db",
                    (
                        "install -d -m 0755 /etc/dconf/db/gdm.d\n"
                        "cat > /etc/dconf/db/gdm.d/95-settings <<'EOF'\n"
                        "[org/gnome/desktop/interface]\n"
                        "clock-format='24h'\n"
                        "clock-show-weekday=true\n"
                        "color-scheme='prefer-dark'\n"
                        "font-name='Cascadia Code Regular 11'\n"
                        "gtk-theme='Adwaita-dark'\n"
                        "icon-theme='Papirus'\n"
                        "\n"
                        "[org/gnome/desktop/peripherals/touchpad]\n"
                        "tap-to-click=true\n"
                        "\n"
                        "[org/gnome/settings-daemon/plugins/color]\n"
                        "night-light-enabled=false\n"
                        "EOF\n"
                        "dconf update"
                    ),
                    True,
                    ["fonts.cascadia", "icons.papirus"],
                ),
                leaf(
                    "login.profile",
                    "profile",
                    "gdm dconf profile",
                    (
                        "install -d -m 0755 /etc/dconf/profile\n"
                        "cat > /etc/dconf/profile/gdm <<'EOF'\n"
                        "user-db:user\n"
                        "system-db:gdm\n"
                        "file-db:/usr/share/gdm/greeter-dconf-defaults\n"
                        "EOF"
                    ),
                    True,
                ),
            ],
        ),
        group(
            "Date & Time",
            [
                leaf(
                    "td.rtc",
                    "rtc",
                    "utc",
                    "timedatectl set-local-rtc false",
                    True,
                ),
                leaf(
                    "td.ntp", "ntp", "enable", "timedatectl set-ntp true", True
                ),
            ],
        ),
        group(
            "Maintenance",
            [
                leaf(
                    "maint.journal",
                    "journal",
                    "vacuum",
                    "journalctl --vacuum-time 0",
                    True,
                ),
            ],
        ),
    ],
)


ROOT = group("", [SYSTEM, USER])


def walk_leaves(node):
    if node["kind"] == "leaf":
        yield node
    else:
        for child in node["children"]:
            yield from walk_leaves(child)


_software = next(g for g in SYSTEM["children"] if g["label"] == "Software")
for _sw in walk_leaves(_software):
    if _sw["id"] != "sw.upgrade":
        _sw["deps"].append("sw.upgrade")

BY_ID = {lf["id"]: lf for lf in walk_leaves(ROOT)}

LABEL_WIDTH = {}


def compute_label_widths(node):
    leaves = [c for c in node["children"] if c["kind"] == "leaf"]
    width = max((len(c["label"]) for c in leaves), default=0)
    for c in leaves:
        LABEL_WIDTH[c["id"]] = width
    for c in node["children"]:
        if c["kind"] == "group":
            compute_label_widths(c)


compute_label_widths(ROOT)
PHASE_OF = {}
for _lf in walk_leaves(SYSTEM):
    PHASE_OF[_lf["id"]] = "system"
for _lf in walk_leaves(USER):
    PHASE_OF[_lf["id"]] = "user"


def resolve(selected):
    out = set(selected)
    changed = True
    while changed:
        changed = False
        for lid in list(out):
            for dep in BY_ID[lid]["deps"]:
                if dep not in out:
                    out.add(dep)
                    changed = True
    return out, out - set(selected)


def prune(selected):
    out = set(selected)
    changed = True
    while changed:
        changed = False
        for lid in list(out):
            if not set(BY_ID[lid]["deps"]) <= out:
                out.discard(lid)
                changed = True
    return out, set(selected) - out


def subtree_ids(node):
    return {lf["id"] for lf in walk_leaves(node)}


def selected_leaves(node, selected):
    return [lf for lf in walk_leaves(node) if lf["id"] in selected]


def leaf_value(value, selected):
    return value(selected) if callable(value) else value


ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def clean(text):
    text = ANSI_RE.sub("", text)
    return "".join(c for c in text if c == "\t" or c >= " ")


def interesting(cmd):
    if not cmd:
        return False
    skip = (
        "[[",
        "[ ",
        "set ",
        "cat ",
        "install ",
        "grep ",
        "if ",
        "fi",
        "then",
    )
    return not cmd.startswith(skip)


def run_tweak(cmd, phase, on_cmd, on_out, pump=None):
    r_out, w_out = os.pipe()
    r_err, w_err = os.pipe()
    script = "set -x\n" + cmd + "\n"
    argv = ["bash", "-c", script]
    if phase == "system":
        argv = ["sudo", "-n"] + argv
    env = dict(os.environ)
    env["PS4"] = "+\x1f"
    proc = subprocess.Popen(
        argv, stdin=subprocess.DEVNULL, stdout=w_out, stderr=w_err, env=env
    )
    os.close(w_out)
    os.close(w_err)
    bufs = {r_out: b"", r_err: b""}
    open_fds = {r_out, r_err}

    def drain(fd):
        data = os.read(fd, 65536)
        if not data:
            return False
        bufs[fd] += data
        while b"\n" in bufs[fd]:
            raw, bufs[fd] = bufs[fd].split(b"\n", 1)
            text = raw.decode("utf-8", "replace")
            if fd == r_err and "\x1f" in text:
                traced = clean(text.split("\x1f", 1)[1]).strip()
                if interesting(traced):
                    on_cmd(traced)
            else:
                on_out(clean(text))
        return True

    while open_fds:
        rlist, _, _ = select.select(list(open_fds), [], [], 0.05)
        for fd in rlist:
            if not drain(fd):
                open_fds.discard(fd)
                os.close(fd)
        if pump:
            pump()
    proc.wait()
    return proc.returncode


def put(win, y, x, text, width, attr=0):
    height, real_width = win.getmaxyx()
    width = min(width, real_width)
    if y < 0 or y >= height or x >= width:
        return
    try:
        win.addnstr(y, x, text, max(0, width - 1 - x), attr)
    except curses.error:
        pass


def box_state(node, selected):
    ids = subtree_ids(node)
    hit = len(ids & selected)
    if hit == 0:
        return "[ ]"
    if hit == len(ids):
        return "[x]"
    return "[~]"


def confirm(stdscr, selected):
    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        put(stdscr, 0, 0, "About to apply:", width, curses.A_BOLD)
        row = 2
        for node, phase in ((SYSTEM, "system"), (USER, "user")):
            leaves = selected_leaves(node, selected)
            if not leaves:
                continue
            put(
                stdscr,
                row,
                0,
                "%s  (%d tweaks)" % (node["label"], len(leaves)),
                width,
                curses.A_BOLD,
            )
            row += 1
        put(
            stdscr,
            height - 1,
            0,
            "enter confirm   esc back",
            width,
            curses.A_REVERSE,
        )
        stdscr.refresh()
        ch = stdscr.getch()
        if ch in (curses.KEY_ENTER, 10, 13):
            return True
        if ch in (27, ord("q")):
            return False


def checklist(stdscr):
    curses.curs_set(0)
    selected = set(BY_ID)
    cursor = 0
    top_row = 0
    msg = ""

    rows = []

    def build(node, depth):
        for child in node["children"]:
            rows.append((child, depth))
            if child["kind"] == "group":
                build(child, depth + 1)

    build(ROOT, 0)

    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        area_h = max(1, height - 4)
        if cursor < top_row:
            top_row = cursor
        elif cursor >= top_row + area_h:
            top_row = cursor - area_h + 1
        top_row = max(0, min(top_row, max(0, len(rows) - area_h)))
        put(stdscr, 0, 0, "Select tweaks", width, curses.A_BOLD)
        for vi in range(area_h):
            i = top_row + vi
            if i >= len(rows):
                break
            node, depth = rows[i]
            y = 2 + vi
            indent = "  " * depth
            if node["kind"] == "leaf":
                box = "[x]" if node["id"] in selected else "[ ]"
                text = "%s%s %-*s  %s" % (
                    indent,
                    box,
                    LABEL_WIDTH.get(node["id"], 0),
                    node["label"],
                    leaf_value(node["desc"], selected),
                )
                attr = curses.A_NORMAL
            else:
                text = "%s%s %s" % (
                    indent,
                    box_state(node, selected),
                    node["label"],
                )
                attr = curses.A_BOLD if depth == 0 else curses.A_NORMAL
            put(
                stdscr,
                y,
                0,
                text,
                width,
                curses.A_REVERSE if i == cursor else attr,
            )
        put(stdscr, height - 2, 0, msg, width)
        put(
            stdscr,
            height - 1,
            0,
            "up/down move  pgup/pgdn page  space/enter select  a apply  q quit",
            width,
            curses.A_REVERSE,
        )
        stdscr.refresh()

        ch = stdscr.getch()
        node = rows[cursor][0]
        if ch in (ord("q"), 27):
            return None
        elif ch == curses.KEY_UP:
            cursor = max(0, cursor - 1)
        elif ch == curses.KEY_DOWN:
            cursor = min(len(rows) - 1, cursor + 1)
        elif ch == curses.KEY_PPAGE:
            cursor = max(0, cursor - area_h)
        elif ch == curses.KEY_NPAGE:
            cursor = min(len(rows) - 1, cursor + area_h)
        elif ch in (curses.KEY_ENTER, 10, 13, ord(" ")):
            ids = {node["id"]} if node["kind"] == "leaf" else subtree_ids(node)
            if ids <= selected:
                selected -= ids
                selected, changed = prune(selected)
                verb = "deselected"
            else:
                selected |= ids
                selected, changed = resolve(selected)
                verb = "selected"
            msg = ""
            if changed:
                msg = "-> also %s: %s" % (
                    verb,
                    ", ".join(sorted(BY_ID[i]["label"] for i in changed)),
                )
        elif ch == ord("a"):
            if not selected:
                msg = "nothing selected"
                continue
            selected, _ = resolve(selected)
            if confirm(stdscr, selected):
                return selected


def apply_screen(stdscr, order, selected):
    curses.curs_set(0)
    stdscr.nodelay(True)
    buf = []
    state = {"label": "", "cmd": "", "n": 0, "total": len(order), "off": 0}

    def geometry():
        height, width = stdscr.getmaxyx()
        top = 3
        body = max(1, height - top - 1)
        return height, width, top, body

    def redraw():
        height, width, top, body = geometry()
        stdscr.erase()
        put(
            stdscr,
            0,
            0,
            "Applying: %s  (%d/%d)"
            % (state["label"], state["n"], state["total"]),
            width,
            curses.A_BOLD,
        )
        put(stdscr, 1, 0, "$ " + state["cmd"], width)
        put(stdscr, 2, 0, "-" * width, width)
        end = len(buf) - state["off"]
        start = max(0, end - body)
        for i, line in enumerate(buf[start:end]):
            put(stdscr, top + i, 0, line, width)
        put(stdscr, height - 1, 0, "PgUp/PgDn scroll", width, curses.A_REVERSE)
        stdscr.refresh()

    def on_out(line):
        buf.append(line)
        if len(buf) > 5000:
            del buf[:1000]

    def on_cmd(cmd):
        state["cmd"] = cmd

    def pump():
        ch = stdscr.getch()
        if ch != -1:
            _, _, _, body = geometry()
            if ch == curses.KEY_PPAGE:
                state["off"] = min(state["off"] + body, max(0, len(buf) - body))
            elif ch == curses.KEY_NPAGE:
                state["off"] = max(0, state["off"] - body)
        redraw()

    for lf in order:
        state["label"] = lf["label"]
        state["n"] += 1
        state["cmd"] = ""
        state["off"] = 0
        redraw()
        rc = run_tweak(
            leaf_value(lf["cmd"], selected),
            PHASE_OF[lf["id"]],
            on_cmd,
            on_out,
            pump,
        )
        if rc != 0:
            on_out("*** %s exited %d ***" % (lf["label"], rc))
            if lf["strict"]:
                stdscr.nodelay(False)
                height, width, _, _ = geometry()
                put(
                    stdscr,
                    height - 1,
                    0,
                    "failed; press any key",
                    width,
                    curses.A_REVERSE,
                )
                stdscr.getch()
                return rc
    stdscr.nodelay(False)
    height, width, _, _ = geometry()
    put(stdscr, height - 1, 0, "done; press any key", width, curses.A_REVERSE)
    stdscr.getch()
    return 0


def interactive_apply(selected):
    sys_order = selected_leaves(SYSTEM, selected)
    usr_order = selected_leaves(USER, selected)
    if sys_order:
        subprocess.run(["sudo", "-v"])
        rc = curses.wrapper(lambda s: apply_screen(s, sys_order, selected))
        if rc != 0:
            return
    if usr_order:
        if sys_order:
            ans = (
                input(
                    "System tweaks applied. A reboot is recommended before user "
                    "tweaks\n(needed for GNOME extensions and GDM).\n"
                    "[r]eboot now / [a]pply user tweaks now / [s]kip: "
                )
                .strip()
                .lower()
            )
            if ans == "r":
                subprocess.run(["sudo", "systemctl", "reboot"])
                return
            if ans not in ("a", ""):
                return
        curses.wrapper(lambda s: apply_screen(s, usr_order, selected))
    elif sys_order:
        print("system tweaks applied; reboot to finish.")


def apply_plain(selected):
    sys_order = selected_leaves(SYSTEM, selected)
    usr_order = selected_leaves(USER, selected)
    if sys_order:
        subprocess.run(["sudo", "-v"])
    for lf in sys_order + usr_order:
        print("== %s ==" % lf["label"])
        script = "set -x\n" + leaf_value(lf["cmd"], selected) + "\n"
        argv = ["bash", "-c", script]
        if PHASE_OF[lf["id"]] == "system":
            argv = ["sudo", "-n"] + argv
        rc = subprocess.run(argv).returncode
        if rc != 0 and lf["strict"]:
            print("%s failed (exit %d)" % (lf["label"], rc), file=sys.stderr)
            sys.exit(rc)
    if sys_order and usr_order:
        print(
            "note: reboot recommended before the user tweaks take full effect"
        )


def print_tree(node, depth=0):
    for child in node["children"]:
        if child["kind"] == "leaf":
            print("%s%s" % ("  " * depth, child["label"]))
        else:
            print("%s%s/" % ("  " * depth, child["label"]))
            print_tree(child, depth + 1)


def reopen_tty():
    fd = os.open("/dev/tty", os.O_RDWR)
    os.dup2(fd, 0)
    os.dup2(fd, 1)
    if fd > 2:
        os.close(fd)


def parse_args():
    parser = argparse.ArgumentParser(description="Apply Fedora setup tweaks.")
    parser.add_argument("--all", action="store_true", help="apply every tweak")
    parser.add_argument(
        "--system", action="store_true", help="apply system tweaks"
    )
    parser.add_argument("--user", action="store_true", help="apply user tweaks")
    parser.add_argument(
        "--list", action="store_true", help="list tweaks and exit"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.list:
        print_tree(ROOT)
        return
    if args.all or args.system or args.user:
        selected = set()
        if args.all:
            selected = set(BY_ID)
        if args.system:
            selected |= subtree_ids(SYSTEM)
        if args.user:
            selected |= subtree_ids(USER)
        selected, _ = resolve(selected)
        apply_plain(selected)
        return
    try:
        reopen_tty()
    except OSError:
        print(
            "setup.py needs a terminal; use --all, --system or --user for "
            "non-interactive runs.",
            file=sys.stderr,
        )
        sys.exit(1)
    selected = curses.wrapper(checklist)
    if not selected:
        return
    selected, _ = resolve(selected)
    interactive_apply(selected)


if __name__ == "__main__":
    main()
