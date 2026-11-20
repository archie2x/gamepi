# RetroArch integration

## Packages and launch

Use Debian packages `retroarch`, `retroarch-assets`, and `libretro-core-info`.
`retroarch-dbgsym` provides matching debugger symbols. Lakka is a separate OS
image and is not required.

Install these files as the gaming user:

```sh
install -Dm644 retroarch.cfg "$HOME/.config/gamepi/retroarch/retroarch.cfg"
install -Dm755 gamepi-retroarch "$HOME/.local/bin/gamepi-retroarch"
install -Dm644 RetroArch.desktop "$HOME/.local/share/gamepi/launchers/RetroArch.desktop"
```

Create the directories named in the configuration before use. Preserve an
existing configuration when reinstalling: RetroArch saves interactive settings
there. The desktop entry currently names Roger's home directory explicitly.
ES-DE may need its game list rescanned/restarted to notice a new desktop entry.

Run the launcher inside the shared Cage session. Games and settings applications
inherit its display; they do not start another compositor. A bare SSH shell
does not inherit the graphical environment.

## Flycast core

Build with `python3 scripts/build-flycast.py`. The pinned source and runtime
page-size patch are documented in `patches/flycast/README.md`. The output is
`build/flycast-core/flycast_runtimepages_libretro.so`.

The source uses `_SC_PAGESIZE` at runtime for Linux allocations, protection and
page tracking. The ELF has 64 KB LOAD alignment. The same binary passes the
memory-protection regression check on 4 KB Linux and gamepi's 16 KB kernel.
Game execution is being tested separately.

## Display and input

The frontend uses Vulkan on the AMD GPU through XWayland, with
`video_context_driver = "vk_x"` and `input_driver = "x"`. Controller input uses
`udev`. These settings are saved in the Gamepi configuration. The patched
Flycast core is installed at
`~/.local/share/gamepi/retroarch/cores/flycast_libretro.so` and selected by ES-DE's
Dreamcast definition.

Controller setup: Settings -> Input -> RetroPad Binds -> Port 1 Controls, then
Save Controller Profile. Use Quick Menu -> Controls for core/game remaps.

Keyboard bindings: P pauses/resumes, F1 opens the menu, K advances a paused
frame, Escape exits. The upstream Nintendo Switch Pro Controller udev profile
provides a Home-button menu binding. Controller gameplay and exit/return still
need verification.

RetroArch uses `audio_driver = "pulse"` to connect to the kiosk user's
PipeWire server through its PulseAudio interface. ES-DE and RetroArch share
the selected output. RetroArch's audio synchronization is enabled. The direct
ALSA/dmix configuration in `runtime/asoundrc` must not be used by RetroArch
while PipeWire owns HDMI.

## Mupen64Plus-Next

The upstream RetroArch executable used by `gamepi-retroarch` supports desktop
OpenGL. Install `Mupen64Plus-Next.opt` and `Mupen64Plus-Next.cfg` in
`~/.config/gamepi/retroarch/overrides/Mupen64Plus-Next/`. These select GLideN64,
HLE RSP, CPU dynarec and XWayland OpenGL for N64. Merge `../es-de/n64.xml` into
the frontend's custom systems file. This configuration uses the existing
unmodified ARM64 libretro core; no emulator source patch is required.
