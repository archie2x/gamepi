"""Exercise preservation and rollback of Raspberry Pi boot configuration."""
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest

MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1] /
    "packaging/gamepi-amdgpu/usr/lib/gamepi-amdgpu/boot-config"))
REVISION = "eef16e98c3d22e8624a83a6aee3266dd1d70435b"


class BootConfiguration(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.boot = self.root / "boot/firmware"
        self.boot.mkdir(parents=True)
        self.original = "# stock settings\nauto_initramfs=1\n[pi5]\ndtoverlay=nospi10\n[all]\n"
        self.command = "console=tty1 root=PARTUUID=card-specific-02 rootfstype=ext4 rootwait ds=nocloud;i=imager\n"
        (self.boot / "config.txt").write_text(self.original)
        (self.boot / "cmdline.txt").write_text(self.command)
        (self.boot / "kernel_2712.img").write_bytes(b"stock kernel")
        payload = self.root / "usr/lib/gamepi-kernel-rpi5"
        source = payload / "boot"
        (source / "overlays").mkdir(parents=True)
        self.files = {"kernel_2712.img": b"custom kernel",
                      "bcm2712-rpi-5-b.dtb": b"matching dtb",
                      "overlays/README": b"matching overlays"}
        for name, data in self.files.items():
            (source / name).write_bytes(data)
        (payload / "manifest.json").write_text(json.dumps({
            "revision": REVISION, "release": "6.18.48-v8-16k+",
            "boot_sha256": {name: hashlib.sha256(data).hexdigest()
                            for name, data in self.files.items()}}))

    def configure(self):
        MODULE["configure"](self.root, check_host=False)

    def test_install_repeat_remove_preserves_stock_and_partition_identity(self):
        other = self.boot / "gamepi/unrelated.txt"
        other.parent.mkdir()
        other.write_text("keep")
        self.configure()
        first = (self.boot / "config.txt").read_text()
        self.configure()
        self.assertEqual(first, (self.boot / "config.txt").read_text())
        self.assertEqual(self.command, (self.boot / "cmdline.txt").read_text())
        self.assertEqual(b"stock kernel", (self.boot / "kernel_2712.img").read_bytes())
        active = self.boot / "gamepi/amdgpu" / REVISION
        self.assertIn(self.command.strip(), (active / "cmdline.txt").read_text())
        self.assertIn("amdgpu.pcie_gen_cap=0x70007", (active / "cmdline.txt").read_text())
        self.assertEqual(self.files["bcm2712-rpi-5-b.dtb"], (active / "bcm2712-rpi-5-b.dtb").read_bytes())
        MODULE["remove"](self.root)
        MODULE["remove"](self.root)
        self.assertEqual(self.original, (self.boot / "config.txt").read_text())
        self.assertEqual("keep", other.read_text())
        self.assertFalse(active.exists())

    def test_bad_payload_does_not_activate(self):
        (self.root / "usr/lib/gamepi-kernel-rpi5/boot/kernel_2712.img").write_bytes(b"damaged")
        with self.assertRaisesRegex(ValueError, "checksum"):
            self.configure()
        self.assertEqual(self.original, (self.boot / "config.txt").read_text())

    def test_existing_boot_selection_is_preserved(self):
        text = self.original + "os_prefix=another-system/\n"
        (self.boot / "config.txt").write_text(text)
        with self.assertRaisesRegex(ValueError, "existing os_prefix"):
            self.configure()
        self.assertEqual(text, (self.boot / "config.txt").read_text())

    def test_unsupported_root_is_not_activated(self):
        (self.boot / "cmdline.txt").write_text("root=/dev/mapper/crypt rootfstype=btrfs\n")
        with self.assertRaisesRegex(ValueError, "plain ext4"):
            self.configure()
        self.assertEqual(self.original, (self.boot / "config.txt").read_text())

    def test_unbalanced_managed_block_is_not_modified(self):
        text = self.original + MODULE["BEGIN"]
        (self.boot / "config.txt").write_text(text)
        with self.assertRaisesRegex(ValueError, "Unbalanced"):
            self.configure()
        self.assertEqual(text, (self.boot / "config.txt").read_text())


if __name__ == "__main__":
    unittest.main()
