# Gamepi runtime

The frontend/emulator configuration below describes the original USB-root
installation unless noted otherwise. The fresh microSD reproducibility test
currently covers the GPU/kernel layer only; the original drive is disconnected.
See [GPU package setup](../packaging/gamepi-amdgpu/README.md) for that recipe.

On the fresh card, both GPU packages installed using APT dependencies;
install/reinstall/removal and stock-kernel reinstall coexistence passed.
Reboot selected `6.18.48-v8-16k+` with 16 KB pages, AMD GPU console output and
RX 460 RADV Vulkan enumeration. At idle the link is 2.5 GT/s, with an 8 GT/s
high power state available; sustained loaded-link verification remains open.
`vulkan-tools` was installed separately for diagnostics. The card currently
requires a sudo password after reboot. Avahi detected a name conflict and
advertises `gamepi-2.local`; direct-IP SSH works. Neither the GPU packages nor
their maintainer scripts alter hostname, network or sudo policy.

## Accepted display arrangement

Use one shared Cage session for ES-DE and its child applications. The Pi's PCIe
link connects the AMD RX 460; storage uses USB. No full desktop environment is
needed. Do not nest Cage for Dolphin, RetroArch, or settings utilities.

The `gamepi-kiosk` Debian package starts greetd at boot through
`gamepi-kiosk.target`. Its configured initial session logs in as roger using
Debian's PAM login stack and runs `gamepi-kiosk-session`: one shared Cage
session containing ES-DE and child applications. The frontend restarts after
exit or crash, with a two-second delay. Existing user settings are retained.

Build on the Mac with `python3 scripts/build-kiosk-package.py`. The package is
`build/packages/gamepi-kiosk_0.1.0_all.deb`. See
`packaging/gamepi-kiosk/README.md` for installation and configuration.
`/etc/greetd/gamepi.toml` selects the initial user and fallback text greeter;
`/etc/gamepi/session.conf` selects the AppImage and restart behavior. A graphical
greeter can later select the registered Gamepi Wayland session.

PAM supplies `XDG_RUNTIME_DIR`, normally `/run/user/1000` for roger. Remote
Wayland clients must use that directory and the session's Wayland socket.
Do not start another Cage while the managed session owns the display.
The prior `packaging/gamepi-session` prototype must not be installed.

## Applications and library

Stock ARM64 AppImages currently live in `~/Applications`:

- `ES-DE_aarch64.AppImage` (3.5.0 r52).
- `Dolphin_Emulator-2609a-anylinux-aarch64.AppImage` (community pkgforge build).
- `ARMSX2-2.9.5-Linux-arm64-16K-pages.AppImage`.
- `flycast-aarch64.AppImage`.

ROMs are shared under `/srv/ROMs`, with standard ES-DE platform directories:
`gc`, `wii`, `ps2`, `dreamcast`, and `n64`. Set ES-DE's `ROMDirectory` to
`/srv/ROMs`. The directories and game files are owned by `root:gamepi`, readable by all
users, and writable by members of the gamepi editing group. Setgid directories
and default ACLs preserve group access for new content. Keep only game images and required
cue/track files here. Game/disc files total 66 files and 40,259,798,066 bytes.

BIOS images are shared under `/srv/BIOS/ps2`. ARMSX2's existing user BIOS folder
contains links to the shared `.ROM0` and `.ROM1` images. NVRAM, `.DIFF`, `.MEC`,
and `.INF` remain user-owned alongside those links. Other platforms currently
have no separate BIOS images to relocate. RetroArch's system directory also
contains writable VMUs, NVRAM, shaders and caches; it is not a BIOS-only store
and remains in the user's home.

Imported N64 saves are in the active `saves/Mupen64Plus-Next` directory.
The two conflicting older Mario saves are preserved under
`~/.local/share/gamepi/imports/n64`. Misplaced Dolphin user trees are under
`~/.local/share/gamepi/imports/dolphin/{gc,wii}` and were not merged over the
working user state. No saves remain alongside ROMs.

ES-DE runtime data is in `~/ES-DE`. Its custom launch definitions are
`~/ES-DE/custom_systems/es_systems.xml`, currently selecting the Dolphin
RetroArch core for GameCube/Wii, ARMSX2 for PS2, and the upstream Flycast dev
RetroArch core for Dreamcast, and Mupen64Plus-Next for N64. Standalone Dolphin and Flycast remain alternative
launchers. Custom systems use the standard lowercase platform directories.
Other systems retain upstream defaults. The XML fragments in `runtime/es-de`
are definitions for merging into the custom systems file.

## Bluetooth and sound

Debian Blueman 2.4.4-1 is installed. The standard distro desktop entry is copied
to `~/.local/share/gamepi/launchers/Bluetooth.desktop`; launch it through ES-DE's Desktop
Applications system. Pairing is managed globally by BlueZ. The GUI currently
expects keyboard/mouse input; gamepad navigation has not been implemented.

RetroArch uses `audio_driver = "pulse"`, connecting through PipeWire's
PulseAudio interface. This shares the HDMI output with ES-DE. The default
PipeWire sink is the connected AMD HDMI output.

The separate ALSA configuration in `~/.asoundrc` uses the `gamepi_hdmi_mix` dmix device on
`hw:CARD=HDMI,DEV=9` (the connected RX 460 HDMI output). It mixes stereo S32_LE
at 48 kHz; a plug layer converts application formats and rates. ES-DE and
emulators can share the output. The configuration is in `runtime/asoundrc`.

## RetroArch

Debian packages already installed on 2026-11-18:

- `retroarch` 1.20.0+dfsg-2+b1.
- `retroarch-assets` 1.20.0+dfsg-1.
- `libretro-core-info` 1.20.0-1.

On a fresh Raspberry Pi OS install, use APT for these packages. Lakka is an
alternative complete OS image, not a dependency of RetroArch on Raspberry Pi OS.

The Gamepi launcher currently uses upstream RetroArch 1.22.2, Git `62eeee40e`,
instead of the installed Debian executable. Debian 1.20's udev controller driver
does not implement accelerometer/gyro callbacks. The upstream ARM64 binary
detects the Pro Controller's sibling IMU device and supplies both sensors to
Dolphin. It is a dynamically linked executable, not an AppImage:
`~/Applications/RetroArch-1.22.2-62eeee40e-aarch64`.

Download provenance:
<https://buildbot.libretro.com/nightly/linux/aarch64/2026-11-18_RetroArch.7z>.
The archive's SHA256 is
`7b17ecf21df643bcfdd0a85de5863d5176a1090dd4eba211a4489468564c30e4`.
All shared-library dependencies resolved on the Pi; version and feature checks
passed on its 16 KB kernel. Debian RetroArch remains installed. Flycast gameplay
was confirmed with Debian RetroArch; retesting it with this executable remains
open.

The inherited `~/.config/retroarch` is a symlink into
`/opt/retropie/configs/all/retroarch`. Preserve it for reference and old saves.
The Gamepi launcher explicitly selects a separate configuration:

```text
~/.local/bin/gamepi-retroarch
~/.config/gamepi/retroarch/retroarch.cfg
~/.config/gamepi/retroarch/autoconfig/
~/.config/gamepi/retroarch/remaps/
~/.local/share/gamepi/retroarch/cores/
~/.local/share/gamepi/retroarch/saves/
~/.local/share/gamepi/retroarch/states/
~/.local/share/gamepi/retroarch/system/
~/.local/share/gamepi/launchers/RetroArch.desktop
```

Reproducible configuration and launcher files are in `runtime/retroarch`.
The launcher inherits the existing Cage display session.
RetroArch uses Vulkan through XWayland (`video_context_driver = "vk_x"`,
`input_driver = "x"`) and udev controller input. The tested Flycast core is
installed at `~/.local/share/gamepi/retroarch/cores/flycast_libretro.so`.

Controller setup belongs in Settings -> Input -> RetroPad Binds -> Port 1
Controls; save a controller profile after binding. Core/game-specific layouts
belong in Quick Menu -> Controls and are saved as remaps. Standalone emulators
do not automatically consume these mappings.

### Dolphin core

The installed ARM64 core is `2609.0.168+0863ee3700`, at
`~/.local/share/gamepi/retroarch/cores/dolphin_libretro.so`. Its Sys directory is
linked from `~/.local/share/gamepi/retroarch/system/dolphin-emu/Sys` to the
installed Debian resources in `/usr/share/games/dolphin-emu/sys`.

Core options are in
`~/.config/gamepi/retroarch/overrides/dolphin-emu/dolphin-emu.opt`. Explicitly
select ARM64 JIT (`dolphin_cpu_core = "4"`), dual core
(`dolphin_main_cpu_thread = "enabled"`), hardware rendering and normal CPU
clock. RetroArch's Vulkan driver selects Dolphin's Vulkan backend. The baseline
settings are recorded in `runtime/retroarch/Dolphin.opt`.

The same core-wide options select Nunchuk for Wii input, enable saved controller
settings, disable sideways/upright toggle hotkeys, and configure gyro-only
pointing. These defaults apply to all Wii games launched through the core.
GameCube uses the core's GameCube pad handling. The controller defaults live in:

```text
~/.local/share/gamepi/retroarch/saves/dolphin-emu/User/Config/WiimoteNew.ini
```

`runtime/retroarch/ProController-Nunchuk.ini` is the reusable section template.
Populate Wiimote1 through Wiimote4 defaults with it, replacing `Libretro/0/`
with the corresponding zero-based port number. Existing source/enable values
for unused ports are preserved; gameplay has been tested with player 1 only.
It binds the accelerometer and gyro from
`Libretro/0/Sensor`, enables motion pointing, and uses L3 (left-stick click)
to recenter. Left stick controls Nunchuk movement and R2/ZR triggers Wii Remote
shake. Motion bindings translate the Mac Dolphin Nunchuk profile's named SDL
axes to the Nintendo controller's raw evdev axes. SDL's Nintendo driver uses
`SDL(X,Y,Z) = (-rawY, rawZ, -rawX)` for both acceleration and gyro. Combined
with Dolphin's SDL axis names, the positive bindings are:

| Dolphin input | Raw Libretro sensor |
| --- | --- |
| Accel Up | AccelZ+ |
| Accel Left | AccelY+ |
| Accel Forward | AccelX+ |
| Gyro Pitch Up | GyroY- |
| Gyro Roll Left | GyroX- |
| Gyro Yaw Left | GyroZ+ |

Opposite directions use the opposite sign. Gain and camera FOV use their normal
defaults; the yaw range is 25 degrees. Both sideways and upright Wii Remote
flags are explicitly false for this Nunchuk profile. The physical controller's
top edge should face the screen. Recenter uses the current pose as screen-center
reference.

The source Mac profiles distinguish Wii Remote orientation per game: `NC 1`
and `NC 2` select Nunchuk without sideways mode, while `Mater` and `Kart`
profiles enable sideways mode. Preserve that per-game distinction when adding
other Wii profiles. Axis conversion is separate from emulated Wii orientation.
The relevant mappings are defined in SDL's
[Nintendo driver](https://github.com/libsdl-org/SDL/blob/release-3.2.26/src/joystick/hidapi/SDL_hidapi_switch.c)
and Dolphin's
[SDL axis definitions](https://github.com/libretro/dolphin/blob/0863ee3700978e826b0d95b72d4742e537a7325b/Source/Core/InputCommon/ControllerInterface/SDL/SDLGamepad.h).

The Dolphin core defaults select IR mode 2 with simulated IR yaw/pitch both zero. This keeps
the simulated pointer neutral while allowing gyro pointing. The core forces
auto-hide on in either right-stick IR mode, even when a saved profile disables
it; its timer watches simulated pointer movement and therefore hides the cursor
during gyro-only movement. Mode 2 disables that timer. Right stick is no longer
a pointer fallback in this setup. The profile and neutral simulated pointer
settings were confirmed in the generated config; both sensors enabled in the
live log. Roger observed gyro motion but needed to point the controller's right
edge at the screen with the unconverted raw axes. The translated axes were
confirmed in the restarted game's generated config; the corrected physical
orientation now seems correct according to Roger's on-screen test. Keep this
mapping as the motion-input baseline; sustained performance and the remaining
controller actions still need separate gameplay checks.

LEGO Batman also loaded these corrected defaults after restart, with both
sensors enabled and Nunchuk attached. The redundant Mario-only options file and
RMGE01 profile selection were removed after backup. Future per-game overrides
should express actual game differences, such as sideways mode, rather than
duplicate hardware-axis corrections or the full shared core configuration.

Mario Galaxy was launched from ES-DE on the 16 KB kernel. Its live log selected
the RX 460 Vulkan device, initialized shared ALSA output, and detected the Pro
Controller. Generated `User/Config/Dolphin.ini` confirmed `CPUCore = 4`,
`CPUThread = True`, and `GFXBackend = Vulkan`; `WiimoteNew.ini` confirmed the
Nunchuk extension. This verifies launch and settings, not sustained game speed.
The log is `~/.cache/gamepi/retroarch/dolphin.log`. Saves and generated Dolphin
configuration live under
`~/.local/share/gamepi/retroarch/saves/dolphin-emu/User`, separately from the
standalone application's data.

### Mario Galaxy ultrawide (confirmed 2026-11-20)

Roger confirmed the USA game's 21:9 Action Replay code works well in the
Dolphin core. The code is in the core user's `GameSettings/RMGE01.ini`:

```ini
[ActionReplay]
$21:9 Aspect Ratio
046A4964 40155555
040972AC 60000000
046AC6D4 3F124925
04367118 60000000

[ActionReplay_Enabled]
$21:9 Aspect Ratio
```

In `~/.config/gamepi/retroarch/overrides/dolphin-emu/`, the content override
`Super Mario Galaxy (USA) (En,Fr,Es).nkit.cfg` sets `aspect_ratio_index = "24"`
(full viewport). There is no Mario-specific `.opt` file: all Dolphin games use
the shared `dolphin-emu.opt`, with `dolphin_efb_scale = "2"`,
`dolphin_cheats_enabled = "enabled"` and `dolphin_cheats_import = "disabled"`.
Dolphin's code engine is enabled globally, while only Mario's game INI enables
the ultrawide code. Native Wii widescreen stays enabled and the generic
widescreen hack stays disabled. The ultrawide test restored the saved position
after restart and was confirmed by Roger. The later shared 2x resolution
change was verified in the files with the game closed; gameplay at 2x is not
yet tested. The code and full-viewport override apply only to Mario Galaxy.
The published code targets 21:9, while 3440x1440 is slightly wider; exact
aspect correction has not been separately measured.

The ultrawide code is specific to the test display and must be disabled for a
16:9 TV; return Mario's RetroArch aspect setting to Core Provided at that time.
Internal resolution is a shared Dolphin default, independent of display size.

### Standalone Dolphin comparison

The existing Dolphin 2609a AppImage was tested with a separate user directory,
`~/.local/share/gamepi/dolphin-comparison`. Its Wii data started as a snapshot
of the core's Wii directory; subsequent saves are independent. Existing
standalone configuration and the ES-DE default launcher were not changed.

The comparison selects ARM64 JIT (`CPUCore=4`), dual core (`CPUThread=True`),
Vulkan, native internal resolution, and graphics backend multithreading. The
graphics settings start from the core's GFX.ini, with FPS/speed display and
backend multithreading enabled. Core graphics backend multithreading was false.
Cubeb initialized its ALSA backend and opened the shared AMD HDMI PCM device.
The controller profile uses SDL motion names from the Mac Nunchuk profile,
with buttons matching the tested core layout and left-stick click to recenter.

Launch inside the existing shared Cage display session:

```sh
"$HOME/Applications/Dolphin_Emulator-2609a-anylinux-aarch64.AppImage" \
  -u "$HOME/.local/share/gamepi/dolphin-comparison" -b -v Vulkan \
  -C Dolphin.Core.CPUCore=4 -C Dolphin.Core.CPUThread=True \
  -C GFX.Settings.BackendMultithreading=True \
  -e "/srv/ROMs/wii/Super Mario Galaxy (USA) (En,Fr,Es).nkit.iso"
```

Roger reported approximately 50–55% speed / 30 FPS during standalone gameplay,
with a cutscene reaching full speed. The core had stuttering audio and felt
slow, but its speed percentage was not measured. These observations are not
a controlled identical gameplay comparison. Standalone's window title confirmed
`JITARM64 DC | Vulkan | HLE`; live CPU, video and Vulkan submission threads were
present. A 15-second sample showed CPU thread around 41–47% of one CPU, video
thread around 38–44%, GPU activity frequently 94–100% at 1250 MHz, no Pi
throttling, and temperature 56 C. Scene transitions limit interpretation of
that sample. PCIe negotiated 5 GT/s at x1. GPU descriptors showed rendering work
on AMD, with no measured V3D engine work in the inspected descriptors.

The standalone process later exited without an assistant stop command. Its log
shows orderly Wii filesystem and audio shutdown; the inspected kernel log had
no GPU reset, fault or OOM report. The trigger is unknown. Batch mode closes
the application when emulation stops. Logs and samples are under
`~/.cache/gamepi/dolphin-comparison`, and its Dolphin log is in the comparison
user directory's `Logs` folder.

## Kernel and performance findings

### PCIe Gen 3 on RX 460 (2026-11-20)

`/boot/firmware/config.txt` already requested Gen 3. The boot log reported
8 GT/s x1, but the live link subsequently ran at 5 GT/s and AMD's
`pp_dpm_pcie` exposed only Gen 1/2 states. The firmware setting alone did not
keep the GPU at Gen 3.

Keep `dtparam=pciex1_gen=3` in `config.txt` and append
`amdgpu.pcie_gen_cap=0x70007` to the existing single line in
`/boot/firmware/cmdline.txt`. This driver capability mask enables Gen 1–3 for
both GPU and platform; its definitions are in the kernel's
`drivers/gpu/drm/amd/include/amd_pcie.h`. The kernel and modules were unchanged.

After reboot, both PCIe sysfs `current_link_speed` and AMD's active power state
reported 8 GT/s, with actual width x1. A 40-second Mario Galaxy sample retained
that speed with zero reported correctable, nonfatal or fatal PCIe errors.
The power-state table's x8/x16 labels are not the negotiated physical width.

Reloading the same RetroArch save state gave sampled window-title FPS averages
of 40.03 at Gen 2 and 54.41 at Gen 3. Samples include startup/scene variation;
they are a short comparison, not a sustained gameplay benchmark. Both tests
held the CPU at its stock 2.4 GHz using the temporary `performance` governor;
that governor remains active for this performance investigation and resets on
reboot. No CPU overclock or persistent governor change was installed.
Measurements are `~/.cache/gamepi/galaxy-gen{2,3}-comparison.json` on the Pi.

A subsequent 20-second gameplay sample measured 46.86–49.56 FPS with Gen 3
stable, no reported correctable PCIe errors and no Pi throttling. Neither main
CPU thread saturated a core; the game's AMD gfx engine averaged 64.3% busy.
GPU memory snapshots alternated between 300 and 1750 MHz despite the core
remaining at 1250 MHz. The bottleneck is not yet isolated. Details are in
`~/.cache/gamepi/galaxy-slow-gen3.json`; no settings changed during this sample.

The working kernel is `6.18.48-v8-16k+`, page size 16384, with Raspberry Pi AMD
GPU support from PR 7113. Preserve boot files and corresponding modules before
any kernel replacement or reinstall. Do not run rpi-update or APT upgrades as
part of frontend configuration work.

Dolphin Vulkan substantially reduced its Video thread CPU load compared with
OpenGL in the tested Mario Galaxy area. Roger reported good playability;
precise sustained speed measurements remain open. Earlier pink/blue GPU hangs
were investigated before Roger discovered unplugged GPU power. They do not
establish a Cage incompatibility.

## Remote keyboard and mouse trial

Deskflow 1.27.0 on the Mac serves a waynergy v0.0.17 uinput receiver in
the existing Pi Cage session, using an SSH reverse tunnel. The Mac server
uses port 24800; the Pi tunnel endpoint uses 24805. Connection was observed
in both logs; keyboard and mouse operation remain to be verified.

The active Mac configuration is `~/Library/Deskflow/Deskflow.conf` and its
GUI-generated layout is `~/Library/Deskflow/deskflow-server.conf`. Roger reset
the layout and placed gamepi to the left of rabbit.lan. There are no switching
hotkeys in the current configuration or the project layout template. Switch
computers using the configured screen edges. No startup service is installed.

## N64 libretro configuration

Use the unmodified `mupen64plus_next_libretro.so` with GLideN64, HLE RSP and
CPU dynamic recompilation. Install `runtime/retroarch/Mupen64Plus-Next.opt`
and `.cfg` under `~/.config/gamepi/retroarch/overrides/Mupen64Plus-Next/`.
The `.cfg` selects desktop OpenGL through XWayland only for this core; the
other cores retain their Vulkan settings. Merge `runtime/es-de/n64.xml` into
ES-DE's custom systems definition and restart the frontend. No N64 BIOS is
required for these cartridge games. Imported `.srm` files are in RetroArch's separate save directory; conflicting
older versions are preserved separately in the user imports directory.

A 600-frame Super Mario 64 test used the ARM64 CPU dynarec and AMD OpenGL
inside Cage and exited cleanly. The ParaLLEl path still aborts, including with
the main CPU interpreter selected, and is not the configured default.

## Shared configuration and library editors

Package-managed defaults are under `/etc/gamepi/es-de`. The session launcher
copies initial settings only if a user has no ES-DE settings file; it does not
layer defaults over existing settings. Current defaults set ROMDirectory to
`/srv/ROMs`. Package-owned /etc files are conffiles, preserving local edits.

`/etc/gamepi/library-editors` lists local accounts added to group gamepi at
package configuration; roger is the initial editor. The package creates only
the group, not a gamepi user. Installation configures existing library access;
upgrades preserve existing content permissions. ROMs and BIOS remain at their
current paths and are never included in the package payload.

## Flycast upstream dev

ES-DE uses unmodified upstream dev at
`de3eab3e832071ef110a15891144bd4969970057`. The checkout is in sources/flycast;
outputs are under build/flycast-dev. The Pi's installed core SHA256 is
`273518846bb40c9b0259cdb5fbe3ed313731c8e8335c0cf2267051456ef954e7`.
The runtime page-protection check passes on the 16 KB kernel. Roger confirmed
Sonic Adventure gameplay; that tested binary is the default installed core.
