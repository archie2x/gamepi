#!/usr/bin/env python3
"""Package the native-cross-built Waynergy receiver and SSH integration."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
packages = root / "build/packages"
packages.mkdir(parents=True, exist_ok=True)
binary = root / "build/waynergy/waynergy"
subprocess.run([sys.executable, str(root / "scripts/build-waynergy.py")], check=True)
stage = root / "build/remote-input-package"
if stage.exists():
    shutil.rmtree(stage)
shutil.copytree(root / "packaging/gamepi-remote-input", stage,
                ignore=shutil.ignore_patterns("README.md"))
target = stage / "usr/lib/gamepi-remote-input/waynergy"
target.parent.mkdir(parents=True)
shutil.copyfile(binary, target)
target.chmod(0o755)
(stage / "usr/bin/gamepi-remote-input").chmod(0o755)
(stage / "DEBIAN/postinst").chmod(0o755)
config = stage / "etc/gamepi/remote-input/config.ini"
config.parent.mkdir(parents=True)
shutil.copyfile(root / "runtime/input/waynergy.ini", config)
docs = stage / "usr/share/doc/gamepi-remote-input"
docs.mkdir(parents=True)
shutil.copyfile(root / "sources/waynergy/LICENSE", docs / "copyright")
(stage / "DEBIAN/conffiles").write_text("".join(
    "/" + str(p.relative_to(stage)) + "\n" for p in sorted((stage / "etc").rglob("*")) if p.is_file()))
(stage / "DEBIAN/md5sums").write_text("".join(
    hashlib.md5(p.read_bytes()).hexdigest() + "  " + str(p.relative_to(stage)) + "\n"
    for p in sorted(stage.rglob("*")) if p.is_file() and "DEBIAN" not in p.relative_to(stage).parts))
subprocess.run(["dpkg-deb", "--root-owner-group", "--build", str(stage),
                str(packages / "gamepi-remote-input_0.1.0_arm64.deb")], check=True)
