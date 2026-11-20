#!/usr/bin/env python3
"""Export target development files with local Docker; never start the container."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parent
lock_path = root / "sysroot-image.json"
if len(sys.argv) > 1:
    image = sys.argv[1]
elif lock_path.exists():
    image = json.loads(lock_path.read_text())["pinned"]
else:
    image = "ghcr.io/archie2x/raspios-build-box:trixie-arm64"
sysroot = root / "sysroot"
work = root / "work"
work.mkdir(exist_ok=True)
if sysroot.exists():
    sys.exit(f"{sysroot} already exists; refusing to merge different sysroots")

subprocess.run(["docker", "pull", "--platform", "linux/arm64", image], check=True)
config = json.loads(subprocess.check_output(["docker", "image", "inspect", image], text=True))[0]
if config.get("Architecture") != "arm64" or config.get("Os") != "linux":
    sys.exit("The image is not Linux ARM64")
pinned = image if "@sha256:" in image else config["RepoDigests"][0]
print(f"Extracting {pinned}\nImage created: {config.get('Created')}", flush=True)
# Docker exports the merged filesystem from a stopped container. bsdtar
# extracts SDK directories and metadata; compilation uses native macOS tools.
paths = [
    "usr/include", "usr/lib/aarch64-linux-gnu", "usr/lib/gcc/aarch64-linux-gnu",
    "usr/lib/ld-linux-aarch64.so.1", "usr/lib/linux",
    "usr/share/pkgconfig", "usr/share/cmake", "etc/os-release", "var/lib/dpkg/status",
]
with tempfile.TemporaryDirectory(prefix="sysroot-", dir=work) as temporary:
    stage = Path(temporary) / "root"
    stage.mkdir()
    container = subprocess.check_output([
        "docker", "create", "--platform", "linux/arm64",
        "--label", "org.gamepi.purpose=sysroot", pinned,
    ], text=True).strip()
    export = subprocess.Popen(["docker", "export", container], stdout=subprocess.PIPE)
    command = ["bsdtar", "-xf", "-", "-C", str(stage), "--no-same-owner"]
    for path in paths:
        for prefix in ("", "./"):
            command += ["--include", prefix + path, "--include", prefix + path + "/*"]
    try:
        result = subprocess.run(command, stdin=export.stdout)
    finally:
        export.stdout.close()
        code = export.wait()
        subprocess.run(["docker", "rm", container], check=True, stdout=subprocess.DEVNULL)
    if code or result.returncode:
        sys.exit(f"Image extraction failed: docker={code}, bsdtar={result.returncode}")
    # Absolute Linux symlinks must resolve inside this directory on macOS.
    for directory, dirs, names in os.walk(stage, followlinks=False):
        for name in dirs + names:
            path = Path(directory) / name
            if path.is_symlink() and os.readlink(path).startswith("/"):
                target = stage / os.readlink(path).lstrip("/")
                path.unlink()
                path.symlink_to(os.path.relpath(target, path.parent))
    (stage / "lib").symlink_to("usr/lib")
    if not (stage / "usr/include/stdio.h").is_file():
        sys.exit("Image does not contain libc development headers")
    if not (stage / "usr/include/SDL2/SDL.h").is_file():
        sys.exit("Image does not contain SDL2 development headers")
    if not (stage / "usr/include/aarch64-linux-gnu/asm/types.h").is_file():
        sys.exit("Image is missing the ARM64 kernel userspace headers")
    stage.rename(sysroot)

lock = {"image": image, "pinned": pinned, "created": config.get("Created"),
        "architecture": config["Architecture"], "os": config["Os"]}
lock_path.write_text(json.dumps(lock, indent=2) + "\n")
print(f"Sysroot ready: {sysroot}", flush=True)
