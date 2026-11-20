# Gamepi development

Read README.md and toolchain/README.md before changing build or integration code.

- The host build tools are native Homebrew tools on macOS. Docker images supply
  sysroot files only; do not move compilation into a container or VM.
- `~/src` is already a case-sensitive filesystem. Do not create or mount another
  filesystem for this project.
- Target Linux ARM64. The accepted runtime is one shared Cage session containing
  the stock ES-DE AppImage and the applications it launches. Do not nest Cage or
  return to direct-KMS handoff without an explicit design change.
- Prefer integration of distro packages and stock ARM64 AppImages. Use RetroArch
  cores where useful and standalone emulators where they work better. Custom
  builds and a public APT repository are deferred until a demonstrated need.
- The immediate milestone is Flycast through RetroArch, followed by controller
  support for the working Dolphin and ARMSX2 emulators. Check whether their
  libretro cores track current upstream; otherwise translate shared controller
  profiles into standalone configurations. N64 debugging is deferred.
  Record changes and observed results in docs/runtime.md and docs/notes.md.
- Preserve existing configurations, saves, ROMs, boot files, and the working
  kernel. A fresh OS install and a separate library drive are proposals, not
  authorization to erase or repartition the current drive.
- `sources/es-de` is an independently versioned submodule. Keep frontend changes
  in that repository as focused commits, and update the superproject pointer
  deliberately. Preserve upstream license notices.
- The existing cross-build probes are configured and built from this directory
  with `cmake --preset probes` and `cmake --build --preset probes`.
- The extracted sysroot, build output, and image caches must remain untracked.
