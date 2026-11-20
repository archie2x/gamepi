#!/usr/bin/env python3
"""Build the native macOS protocol generator and Linux ARM64 input receiver."""

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "build/host-tools"
WAYLAND = ROOT / "sources/wayland-scanner/src"
BUILD = ROOT / "build/waynergy"


def run(*args):
    subprocess.run([str(arg) for arg in args], check=True)


def main():
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
