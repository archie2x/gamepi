# Native macOS to Raspberry Pi ARM64

This first setup builds two small Linux programs using native Homebrew Clang,
LLD, CMake, Ninja, and pkg-config. Docker supplies files only: no container or
VM runs during extraction or compilation.

The sysroot lives on the existing case-sensitive filesystem mounted at `~/src`.
Its source is `ghcr.io/archie2x/raspios-build-box:trixie-arm64`, built by the
existing `archie2x/raspi-docker` GitHub workflow. `sysroot-image.json` records
the exact ARM64 image digest used. The image's Linux compilers are not executed.

## Build

Dependencies on the Mac: `llvm`, `lld`, `cmake`, `ninja`, `pkgconf`, `crane`,
and Python 3. The Homebrew paths in the toolchain file target Apple Silicon.

From this directory:

```sh
python3 extract-sysroot.py
cmake -S . -B build -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE=cmake/aarch64-linux-gnu.cmake \
  -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

Extraction uses the pinned digest from `sysroot-image.json` by default.
To select a different image, pass its tag or digest to `extract-sysroot.py`.
The script refuses to merge an image into an existing sysroot. For a refresh,
keep the old sysroot separately before extracting the replacement and use a
fresh CMake build directory.

`build/hello` checks C++, libc, the target architecture, and runtime page size.
`build/sdl-probe` checks the image's stock SDL2 headers against the Pi's runtime,
lists compiled video backends, and initializes controller support. It does not
open a window, change the display, or play audio.

## What is handled

- Clang targets `aarch64-linux-gnu`; its macOS SDK default config is disabled.
- Headers, Debian's libstdc++/libgcc, startup objects, and shared libraries come
  from the image. No target library is taken from Homebrew.
- Native pkg-config reads only sysroot metadata and rebases its include/library
  paths. Native CMake tools remain executable on macOS.
- Absolute Linux symlinks are made relative inside the extracted sysroot.
- ELF segment alignment supports 4K, 16K, and 64K Linux kernels.

This is a development sysroot, not a bootable Pi root filesystem. It currently
contains SDL2 from the image. Add distro SDL3 development packages to the image
when a target needs SDL3; build a separate SDL only for a demonstrated missing
version, backend, or fix. The probes do not establish emulator compatibility or
fullscreen KMS handoff.

## Verified on gamepi, 2026-11-17

The image refresh completed successfully in
<https://github.com/archie2x/raspi-docker/actions/runs/44160739302>.
Both executables were built by native Homebrew Clang 22.1.4 and LLD 22.1.4,
copied to `/var/tmp/gamepi-cross-probe-20261117/`, and executed on the Pi:

```text
Built on macOS with native Clang; running on Linux aarch64
Page size: 16384
C++ library check: 10
SDL headers: 2.32.4
SDL runtime: 2.32.4
Video backends: x11 wayland KMSDRM offscreen dummy evdev
Controller initialization succeeded; joysticks: 0
```

The binaries have no embedded build-directory RPATH. On gamepi, they load the
system's SDL2, libstdc++, libgcc, and libc. ELF LOAD segments have 64K alignment.
