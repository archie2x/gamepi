#!/usr/bin/env python3
"""Assemble the Gamepi integration package using native dpkg-deb."""
from pathlib import Path
import hashlib
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
source = root / 'packaging/gamepi-kiosk'
stage = root / 'build/kiosk-package'
stage.mkdir(parents=True, exist_ok=True)
for name in ('DEBIAN', 'etc', 'usr'):
    shutil.copytree(source / name, stage / name, dirs_exist_ok=True)
files = sorted(p for name in ('etc', 'usr') for p in (stage / name).rglob('*') if p.is_file())
(stage / 'DEBIAN/md5sums').write_text(''.join(
    hashlib.md5(p.read_bytes()).hexdigest() + '  ' + str(p.relative_to(stage)) + '\n'
    for p in files
))
output = root / 'build/packages/gamepi-kiosk_0.1.0_all.deb'
output.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(['dpkg-deb', '--root-owner-group', '--build', str(stage), str(output)], check=True)
