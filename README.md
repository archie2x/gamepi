# Gamepi

A controller-operated TV gaming appliance for Raspberry Pi 5 and Linux ARM64.

Gamepi uses ES-DE as its frontend base. The first milestone is integrated
Bluetooth pairing and shared controller configuration. The library should
focus on games, with a choice of installed versions when a title is available
on multiple platforms.

## Repositories

- [archie2x/gamepi](https://github.com/archie2x/gamepi): integration, build tooling,
  configuration, and Debian packaging.
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

The native macOS cross-compilation setup works. Its C++ and stock SDL2 probes
have run successfully on gamepi with a 16 KB kernel. Bluetooth and shared
controller configuration are planned; no frontend modifications are included
in this initial repository setup.

```text
sources/es-de/     ES-DE source submodule
toolchain/        Docker-derived sysroot extraction, Clang toolchain, and probes
build/            Generated output (ignored)
```

## Get started

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

- Display directly through DRM/KMS, without X11 or Wayland.
- Deliver installed components through `.deb` packages.
- Prefer distro libraries and packages where suitable.
- Support both standalone emulators and libretro cores where useful.
- Reuse RetroArch-compatible controller profiles where practical, preserving
  input-driver identity when translating mappings.
- Keep Bluetooth pairing and persistent player assignment distinct from button
  mappings. Standalone emulator adapters will be added after the frontend work.
- Keep upstream modifications as small, separate commits, with tested source
  revisions pinned by the superproject.

Emulator packaging compatibility and a public APT repository are later work.
