# Working notes

## Current scope

Build a controller-operated Raspberry Pi 5 appliance by integrating existing
software. Use Raspberry Pi OS 64-bit, the AMD GPU on PCIe, one shared Cage
session, the ES-DE AppImage, Debian utilities, and suitable libretro cores or
standalone emulator AppImages. Keep source patches small and reproducible.

Priorities:

1. Flycast through RetroArch, including controller input and launch/return.
2. Controllers for Dolphin and ARMSX2: evaluate their current libretro cores;
   translate shared layouts into standalone configs where needed.
3. Menu/exit hotkeys and persistent player assignments.
4. Shared audio, autostart/recovery, library storage, and save backups.

N64 is deferred. A separate USB library drive and a clean OS installation are
being considered; no disk wipe or repartition is planned in the current work.

## Runtime facts

- Pi kernel: `6.18.48-v8-16k+`, page size 16384, AMD support from PR 7113.
- Stock ES-DE, Dolphin, ARMSX2 and Flycast AppImages are in `~/Applications`.
- ROMs are in `~/ROMs`; use case-sensitive directory names documented in runtime.md.
- Standalone ARMSX2, Dolphin and Flycast have run games.
- Blueman launches through ES-DE's Desktop Applications menu.
- ALSA defaults to the `gamepi_hdmi_mix` dmix device on AMD HDMI, with a plug
  conversion layer and stereo S32_LE/48 kHz hardware output. Simultaneous
  44.1 kHz and 48 kHz clients pass, including playback alongside ES-DE.
- Debian RetroArch: `1.20.0+dfsg-2+b1`, verified against its package checksums.
  Its ARM64 OpenGL backend is GLES; Vulkan works on the RX 460.
- The launcher now uses upstream ARM64 RetroArch `1.22.2`, Git `62eeee40e`,
  downloaded from the 2026-11-18 buildbot archive. Its udev driver exposes the
  Pro Controller's accelerometer and gyro; Debian 1.20's driver has no sensor
  callbacks. Debian remains installed. Download details are in runtime.md.
- RetroArch's menu works with keyboard, mouse and Pro Controller. Its explicit
  config is `~/.config/gamepi/retroarch/retroarch.cfg`.
- The standard RetroArch config path remains a symlink into `/opt/retropie` and
  is not used by the Gamepi launcher. Preserve its data and saves.

## Flycast

Source: flyinghead/flycast `3a5267a5e32438026e1c5b97d5de6cd77236f72c`.
Patch branch: `archie2x-upstream/flycast:fix/linux-runtime-page-size`, commit
`d97941bac1710d5d767de07d292f6138cd5103c9`.
Upstream review: <https://github.com/flyinghead/flycast/pull/2616>, closing
<https://github.com/flyinghead/flycast/issues/2615> on merge.
The runtime-page-size patch extends Linux's handling to query `_SC_PAGESIZE`.
Allocation, memory protection and page tracking use that value. ELF segments
are aligned to 64 KB. Compile-time structure-layout checks use a 64 KB maximum.

Build with `python3 scripts/build-flycast.py`. Compilation uses native Homebrew
Clang/LLD and the extracted Linux sysroot. Docker is used only for a runtime
check of the resulting binary on a 4 KB Linux kernel.

The same core passes actual lock/unlock/executable-memory protection calls on
4 KB Linux and on gamepi's 16 KB kernel. The regression check deliberately
uses a 4 KB offset that lies inside a larger host page.

The standalone AppImage also queries its page size at runtime; this was verified
in its executable's startup and memory-protection instructions.

Toy Commander works through the patched core with Vulkan/XWayland; Roger
confirmed gameplay. The Pro Controller profile is detected. RetroArch's native
Wayland path blocks in `flush_wayland_fd()` at
`input/common/wayland_common.c:1178`; the active configuration selects `vk_x`
and X11 input while retaining udev controller input.

ES-DE has a Dreamcast definition pointing at `%ROMPATH%/Dreamcast`, with the
patched core installed in the Gamepi core directory. Three cue-based titles
are present: Toy Commander, Crazy Taxi, and Looney Tunes - Space Race. The
default command launches the RetroArch core; standalone Flycast is available
as an alternative emulator.

Logs: `~/.cache/gamepi/retroarch/flycast.log` and `flycast-stall.gdb.log` on gamepi.

## Core candidates

Downloaded ARM64 binaries identify as:

| Core | Version | Source date |
| --- | --- | --- |
| Flycast | `3a5267a` | 2026-11-13 |
| Dolphin | `2609.0.168+0863ee3700` | 2026-11-11 |
| ARMSX2 | `2.9.5-17-g9fed7879` | 2026-11-17 |

Dolphin is installed as the default GameCube/Wii launcher. Mario Galaxy launched
through the core on the 16 KB kernel with RX 460 Vulkan, ARM64 JIT (`CPUCore=4`)
and dual core (`CPUThread=True`) confirmed in the live log/generated config.
Its core-wide default selects an emulated Wii Remote + Nunchuk; the Pro Controller
is detected. With upstream RetroArch, both sensors enable successfully. A saved
`ProController-Nunchuk` section template supplies global WiimoteNew.ini defaults
because the core's default Nunchuk branch omits IMU bindings. L3 recenters motion
pointing. The generated config confirms those bindings loaded. Shared ALSA
output initializes successfully. Sustained performance and on-screen motion
pointing still need gameplay confirmation. Core settings and launch definitions
are in `runtime/retroarch` and `runtime/es-de`.

Roger observed motion pointing with the controller's right edge facing the
screen, instead of its top edge. The Mac Dolphin profiles use named SDL motion
axes; SDL's Nintendo driver transforms raw sensor data as
`SDL(X,Y,Z) = (-rawY, rawZ, -rawX)`. The Nunchuk profile now applies the equivalent
conversion for both accelerometer and gyro. Normal gain/FOV are restored;
sideways/upright flags are false, matching the Mac Nunchuk profiles. Mac Mater
and Kart profiles use sideways mode separately for those games. The generated
Pi config confirms the translated axes. Roger reports that motion pointing now
seems correct with the translated mapping. Keep it as the motion-input baseline.

The cursor also disappeared until the right stick moved. The core forces auto-hide in
right-stick IR modes; its timer ignores gyro movement. The Dolphin core now uses
IR mode 2, neutral simulated IR yaw/pitch (both zero), and gyro-only pointing.
The yaw range is 25 degrees. L3 recenters the current pose on screen center.

LEGO Batman exposed that the initial fix had been restricted to Mario Galaxy.
The corrected axes, saved-controller loading, Nunchuk selection, gyro-only
pointing and disabled orientation hotkeys are now core-wide defaults. Global
WiimoteNew.ini sections contain port-specific sensor qualifiers. Batman was
restarted and its generated config confirmed the corrected axes and Nunchuk
extension, with both sensors enabled. The redundant Mario .opt and RMGE01.ini
profile selection were removed after backup at
`~/.local/state/gamepi/backups/20261119T062343Z`. Keep per-game overrides for
game-specific layouts, not hardware sensor-axis conversion.

Identify RetroArch instances by executable path and core argument in
`/proc/*/cmdline`, rather than `pgrep -x retroarch`: the versioned executable
has a different process name. Check all matching instances before a restart.

Standalone Dolphin 2609a comparison: isolated user directory
`~/.local/share/gamepi/dolphin-comparison`, copied initial Wii data from the core,
Vulkan + ARM64 JIT + dual core + backend multithreading, native resolution.
Controller uses Mac SDL motion names and core-equivalent buttons. Roger reports
about 50–55% speed / 30 FPS during gameplay, full speed in a cutscene. The core
had audio stutters and felt slow; its speed percentage was not measured. A
controlled same-scene timing comparison has not been completed. Live threads
and title confirmed the selected
backend. Sampling found neither main emulation thread saturated, frequent high
GPU activity, full GPU clock and no Pi throttling. See runtime.md for details.
The application later shut down cleanly without an assistant stop command;
the trigger is unknown. No kernel GPU reset/OOM was found. ES-DE remains open.

ARMSX2 remains a candidate; loader success does not establish game execution
or 16 KB runtime compatibility. Test binaries are in
`~/.cache/gamepi/retroarch-setup/inspect`. Standalone applications remain
available.

Standalone Dolphin's GameCube config selects `SDL/0/8BitDo Pro 2`; the connected
controller identifies as Pro Controller. ARMSX2's Pad1 currently has keyboard
bindings.

## N64

Mupen64Plus-Next `3.0-Vulkan 15bada8` works with GLideN64 graphics, HLE RSP,
and the R4300 dynamic recompiler on the 16 KB kernel. The installed unmodified
core SHA256 is `53a51efd47a69c7ec9dd60907213d04f197356e036161431bad9960fc9a81fbf`.
ParaLLEl also aborts with the CPU in cached-interpreter mode, so the old
description blaming the CPU dynarec was not established. The exact ParaLLEl
failure remains unresolved. Roger's cache-alignment fix is upstream PR 1162 /
commit c5226d69; its warning text exists in the downloaded binary.

Per-core options select GLideN64/HLE/dynamic_recompiler. The core's `.cfg`
override selects glcore with context x and input x, using Cage's XWayland
display and the AMD GPU. Super Mario 64 completed a 600-frame test and clean
shutdown. ES-DE's custom N64 definition now points to the installed core,
replacing the upstream default referencing missing parallel_n64_libretro.so.
Diagnostics are in `~/.cache/gamepi/mupen-debug`. No custom core was built.

## Remote input

Use the manually started Deskflow GUI server with waynergy on the Pi via SSH.
The helper launched directly from the agent was rejected by macOS Accessibility;
the GUI-launched server accepted the Pi connection. Roger controls the GUI
layout. Switching uses screen edges; do not add keyboard shortcuts. Input
operation is not yet confirmed. See runtime.md for configuration locations.

Roger requested stopping remote input. Both waynergy instances were stopped;
a subsequent `/proc` check found no active waynergy clients. The SSH tunnel
was tied to the receiver command. No client service/autostart was installed.

## Shutdown investigation, 2026-11-19

At 10:14:19 PST, `/var/log/auth.log` records systemd-logind: "Power key pressed
short", "Powering off...", and "System is powering down." `/var/log/syslog`
then records orderly target/service shutdown. The next boot began at 10:14:49.
No kernel panic, AMD GPU timeout/reset, OOM kill or undervoltage warning was
found in the inspected pre-shutdown records. This identifies the shutdown
trigger; it does not explain a preceding application/display freeze.

Journald is explicitly volatile via
`/usr/lib/systemd/journald.conf.d/40-rpi-volatile-storage.conf`, but rsyslog's
`/var/log/syslog`, `kern.log` and `auth.log` retain previous-boot entries.
Pstore and the saved systemd pstore/coredump directories were empty. Current
`vcgencmd get_throttled` was `0x0`, which does not establish the previous boot's
power state. Latest saved Cage session log predates the incident; ES-DE's log
last recorded launching Blueman at 09:55:37. No Pi configuration was changed.

Waynergy keymap correction: raw-keymap offset=8 and
offset_on_explicit=true. The table stores Linux evdev codes; waynergy
expects XKB codes and its uinput backend subtracts 8. Restored the full map
on the Pi, replacing the commented-out version at Roger's request.
Without its mapping, left-arrow raw code 124 passed through and the backend
emitted KEY_POWER (116), plausibly explaining the 10:14:19 power-key shutdown.
Logs do not identify its originating device. Checked A/modifier/arrow
translations; no raw Mac code 0–127 maps to KEY_POWER. Physical keyboard
verification remains pending.

## Shared library migration, 2026-11-19

Moved games to `/srv/ROMs/{gc,wii,ps2,dreamcast,n64}` and immutable PS2 firmware
to `/srv/BIOS/ps2`. Verified original inodes and sizes for all 66 game/disc
files (40,259,798,066 bytes); no ROM conversion or duplicate library copy.
Cue/GDI references and ES-DE gamelist targets resolve. Library is root-owned
and read-only to gaming users. ARMSX2's local BIOS links resolve; writable
NVRAM and patch data remain local. Imported N64 saves without collisions into
the active core save folder; preserved two differing older Mario saves under
`~/.local/share/gamepi/imports/n64`. Stray Dolphin state moved intact into
`imports/dolphin/{gc,wii}`. Tool launchers moved to
`~/.local/share/gamepi/launchers`; no `~/ROMs` compatibility link remains.
Updated ES-DE's ROM root and custom paths, RetroArch's browser/history,
ARMSX2's game list, and standalone Dolphin's paths. Relative gamelist entries
and favorites metadata remain intact. Migration inventory is in
`~/.cache/gamepi/library-migration.json` on the Pi.

After migration ES-DE loaded 32 entries (30 games and two tool launchers).
180-frame N64 (GoldenEye), Dreamcast (Toy Commander), and Wii (Mario Galaxy)
tests exited with status 0. The PS2 timed boot loaded the relocated BIOS,
opened Jak II from `/srv/ROMs/ps2`, and executed its game ELF using AMD Vulkan;
it was interrupted after 12 seconds as intended (timeout status 124). No
save/config/log files appeared in the ROM library. ES-DE/Cage remains running.
Flycast reports existing unsupported texture-upscaling option lookups; these
did not prevent the smoke test and were not modified during the library move.

## Packaged kiosk session, 2026-11-20

Built native-macOS package gamepi-kiosk 0.1.0, Architecture all; source is
packaging/gamepi-kiosk, builder scripts/build-kiosk-package.py. Installed
Debian greetd 0.10.3-4 and acl plus the local package. greetd was temporarily
runtime-masked while dependencies installed, then unmasked for activation.
No existing display manager was installed. Multi-user target remains the boot
default; gamepi-kiosk.target is enabled beneath it and wants greetd.service.
The service uses a package-owned configuration and Debian's PAM stack.

Initial auto-login is roger. The session runs Cage with the stock ES-DE AppImage
and restarts it after exit. Verified a new ES-DE PID after terminating the
frontend with its game stopped. PAM sets XDG_RUNTIME_DIR=/run/user/1000 and an
active seat0 user session; remote-input.py now uses the PAM runtime directory.
No new gamepi user/home was created. Group gamepi (GID 985) was created and
roger added; verified creating/removing a test file in /srv/ROMs with inherited
GID 985. Shared library group access/default ACLs are configured by the package.
Shared defaults live under /etc/gamepi/es-de; existing Roger settings retained.

Reboot verification passed: greetd active, target enabled, Roger's PAM seat0
session active, ES-DE PID 987 started automatically with /run/user/1000.

## Kiosk audio correction, 2026-11-20

The PAM login starts the existing PipeWire/WirePlumber user services. PipeWire
owns the connected AMD HDMI PCM, so RetroArch's direct ALSA/dmix driver failed
with Device or resource busy. Changed the active Gamepi RetroArch config and
runtime template to audio_driver=pulse. A short Dolphin/Batman run initialized
PulseAudio successfully and exposed active stereo RetroArch channels routed
to PHL 346E2C alongside ES-DE. Default sink unmuted, volume 0.40. No additional
packages were installed. Remote-input work is deferred at Roger's request.

## Upstream Flycast dev test, 2026-11-20

Moved the existing fork checkout from build/flycast-src to sources/flycast,
preserving origin (archie2x-upstream), upstream, and the submitted patch branch.
Checked out upstream-dev at de3eab3e832071ef110a15891144bd4969970057 and verified
it contains 802874e79dd196faaba05fc2dd8c3d39c93c6657. Working tree and required
submodules are clean. No local source patch applied. Native Homebrew Clang/LLD
built the ARM64 core in build/flycast-dev. Dev adds basis_universal to the
required submodules. Deployable core SHA256:
273518846bb40c9b0259cdb5fbe3ed313731c8e8335c0cf2267051456ef954e7.

Deployed separately under ~/.cache/gamepi/flycast-dev on the Pi. The runtime
page-size/protection checker passed with host and core both reporting 16384.
Launched Sonic Adventure using that core, AMD Vulkan, and working PulseAudio
routing. It remains running for Roger's gameplay test. ES-DE's normal installed
core has not been replaced. Existing unsupported texture-upscaling option
lookups appear in both old and new cores and do not stop startup.
Audio fix was separately committed and pushed as 6a4b70f before this build.

Roger confirmed upstream dev gameplay works. Atomically installed that tested
binary as ~/.local/share/gamepi/retroarch/cores/flycast_libretro.so; normal
ES-DE launches now use upstream dev. The running test game was not interrupted.
