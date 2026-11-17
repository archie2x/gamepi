# Gamepi development

Read README.md and toolchain/README.md before changing build or integration code.

- The host build tools are native Homebrew tools on macOS. Docker images supply
  sysroot files only; do not move compilation into a container or VM.
- `~/src` is already a case-sensitive filesystem. Do not create or mount another
  filesystem for this project.
- Target Linux ARM64 and direct DRM/KMS. X11 and Wayland are outside the product
  requirements.
- Installed software is delivered as Debian packages; prefer distro libraries
  before introducing custom builds.
- The immediate product milestone is ES-DE Bluetooth and shared controller
  configuration. Defer broad emulator packaging and coexistence work.
- `sources/es-de` is an independently versioned submodule. Keep frontend changes
  in that repository as focused commits, and update the superproject pointer
  deliberately. Preserve upstream license notices.
- The existing cross-build probes are configured and built from this directory
  with `cmake --preset probes` and `cmake --build --preset probes`.
- The extracted sysroot, build output, and image caches must remain untracked.
