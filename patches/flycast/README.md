# Flycast runtime page size

Base: flyinghead/flycast `3a5267a5e32438026e1c5b97d5de6cd77236f72c`.

`0001-linux-runtime-page-size.patch` uses the existing runtime page-size design
for Linux builds. `PAGE_SIZE` is initialized with `sysconf(_SC_PAGESIZE)`;
`PAGE_MASK` follows that value. The compiler no longer receives the build
machine's page size from CMake. Allocation, protection, texture invalidation,
and dynarec page tracking therefore use the executing machine's granularity.

`MAX_PAGE_SIZE` is a compile-time structure-layout constraint, set to 64 KB on
Linux. It is independent of the runtime value. Android retains its 16 KB
layout limit. Windows and macOS handling are unchanged.

Build on the Mac with native Homebrew Clang/LLD:

```sh
python3 scripts/build-flycast.py
```

The existing toolchain supplies the Linux ARM64 sysroot and 64 KB ELF LOAD
alignment. `CMAKE_OSX_ARCHITECTURES` is cleared because Flycast sets it before
its `project()` call, when CMake still sees the macOS host.

The deployable core is `build/flycast-core/flycast_runtimepages_libretro.so`;
`page-symbols.json` supplies its internal symbol offsets for the regression
checker. Keep those two files together.

Run on Linux with the matching files:

```sh
python3 scripts/check-flycast-pages.py /path/to/flycast_runtimepages_libretro.so /path/to/page-symbols.json
```

The checker loads the actual core, verifies its detected page size, and calls
its lock/unlock/executable-protection functions on a 4 KB-offset memory region.
It checks writes and reads around those protection changes. No renderer or game
is required for this specific regression check.

Verified with the same binary on 4 KB Linux in a local Docker runtime and on
gamepi's 16 KB kernel. A 64 KB-kernel execution test has not been performed.
Core SHA256: `ba3ea793ddcd25e376f27bc763a99d284584a232117799c3b711008fab9ee6c8`.

Fork: <https://github.com/archie2x-upstream/flycast>, branch
`fix/linux-runtime-page-size`, commit `d97941bac1710d5d767de07d292f6138cd5103c9`.
Upstream PR: <https://github.com/flyinghead/flycast/pull/2616>, linked to
<https://github.com/flyinghead/flycast/issues/2615>.
