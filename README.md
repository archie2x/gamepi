# Gamepi

A controller-operated TV gaming appliance for Raspberry Pi 5 and Linux ARM64.

Gamepi integrates existing software on Raspberry Pi OS 64-bit, using the stock
ES-DE AppImage as its frontend. The current milestone is Flycast through
RetroArch and controller support for Dolphin and ARMSX2, alongside Blueman.
The library should
focus on games, with a choice of installed versions when a title is available
on multiple platforms.

## Repositories

- [archie2x/gamepi](https://github.com/archie2x/gamepi): integration, build tooling,
  configuration, notes, and optional build tooling.
- [archie2x-upstream/es-de](https://github.com/archie2x-upstream/es-de): our ES-DE
  source fork, imported from [GitLab](https://gitlab.com/es-de/emulationstation-de).
  GitHub cannot create a native fork relationship with a GitLab repository.

`sources/es-de` is a submodule pinned to the ES-DE 3.5.0 release. Its `gamepi`
branch is where frontend changes will be developed. `origin` points to our
GitHub fork. When working on the fork in a fresh clone, add the original GitLab
repository as its `upstream` remote:

```sh
git -C sources/es-de remote add upstream https://gitlab.com/es-de/emulationstation-de.git
```

## Current state

The runtime direction is integration first: one shared Cage session contains
the stock ES-DE AppImage and the applications it launches. Use distro packages,
RetroArch cores where useful, and standalone emulator AppImages where preferred.
No full desktop environment or nested compositor is needed.
See [runtime setup](docs/runtime.md) and [working notes](docs/notes.md).

The local `gamepi-kiosk` Debian package provides boot startup through greetd,
frontend restart behavior, shared defaults, and the library editing group.
Build it with `python3 scripts/build-kiosk-package.py`; see
[package source and setup](packaging/gamepi-kiosk/README.md).

The GPU/kernel packages are built with
`python3 scripts/build-gpu-packages.py` from a checksum-pinned upstream binary
artifact. `gamepi-amdgpu` depends on the packaged Pi 5 kernel and distro AMD
firmware/Mesa, and selects a separate versioned boot directory. See
[GPU package source and fresh-card setup](packaging/gamepi-amdgpu/README.md).

The older `packaging/gamepi-session` prototype implements a superseded launch
scheme and must not be installed as the current setup. A fresh Raspberry Pi OS
Lite 64-bit microSD installation is now testing the packaged GPU/kernel layer.
The original USB installation is retained separately; its frontend/emulator
configuration has not yet been reproduced on the card. A separate library
drive remains a proposal. The Pi's PCIe link is occupied by the AMD GPU.

The native macOS cross-compilation setup works. Its C++ and stock SDL2 probes
have run successfully on gamepi with a 16 KB kernel. The runtime uses downloaded
AppImages; building the ES-DE fork is not required for the current milestone.

```text
sources/es-de/     ES-DE source submodule
toolchain/        Docker-derived sysroot extraction, Clang toolchain, and probes
build/            Generated output (ignored)
```

## Optional cross-compilation

```sh
git clone --recurse-submodules https://github.com/archie2x/gamepi.git
cd gamepi
python3 toolchain/extract-sysroot.py
cmake --preset probes
cmake --build --preset probes
```

The initial executables are `build/probes/bin/hello` and
`build/probes/bin/sdl-probe`. The current build compiles these probes, not ES-DE.
See [toolchain/README.md](toolchain/README.md) for dependencies and details.

The Docker image supplies a disk-resident Linux sysroot. Homebrew Clang and LLD
execute natively on the Mac. The source image is pinned by digest in
`toolchain/sysroot-image.json`; the extracted sysroot is not stored in Git.
The sysroot and checkout belong on a case-sensitive filesystem (`~/src` on the
development Mac).

## Design constraints

- Run ES-DE and child applications inside one shared Cage session.
- Prefer existing `.deb` packages and ARM64 AppImages; defer custom packaging.
- Prefer distro libraries and packages where suitable.
- Support both standalone emulators and libretro cores where useful.
- Reuse RetroArch-compatible controller profiles where practical, preserving
  input-driver identity when translating mappings.
- Keep Bluetooth pairing and persistent player assignment distinct from button
  mappings. Standalone emulator adapters remain later work; RetroArch mappings
  do not automatically configure standalone applications.
- Keep upstream modifications as small, separate commits, with tested source
  revisions pinned by the superproject.

Emulator packaging compatibility and a public APT repository are later work.
