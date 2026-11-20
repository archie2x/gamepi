# Raspberry Pi 5 AMD GPU packages

These packages target stock Raspberry Pi OS Lite 64-bit, Trixie, on a Pi 5
with a plain ext4 root filesystem. The RX 460 is the tested GPU. They do not
install the frontend, emulators, ROMs or display-specific settings.

- `gamepi-kernel-rpi5` contains the checksum-pinned prebuilt bcm2712 kernel,
  matching device trees/overlays and modules. `kernel.json` pins the source
  revision, binary artifact checksum, release and package version.
- `gamepi-amdgpu` depends on that kernel and distro AMD firmware/Mesa packages.
  Its maintainer scripts activate/remove the Gamepi boot selection.

## Build on macOS

Use native Homebrew `dpkg-deb` and Python 3; no VM/container runs the build.

```sh
mkdir -p build/downloads
curl -L --fail \
  -o build/downloads/gamepi-linux-eef16e98-bcm2712.zip \
  https://builds.raspberrypi.com/github/linux/eef16e98c3d22e8624a83a6aee3266dd1d70435b/bcm2712
python3 tests/test_gpu_boot_config.py
python3 scripts/build-gpu-packages.py
```

The upstream artifact is a ZIP containing `bcm2712_build.tar`. The builder
verifies its SHA256 before repackaging. An optional `--artifact PATH` selects
an archived copy; it must still match the pinned checksum. Outputs are:

```text
build/packages/gamepi-kernel-rpi5_6.18.48+eef16e98-1_arm64.deb
build/packages/gamepi-amdgpu_0.1.0_all.deb
```

The download, extraction, staging and binaries stay under ignored `build/`.
Preserve the artifact or built kernel package in a durable release archive:
GitHub build artifacts expire. The repository alone does not contain these
binaries, and no public APT/release archive has been published yet.

## Install on a fresh card

First complete stock OS updates. Copy both `.deb` files to the Pi, then run:

```sh
sudo apt install ./gamepi-kernel-rpi5_6.18.48+eef16e98-1_arm64.deb ./gamepi-amdgpu_0.1.0_all.deb
sudo reboot
```

The package installation scripts do not fetch artifacts or run `rpi-update`.
APT resolves the declared firmware/Mesa dependencies using the Pi's configured
repositories. The GPU package currently has no APT repository of its own.

## Boot ownership and removal

Canonical boot files are package-owned under `/usr/lib/gamepi-kernel-rpi5/boot`;
modules live under `/usr/lib/modules/6.18.48-v8-16k+`. Activation stages the
matching boot set under `/boot/firmware/gamepi/amdgpu/<revision>/` and adds one
marked include block to the stock `config.txt`. The generated include selects
that versioned directory with `os_prefix`, requests PCIe Gen 3, and disables
automatic initramfs loading for this tested direct-ext4-boot profile.

The versioned directory receives a generated `cmdline.txt` based on this
installation's stock file, retaining its root partition ID and other arguments
while setting `arm64.nodczva=1 amdgpu.pcie_gen_cap=0x70007`. Stock `cmdline.txt`,
kernel images, device trees and overlays are untouched. Existing explicit
`os_prefix` configurations require integration rather than silent replacement.
No EEPROM, CPU governor, display mode or emulator configuration is changed.

```sh
sudo apt remove gamepi-amdgpu
sudo reboot
```

Removal deletes the managed include and Gamepi's generated AMD boot directory;
the stock boot selection resumes on reboot. The kernel dependency can remain
installed without selecting it. Firmware/Mesa dependencies are not uninstalled
by the removal script. Reinstalling activation regenerates the same profile.

## Verify after reboot

```sh
uname -r
getconf PAGESIZE
cat /sys/bus/pci/devices/0001:01:00.0/current_link_speed
cat /sys/bus/pci/devices/0001:01:00.0/current_link_width
cat /sys/bus/pci/devices/0001:01:00.0/pp_dpm_pcie
readlink /sys/bus/pci/devices/0001:01:00.0/driver
```

Expected: `6.18.48-v8-16k+`, page size `16384`, driver `amdgpu`, and an active
8 GT/s x1 link under load. The stock OS kernel packages remain installed and
can continue updating their own boot files without overwriting this directory.

## Fresh-card result, 2026-11-20

Installed on the updated stock Trixie microSD using only these two local
packages and declared APT dependencies. Reinstall was idempotent. Removing
activation restored all recorded stock boot-file hashes; reinstallation
reactivated it. A real reinstall of the stock 6.18.60 Pi 5 kernel ran its
initramfs/raspi-firmware hooks without changing Gamepi's boot selection or
any of its 408 boot files.

After reboot, the kernel reported 6.18.48-v8-16k+ and page size 16384. Roger
confirmed console output on the RX 460. Distro `vulkan-tools` (installed only
for this check) enumerated RX 460 RADV, Mesa 26.2.7, Vulkan 1.4.354. The link
was at 2.5 GT/s idle with an 8 GT/s high state available. Loaded Gen 3 testing
on this card remains open; an optional forced-high-state check was blocked
by the card requiring a sudo password after reboot. No power policy changed.
