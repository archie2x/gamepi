# gamepi-controllers

Bluetooth controller pairing for the appliance, with the Pi's own power
button as the only control.

- `/usr/bin/gamepi-controller-pair` reconnects known pads and pairs any 8BitDo
  pad that is in Switch pairing mode. It prefers the USB adapter and removes
  a pad's bond from any other adapter. `--status` lists adapters and pads.
- `gamepi-power-button.service` grabs the `pwr_button` input device. A short
  press opens a 30 second pairing window; holding for two seconds runs
  `systemctl poweroff`. Tones are played through the session's PipeWire.
  Set `GAMEPI_BUTTON_SOUND=0` in a drop-in to silence them.

The scripts live in `runtime/controllers/`; `scripts/build-controllers-package.py`
stages them. Pairing state in `/var/lib/bluetooth` is not packaged.

Replacing a hand install: remove `/usr/local/bin/gamepi-controller-pair`,
`/usr/local/bin/gamepi-power-button` and
`/etc/systemd/system/gamepi-power-button.service` so the packaged unit is
the one systemd uses.

## Onboard Bluetooth (manual)

The package does not touch the onboard radio. On a Pi whose internal antenna
suffers interference, turn it off by hand so every pad uses the USB adapter:

    echo 'blacklist hci_uart' | sudo tee /etc/modprobe.d/gamepi-no-onboard-bt.conf

It takes effect at the next boot; delete the file to undo it.
