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

## PCIe Gen 3 test, 2026-11-20

The existing firmware Gen 3 request trained at 8 GT/s during boot, but the
running RX 460 link dropped to 5 GT/s and AMD exposed no Gen 3 power state.
Removed the inline comment from the existing `dtparam=pciex1_gen=3` line;
rebooting with that alone still resulted in Gen 2. Added the verified driver
capability override `amdgpu.pcie_gen_cap=0x70007` to the existing firmware
cmdline and rebooted. Live link and active AMD power state now both report
8 GT/s; negotiated width remains x1. Existing kernel, initramfs policy and
other boot arguments were preserved.

Saved Mario Galaxy before reboot and loaded that state for each comparison.
An extra test launch briefly overlapped a game Roger had already started;
terminated the extra process before collecting either comparison dataset.
With one game instance and CPU governor held at stock 2.4 GHz performance,
six Gen 2 FPS samples averaged 40.03; eight Gen 3 samples averaged 54.41.
Gen 3 remained active through the 40-second loaded sample, and all reported
PCIe AER error counters were zero afterward. Vulkan selected RX 460 and the
PulseAudio driver initialized. The game remains running; CPU governor is
still temporarily performance, with no persistent governor configuration.
See docs/runtime.md for boot settings and measurement paths.

During Roger's subsequent slow gameplay report (47.75 FPS), a nonintrusive
20-second sample measured 46.86–49.56 FPS. Gen 3 stayed at 8 GT/s, reported
correctable PCIe errors remained zero, CPU stayed at 2.4 GHz, temperature was
57.6 C, and throttled=0x0. Main/render and emulation CPU threads used 59.9%
and 58.2% of one core; the game's AMD gfx engine accumulated 64.3% busy time.
GPU core stayed at 1250 MHz, while memory snapshots alternated between 300
and 1750 MHz. This does not isolate a bottleneck; memory power management is
a candidate for a controlled test. No settings or game state were changed.
Detailed sample: ~/.cache/gamepi/galaxy-slow-gen3.json on gamepi.

## Mario Galaxy ultrawide, 2026-11-20

Applied the four-line USA/NTSC 21:9 Action Replay code to the Dolphin core's
User/GameSettings/RMGE01.ini, with the named code enabled. Created Mario-only
RetroArch `.cfg` (full viewport, aspect_ratio_index=24) and `.opt` (existing
profile with internal cheats enabled and cheat import disabled). Native Wii
widescreen remains on; generic widescreen hack remains off. Saved Roger's
current position before stopping, restarted with one core instance, verified
the content overrides loaded, and restored the saved state. Roger confirmed
the result works great. No internal resolution, controller or other-game
settings changed. The game remains running. Runtime documentation includes
the exact code and file locations. Source of the published code:
https://www.reddit.com/r/DolphinEmulator/comments/zuuzik/.

Roger requested 2x native as the default for all Dolphin games. With RetroArch
closed, set dolphin_efb_scale=2 in the shared dolphin-emu.opt. Enabled Dolphin's
internal code engine globally and disabled the RetroArch cheat importer, then
removed Mario's copied .opt after checking that it differed only in these
options. Mario's game INI and viewport .cfg remain game-specific. This removes
the duplicated controller/resolution profile. Updated runtime/retroarch/Dolphin.opt
to match. Readback verified the settings; no game was launched, so the 2x
performance/visual test remains for the next launch. Ultrawide is a test-screen
setting, not the intended 16:9 TV default.

## Fresh microSD GPU/kernel packaging test, 2026-11-20

Roger imaged a separate 128 GB microSD with Raspberry Pi OS Lite 64-bit and
completed stock updates. SSH/passwordless sudo verified. Root and firmware
are /dev/mmcblk0p2 and /dev/mmcblk0p1; the USB installation is not attached.
Initial running kernel was 6.18.50+rpt-rpi-2712 with 16 KB pages; installed
stock kernel packages were already 6.18.60. No existing gamepi-kiosk package
or AMD firmware/Mesa runtime was installed on the card.

Built native-macOS gamepi-kernel-rpi5 6.18.48+eef16e98-1 and gamepi-amdgpu
0.1.0 from checked-in packaging source and checksum-pinned upstream bcm2712
artifact. No kernel compilation or rpi-update invocation. The artifact is a
ZIP containing bcm2712_build.tar; cache and generated packages remain under
build/. Five preservation/rollback tests passed. The kernel package owns
canonical boot payload and matching modules; activation copies its 408 boot
files to a separate os_prefix directory and generates a cmdline retaining
the card's own PARTUUID=76f5e8f9-02. No display mode, CPU policy or EEPROM
settings were changed.

Installed both packages with apt, which resolved AMD firmware/Mesa dependencies.
Verified reinstall idempotency, removed the activation package and verified
all recorded stock boot-file hashes restored, then reinstalled activation.
Reinstalled the stock 6.18.60 Pi 5 kernel through apt; its normal initramfs and
raspi-firmware hooks ran while all custom boot payload hashes and the selected
include remained intact. Fresh-card initramfs generation succeeded with its
stock policy, so the old USB MODULES=most workaround was not carried over.
Installed distro vulkan-tools solely as a diagnostic, outside package runtime
dependencies. Rebooted; Roger confirmed console output on the AMD GPU monitor.
Direct-IP SSH verified the booted kernel is 6.18.48-v8-16k+, page size 16384,
root remains on mmcblk0p2, and amdgpu is bound to the RX 460. vulkaninfo
identified AMD Radeon RX 460 Graphics (RADV POLARIS11), Mesa 26.2.7, Vulkan
1.4.354. At idle the link is 2.5 GT/s; the AMD PCIe table offers 8 GT/s as its
high state. An optional forced-high-state test did not run because sudo now
requires a password after reboot; automatic GPU power management was not
changed. Gen 3 under workload on this fresh card remains to be measured.

The SSH interruption was mDNS naming: Avahi logged a hostname conflict and
switched to gamepi-2.local. Static hostname and DHCP host_name remain gamepi;
Ethernet is 192.168.87.250 and Wi-Fi 192.168.87.80. Direct SSH to the Ethernet
IP, checked against gamepi.local's known host key, works. No network settings
were changed. No kiosk, frontend, emulator or ROM setup has been installed on
this card. GPU/kernel packaging source and the tested installation recipe are
in this repository; binaries have not been published to an APT repository.

## Render96ex cross-build, 2026-11-22

Roger asked for the Render96 Super Mario 64 PC port alongside the emulators.
Added scripts/build-render96ex.py. It pins Render96/Render96ex branch tester
at 61480c4e6e5c7e7bed40341c0aa76b75d405c3c7. Branch master was tried first and
rejected: it has no DynOS, so it cannot load the Render96 model pack.

Upstream uses a GNU Makefile, not CMake, so the script generates
aarch64-linux-gnu-{gcc,g++,cpp,as,objcopy,objdump} and sdl2-config wrappers
around Homebrew Clang/LLD, llvm-objcopy and sysroot pkg-config under
build/render96ex/cross-bin, and passes CROSS/CC/CXX to gmake. Findings:

- macOS make 3.81 lacks the != operator; the wrappers put gmake first as make.
- HOST_OS=Linux is passed, otherwise the Makefile selects its macOS target.
- Upstream forwards the game's CC to its asset tools. The script builds the
  tools first with the Mac compiler, serially (tabledesign races the
  audiofile library), with -D_DARWIN_C_SOURCE for vsnprintf.
- TARGET_RPI=1 was not used: it selects GLES2 and derives -march from the
  build machine. The build links desktop libGL for the AMD card.
- Clang rejects 28 texture-coordinate literals wider than 64 bits in
  actors/luigi_cap/model.inc.c. GCC warns and truncates; all become 0 as s16.
  patches/render96ex/luigi-cap-texcoord-literals.patch writes those zeros.
- Clang 16+/GCC 14 errors for incompatible pointer types (u64* against
  uint64_t*) are demoted to warnings in the C wrapper.
- The one assembly sequence (00_sound_player.s) assembles with Clang's
  integrated assembler through the as wrapper.

Assets were extracted from Roger's US ROM (SHA-1 9bef1128..., matching
sm64.us.sha1), copied to the ignored checkout as baserom.us.z64. No sysroot
changes and no Python packages were needed; SDL2 and libGL were already there.

Result: sources/render96ex/build/us_pc/sm64.us.f3dex2e, ELF aarch64, 64 KB
segment alignment, SHA256
7d0e75b7d0288e009cf96cda0d3b761f8f6567cf2ed05b8bd272465bccfa2120, needing
libSDL2-2.0, libGL, libstdc++, libgcc_s, libm and libc. res/based.zip holds
1634 files. In the pinned Docker image (4 KB pages, repository directory
mounted read-only, no network) all libraries resolved and the program ran
through SDL offscreen window and OpenGL setup, then stopped at "Failed to
initialize device for music": the container has no audio device. Log:
build/render96ex/build.log.

The build output contains ROM-derived assets and must stay out of Git and out
of any published package.

### Installed on the NVMe prototype

Roger confirmed the NVMe installation was booted and asked for installation,
a launcher and both packs. Verified root /dev/sda2, kernel 6.18.48-v8-16k+,
16 KB pages and an idle ES-DE before changing anything. Direct SSH used the
existing gamepi alias with HostKeyAlgorithms=ssh-ed25519 per invocation; no
SSH configuration was edited. No packages were installed and sudo was not used.

Added scripts/install-render96ex.py and runtime/render96ex/. The script stages
build/render96ex/stage/render96ex from the build output, the model pack
Render96_DynOs_v3.25.7z (Render96/ModelPack 3.25, four pack directories into
dynos/packs) and Render96.HD.Texture.Pack.1.3.26.7.7.7z (overlaid on res/gfx;
1345 of the 1629 base texture names are replaced). Both archives are pinned by
SHA-256 and cached under build/downloads/render96ex. With --host and
--expected-root it checks the root device, refuses to update a running game
and copies with rsync, without --delete.

On the Pi: ~/.local/share/gamepi/render96ex (842 MB), the launcher
~/.local/bin/gamepi-render96ex, and /srv/ROMs/ports/Super Mario 64
(Render96).sh for ES-DE's bundled Ports system. es_systems.xml was not
changed. DynOS leaves model packs disabled by default, so a first-run
~/.local/share/sm64ex/DynOS.1.1.alpha.config.txt enabling the four packs was
seeded; the script never overwrites an existing one.

Two launches through the launcher from SSH, in the running Cage session, ran
for 40 and 45 seconds until the test's SIGTERM and exited cleanly, saving
sm64config.txt. The process opened the amdgpu render node, loaded Mesa's
libGL through XWayland and libpulse, found all four packs and reported "Pro
Controller has haptics support, rumble enabled". Log:
~/.cache/gamepi/render96ex.log. The pack's extra non-texture PNGs produce
harmless "unknown texture format" lines during precaching.

Not verified: nobody looked at the picture or listened, so rendering, HD
textures, whether the seeded pack keys take effect, sound, frame rate and
button layout are unconfirmed. ES-DE was not restarted, because the session's
restart behaviour on this installation was not established; Ports appears
after a ROM-directory rescan or the next frontend start. vsync defaults to
false and 60 fps to true in the generated configuration. Nothing is packaged.

Roger reported the game came up in French. Cause: text-loader.c numbers
languages in readdir order and the default configuration selects index 0; on
the Pi's ext4 the first file was FR_fr.json. patches/render96ex/
sorted-language-files.patch loads the files with scandir/alphasort, making
index 0 AM_us (English) on any filesystem. Rebuilt; executable SHA256
efca75714492fda5af9eb2657028d0e2bfec5ecdc612571b4746a552ec19e75c. This
supersedes the hash above. The existing sm64config.txt keeps `language 0`.

### Render96ex controls matched to the N64 core

Roger asked for the same controls as the established Mupen64Plus-Next setup.
An SDL probe on the Pi (ctypes, loading the game's own gamecontrollerdb.txt)
showed the Pro 2 arrives through evdev/hid-nintendo with GUID
0500d71f7e0500000920000001800000 and positional buttons: SDL a is raw b0
(printed B), b is b1 (printed A), x is b3 (printed Y), y is b2 (printed X).
The game's defaults therefore put N64 A on printed B and N64 B on printed Y,
and bound Z to the left-stick click and both R and R2 to N64 R.

runtime/render96ex/controls.txt now binds printed A to N64 A, printed B to
B, L2 to Z, L/R to L/R, Start and the D-pad; the right stick already drives
the C buttons. The installer merges only those keys, plus `language 0`, into
sm64config.txt. patches/render96ex/mupen-style-controls.patch adds what the
game cannot express in its configuration: holding R2 turns the face buttons
into C buttons by position (X up, Y left, A right, B down) and suppresses
A/B, and Star/Capture pressed twice within three seconds exits. Unlike
RetroArch there is no on-screen prompt after the first press. The launcher
exports SDL_GAMECONTROLLERCONFIG so Capture is available as misc1; the probe
confirmed this mapping takes precedence over the game's database. Heart/Home
has no function here. Executable SHA256
cfdbaa2ba5476f5ecfec24217c73f2064bd647590b941a6727e99d82389b6092, installed
with the language fix after Roger exited the game. Roger had changed the
language index in-game to 4; it was reset to 0, which is now English.
Not yet played with the new bindings.

### Render96ex slow, invisible start and double launches

Roger reported that launching took a long time with ES-DE still visible, and
that launching again produced two instances. Cause: `precache true` (the
game's default) loads every texture before the first frame, and until the
first buffer swap the window has no content, so Cage keeps showing ES-DE.

patches/render96ex/precache-loading-screen.patch counts the textures, then
draws a black screen with a progress bar (scissored clears only) every 16
textures during precaching. The launcher now runs the game under
`flock --nonblock` on $XDG_RUNTIME_DIR/gamepi-render96ex.lock and opens the
log only after taking the lock. Executable SHA256
bd1a53b2b98f1a930ac696a906d76eefaffaa2b16d11d5d29ae38b9f26cff124, installed
after Roger exited the game.

Tested from SSH in the Cage session: a second launcher invocation one second
after the first exited with status 1 and one instance remained. Precaching
began about 3 s after launch; file reads reached 390 MB at about 18 s and then
stopped growing, so loading takes roughly 15-20 s with the HD pack. This is an
I/O-based estimate: stdout is block-buffered into the log, the Pi has no bc,
and an earlier attempt lost its timestamps. That run ended at 44 s with a
clean exit and saved configuration, which was not sent by the test; Roger was
probably at the controller. Nobody has confirmed the progress bar's
appearance. Precaching was left enabled; `precache false` in sm64config.txt
(Options, also in-game) trades the wait for first-use hitches.

Roger then saw the intro (Mario's face) run fast-forward after loading. This
was a defect in the loading-screen patch, not a collision with a test launch
as first suggested to him: upstream's frame limiter advances its clock by one
frame per buffer swap, and the progress bar swapped only about 140 times
during a 15 s load, so the game ran unthrottled afterwards to "catch up".
The patch now resynchronizes the limiter whenever it is more than 250 ms
behind. Executable SHA256
c6b6344dc565c4a849202d886c778501feb1a7775f9ab9c2060c3a7d4e5dcc1d, installed
while no game was running; no test launch was made. Awaiting Roger's check.
The progress bar shows textures loaded out of the counted total; it is not a
timed animation.
