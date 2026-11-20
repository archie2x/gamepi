# Gamepi kiosk package

This package integrates Debian greetd and Cage with the existing ES-DE AppImage.
It is built natively on macOS; no compilation or container is required.

```sh
python3 scripts/build-kiosk-package.py
```

Install with `sudo apt install ./gamepi-kiosk_0.1.0_all.deb` and reboot to activate.
The initial login user is configured in `/etc/greetd/gamepi.toml`; this local
appliance build selects roger. ES-DE itself must already exist at the path in
`/etc/gamepi/session.conf`.

`gamepi-kiosk.target` is enabled under multi-user.target. greetd creates a PAM
login session and starts `gamepi-kiosk-session`. That launcher runs one shared
Cage compositor with ES-DE, restarting it after exit with a two-second delay.
Set GAMEPI_RESTART=no to return to greetd's fallback text login on exit.
GUI login can later replace agreety in the default_session section.

`/etc/gamepi/es-de/settings/es_settings.xml` supplies initial ROM-root defaults
only for users lacking an ES-DE settings file. Existing preferences are not
rewritten. Personal favorites, saves and emulator configuration remain local.
The runtime directory is supplied by PAM, normally `/run/user/1000` for roger;
remote Wayland clients must connect there, not to a directory in ~/.cache.

The package declares group gamepi through sysusers.d and library directories
through tmpfiles.d. On first installation, existing library files become
group-writable, directories become setgid, and default ACLs grant inherited
group write access. `/etc/gamepi/library-editors` lists local group members.
The group has no dedicated user account. ROM and BIOS data remain outside the
package and are retained on package removal. No library locations are moved.

Package-owned files under /etc are conffiles. Dependencies use the distribution's
own PAM configuration. The configuration enables automatic local login; no
password or new login account is created. The installed session entry allows
future graphical greeters to select the same Gamepi session.
