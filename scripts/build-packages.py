#!/usr/bin/env python3
"""Build the complete local package set using native host tools."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
kernel = json.loads((root / "packaging/gamepi-kernel-rpi5/kernel.json").read_text())
archive = root / "build/downloads/gamepi-linux-eef16e98-bcm2712.zip"
if not archive.exists():
    archive.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["curl", "-L", "--fail", "--output", str(archive), kernel["artifact_url"]], check=True)
for script in ("build-gpu-packages.py", "build-apps-package.py", "build-kiosk-package.py",
               "build-remote-input-package.py", "build-controllers-package.py"):
    subprocess.run([sys.executable, str(root / "scripts" / script)], check=True)
stage = root / "build/meta-package"
if stage.exists():
    shutil.rmtree(stage)
shutil.copytree(root / "packaging/gamepi/DEBIAN", stage / "DEBIAN")
packages = root / "build/packages"
subprocess.run(["dpkg-deb", "--root-owner-group", "--build", str(stage),
                str(packages / "gamepi_0.1.0_all.deb")], check=True)
current = packages / "current"
if current.exists():
    shutil.rmtree(current)
current.mkdir()
for name in (f"gamepi-kernel-rpi5_{kernel['version']}_arm64.deb",
             "gamepi-amdgpu_0.1.0_all.deb", "gamepi-apps_0.1.0_arm64.deb",
             "gamepi-kiosk_0.2.0_all.deb", "gamepi-remote-input_0.1.0_arm64.deb",
             "gamepi-controllers_0.1.0_all.deb", "gamepi_0.1.0_all.deb"):
    (current / name).symlink_to("../" + name)
print("Installable package set:", current)
