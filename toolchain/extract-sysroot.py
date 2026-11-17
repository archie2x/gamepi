#!/usr/bin/env python3
"""Extract target development files from a Docker image; never run the image."""
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

def crane(*args):
    return subprocess.check_output(["crane", *args, "--platform", "linux/arm64"], text=True).strip()

pinned = crane("digest", "--full-ref", image)
config = json.loads(crane("config", pinned))
if config.get("architecture") != "arm64" or config.get("os") != "linux":
    sys.exit("The image is not Linux ARM64")
print(f"Extracting {pinned}\nImage created: {config.get('created')}", flush=True)
# crane merges Docker layers and whiteouts. bsdtar extracts target SDK
# directories and metadata. All compilation uses native macOS tools.
paths = [
    "usr/include", "usr/lib/aarch64-linux-gnu", "usr/lib/gcc/aarch64-linux-gnu",
    "usr/lib/ld-linux-aarch64.so.1", "usr/lib/linux",
    "usr/share/pkgconfig", "usr/share/cmake", "etc/os-release", "var/lib/dpkg/status",
]
with tempfile.TemporaryDirectory(prefix="sysroot-", dir=work) as temporary:
    stage = Path(temporary) / "root"
    stage.mkdir()
    export = subprocess.Popen(["crane", "export", "--platform", "linux/arm64", pinned, "-"],
                              stdout=subprocess.PIPE)
    command = ["bsdtar", "-xf", "-", "-C", str(stage), "--no-same-owner"]
    for path in paths:
        for prefix in ("", "./"):
            command += ["--include", prefix + path, "--include", prefix + path + "/*"]
    try:
        result = subprocess.run(command, stdin=export.stdout)
    finally:
        export.stdout.close()
    code = export.wait()
    if code or result.returncode:
        sys.exit(f"Image extraction failed: crane={code}, bsdtar={result.returncode}")
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

lock = {"image": image, "pinned": pinned, "created": config.get("created"),
        "architecture": config["architecture"], "os": config["os"]}
lock_path.write_text(json.dumps(lock, indent=2) + "\n")
print(f"Sysroot ready: {sysroot}", flush=True)
