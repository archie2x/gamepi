#!/usr/bin/env python3
"""Package the controller pairing script and the power-button service."""
import hashlib
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
packages = root / "build/packages"
packages.mkdir(parents=True, exist_ok=True)
stage = root / "build/controllers-package"
if stage.exists():
    shutil.rmtree(stage)
shutil.copytree(root / "packaging/gamepi-controllers", stage,
                ignore=shutil.ignore_patterns("README.md"))
source = root / "runtime/controllers"
for name in ("gamepi-controller-pair", "gamepi-power-button"):
    target = stage / "usr/bin" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source / name, target)
    target.chmod(0o755)
unit = stage / "usr/lib/systemd/system/gamepi-power-button.service"
unit.parent.mkdir(parents=True)
shutil.copyfile(source / unit.name, unit)
for script in ("postinst", "prerm"):
    (stage / "DEBIAN" / script).chmod(0o755)
(stage / "DEBIAN/md5sums").write_text("".join(
    hashlib.md5(p.read_bytes()).hexdigest() + "  " + str(p.relative_to(stage)) + "\n"
    for p in sorted(stage.rglob("*")) if p.is_file() and "DEBIAN" not in p.relative_to(stage).parts))
subprocess.run(["dpkg-deb", "--root-owner-group", "--build", str(stage),
                str(packages / "gamepi-controllers_0.1.0_all.deb")], check=True)
