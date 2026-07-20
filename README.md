# fedora-setup

A curses text UI for selectively applying post-install tweaks to a fresh
Fedora GNOME Workstation. Uses only the Python 3 standard library, so it
runs out of the box with no extra packages.

## Run

```
curl -sSL https://raw.githubusercontent.com/sandip4n/fedora-setup/refs/heads/master/setup.py | python3 -
```

Run it in a terminal inside your GNOME session. Tweaks are shown as a
fully expanded, scrollable tree (System / User -> theme -> dconf schema
-> individual key). Navigate with the keyboard:

- up / down      move
- pgup / pgdn    scroll a page
- space, enter   select or deselect the current item (a whole group or a
                 single tweak)
- a              apply the current selection
- q, esc         quit

System tweaks are applied with `sudo` (you are prompted once); user
tweaks run in your session.

Tweaks are grouped into two phases. After the system phase you are asked
to reboot before the user phase, because enabling GNOME extensions and
the GDM greeter changes need a restarted session. The clean flow is:

1. Run and select the system tweaks, then reboot when prompted.
2. Run again and select the user tweaks.

Selecting a tweak automatically selects the tweaks it depends on and
tells you which were added.

## Non-interactive

```
setup.py --list             # show all tweaks
setup.py --system           # apply all system tweaks
setup.py --user             # apply all user tweaks
setup.py --all              # apply everything
```
