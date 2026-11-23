# Remote keyboard and mouse

Deskflow on the Mac sends input to Waynergy in the Pi user's existing Cage
session. The SwiftBar Gamepi Input menu starts and stops an SSH reverse tunnel:
Pi localhost port 24805 forwards to the Mac's Deskflow server on localhost
port 24800. The input connection starts on demand.

## Pi provisioning

`gamepi-remote-input` installs:

- Waynergy v0.0.17 at `/usr/lib/gamepi-remote-input/waynergy`.
- `/usr/bin/gamepi-remote-input`, which supervises the receiver and stops it
  when the SSH connection closes. A per-user lock prevents duplicate receivers.
- `/etc/gamepi/remote-input/config.ini`, with the Mac raw-key mapping and
  display dimensions detected from Wayland.
- A modules-load entry for `uinput` and a udev rule giving group `input`
  read/write access to `/dev/uinput`.

Build on the Mac after extracting the project's Linux sysroot:

```sh
python3 scripts/build-remote-input-package.py
```

This uses native Homebrew tools and the pinned, checksummed Waynergy inputs.
The output is `build/packages/gamepi-remote-input_0.1.0_arm64.deb`. Copy it to
the Pi and install it there:

```sh
sudo apt install ./gamepi-remote-input_0.1.0_arm64.deb
```

The package works with `gamepi-kiosk` 0.1.0 and later. The receiver runs as the
same user as Cage and uses that user's `/run/user/UID/wayland-0` socket. That
user needs membership in `input`; the existing Raspberry Pi OS user already
had this access on both tested installations. If needed, add the gaming user
and start a new login session:

```sh
sudo usermod -aG input roger
```

Installation loads `uinput` and applies its device rule immediately. It does
not restart Cage or enable a receiver service at boot. The package installs
its runtime-library dependencies through APT.

## Mac setup

Install Deskflow and SwiftBar, grant Deskflow the required input permissions,
and configure its server on `127.0.0.1:24800`. Its client screen is named
`gamepi`; the existing layout places it to the left of the Mac. Configure
SwiftBar's plugin directory, then run:

```sh
python3 scripts/install-mac-remote-input.py
```

This installs the menu and an on-demand launchd job. The default connection
settings in `~/.config/gamepi/remote-input.json` are:

```json
{"host": "gamepi"}
```

The menu uses the normal `gamepi` SSH alias. The installer preserves existing
settings; remove an unwanted `hostname` override from this JSON file to return
to the alias. This setup does not edit `~/.ssh/config` or Deskflow's layout.

Choose Connect, then move off the Mac's left edge to send keyboard/mouse input
to the Pi. Move right to return. Disconnect closes the SSH connection and
stops the receiver. Sharing does not start automatically at login.

## Verification

```sh
PYTHONPYCACHEPREFIX=build/pycache python3 -m unittest discover -s tests -p test_remote_input.py
python3 scripts/remote-input.py status
```

The tests cover raw-key mapping and receiver cleanup on SSH input EOF.
On the NVMe prototype, the package installed alongside kiosk 0.1.0 and the
menu reached Connected with Waynergy using uinput. Physical input is checked
using the configured screen edge.
