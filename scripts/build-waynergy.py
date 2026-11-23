#!/usr/bin/env python3
"""Build the native macOS protocol generator and Linux ARM64 input receiver."""

from pathlib import Path
import hashlib
import subprocess
import tarfile


ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "build/host-tools"
WAYLAND = ROOT / "sources/wayland-scanner/src"
BUILD = ROOT / "build/waynergy"


def run(*args):
    subprocess.run([str(arg) for arg in args], check=True)


def main():
    cache = ROOT / "build/downloads"
    cache.mkdir(parents=True, exist_ok=True)
    inputs = (
        ("waynergy-v0.0.17.tar.gz", "https://github.com/r-c-f/waynergy/archive/refs/tags/v0.0.17.tar.gz",
         "b8b2d12588cabfe161ce21a5cd898f06bdfd55c0106ecd4a26c8628aafeff990", ROOT / "sources/waynergy"),
        ("wayland-1.26.0.tar.xz", "https://gitlab.freedesktop.org/wayland/wayland/-/releases/1.26.0/downloads/wayland-1.26.0.tar.xz",
         "64176eaa46e4969903e286f8e5ef8331affc17fdf03ac9b58381d2b23162b7a3", ROOT / "sources/wayland-scanner"),
        ("libtls-dev_3.8.1-2.1+b2_arm64.deb", "https://deb.debian.org/debian/pool/main/libr/libretls/libtls-dev_3.8.1-2.1+b2_arm64.deb",
         "ff14a87442a7960a51777170dbf1b54741a0f41d0f948f8dc2e8e64d7a37a502", None),
        ("libtls28t64_3.8.1-2.1+b2_arm64.deb", "https://deb.debian.org/debian/pool/main/libr/libretls/libtls28t64_3.8.1-2.1+b2_arm64.deb",
         "e0f0db87d97f154f6b6fff0f391071cb5901482d73f8d1e082611f92cc174bf8", None),
    )
    sysroot = ROOT / "toolchain/sysroot"
    if not (sysroot / "usr/include/stdio.h").exists():
        raise SystemExit("Extract the toolchain sysroot first")
    for filename, url, sha, destination in inputs:
        archive = cache / filename
        if not archive.exists():
            run("curl", "-L", "--fail", "--output", archive, url)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != sha:
            raise SystemExit("Input checksum mismatch: " + filename)
        if destination is None:
            run("dpkg-deb", "--extract", archive, sysroot)
        else:
            with tarfile.open(archive) as tar:
                for member in tar.getmembers():
                    parts = Path(member.name).parts[1:]
                    if not parts or not member.isfile():
                        continue
                    target = destination.joinpath(*parts)
                    content = tar.extractfile(member).read()
                    if target.exists() and target.read_bytes() != content:
                        raise SystemExit("Source differs from pinned archive: " + str(target))
                    if not target.exists():
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(content)
    HOST.mkdir(parents=True, exist_ok=True)
    version = (WAYLAND / "wayland-version.h.in").read_text()
    for key, value in {
        "WAYLAND_VERSION_MAJOR": "1",
        "WAYLAND_VERSION_MINOR": "26",
        "WAYLAND_VERSION_MICRO": "0",
        "WAYLAND_VERSION": "1.26.0",
    }.items():
        version = version.replace(f"@{key}@", value)
    (HOST / "wayland-version.h").write_text(version)
    run(
        "/opt/homebrew/opt/llvm/bin/clang", "-O2", "-DHAVE_STRNDUP=1",
        "-DHAVE_LIBXML=0", f"-I{HOST}", f"-I{WAYLAND}",
        WAYLAND / "scanner.c", WAYLAND / "wayland-util.c", "-lexpat",
        "-o", HOST / "wayland-scanner",
    )
    run(
        "cmake", "-S", ROOT / "toolchain/waynergy", "-B", BUILD, "-G", "Ninja",
        f"-DCMAKE_TOOLCHAIN_FILE={ROOT / 'toolchain/cmake/aarch64-linux-gnu.cmake'}",
        "-DCMAKE_BUILD_TYPE=Release",
    )
    run("cmake", "--build", BUILD)


if __name__ == "__main__":
    main()
