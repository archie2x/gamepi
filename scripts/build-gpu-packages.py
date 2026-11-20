#!/usr/bin/env python3
"""Repackage a checksum-pinned Pi kernel using native macOS dpkg-deb."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def build(artifact):
    manifest = json.loads((ROOT / "packaging/gamepi-kernel-rpi5/kernel.json").read_text())
    if hashlib.sha256(artifact.read_bytes()).hexdigest() != manifest["artifact_sha256"]:
        raise SystemExit("Kernel artifact SHA256 does not match kernel.json")
    stages = ROOT / "build/gpu-packages"
    if stages.exists():
        shutil.rmtree(stages)
    kernel = stages / "gamepi-kernel-rpi5"
    payload = kernel / "usr/lib/gamepi-kernel-rpi5"
    with zipfile.ZipFile(artifact) as archive:
        with archive.open("bcm2712_build.tar") as stream, tarfile.open(fileobj=stream, mode="r|") as tar:
            for member in tar:
                path = PurePosixPath(member.name)
                if path.is_absolute() or ".." in path.parts:
                    raise SystemExit("Unsafe kernel archive path: " + member.name)
                parts = path.parts
                if not parts:
                    continue
                if parts[0] == "boot":
                    target = payload / Path(*parts)
                elif parts[:2] == ("lib", "modules") and len(parts) >= 3:
                    if parts[2] != manifest["release"]:
                        raise SystemExit("Unexpected module release: " + member.name)
                    target = kernel / "usr" / Path(*parts)
                else:
                    continue
                # The CI build-directory link is not usable on the appliance.
                if member.issym() and path.name == "build":
                    continue
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with tar.extractfile(member) as src, target.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
                    target.chmod(0o644)
                else:
                    raise SystemExit("Unexpected archive entry: " + member.name)
    for name in ("kernel_2712.img", "bcm2712-rpi-5-b.dtb", "overlays/README", "overlays/vc4-kms-v3d.dtbo"):
        if not (payload / "boot" / name).is_file():
            raise SystemExit("Required boot file missing: " + name)
    manifest["boot_sha256"] = {
        str(p.relative_to(payload / "boot")): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((payload / "boot").rglob("*")) if p.is_file()
    }
    (payload / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for package in ("gamepi-kernel-rpi5", "gamepi-amdgpu"):
        stage = stages / package
        source = ROOT / "packaging" / package
        shutil.copytree(source / "DEBIAN", stage / "DEBIAN", dirs_exist_ok=True)
        if (source / "usr").exists():
            shutil.copytree(source / "usr", stage / "usr", dirs_exist_ok=True)
        for file in (stage / "DEBIAN").iterdir():
            text = file.read_text().replace("@KERNEL_VERSION@", manifest["version"])
            text = text.replace("@KERNEL_RELEASE@", manifest["release"])
            file.write_text(text)
            file.chmod(0o755 if file.name in ("postinst", "prerm", "postrm", "preinst") else 0o644)
        if package == "gamepi-amdgpu":
            (stage / "usr/lib/gamepi-amdgpu/boot-config").chmod(0o755)
        docs = stage / "usr/share/doc" / package
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "copyright").write_text(
            "Kernel: Linux contributors; GPL-2.0-only with Linux syscall exception.\n"
            "Corresponding source revision: " + manifest["source_url"] + "\n"
            "Kernel COPYING and individual source files describe applicable terms.\n"
            "Gamepi integration: see https://github.com/archie2x/gamepi\n")
        files = sorted(p for p in stage.rglob("*") if p.is_file() and "DEBIAN" not in p.relative_to(stage).parts)
        (stage / "DEBIAN/md5sums").write_text("".join(
            hashlib.md5(p.read_bytes()).hexdigest() + "  " + str(p.relative_to(stage)) + "\n" for p in files))
        control = stage / "DEBIAN/control"
        control.write_text(control.read_text() + "Installed-Size: " + str((sum(p.stat().st_size for p in files) + 1023) // 1024) + "\n")
        version = manifest["version"] if package == "gamepi-kernel-rpi5" else "0.1.0"
        arch = "arm64" if package == "gamepi-kernel-rpi5" else "all"
        output = ROOT / "build/packages" / (package + "_" + version + "_" + arch + ".deb")
        output.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["dpkg-deb", "--root-owner-group", "--build", str(stage), str(output)], check=True)
        print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path,
                        default=ROOT / "build/downloads/gamepi-linux-eef16e98-bcm2712.zip")
    build(parser.parse_args().artifact)
