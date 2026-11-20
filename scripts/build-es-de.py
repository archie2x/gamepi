#!/usr/bin/env python3
"""Build the Linux ARM64 ES-DE frontend with native macOS build tools."""
import argparse
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--jobs", type=int, default=4)
args = parser.parse_args()
if args.jobs < 1:
    parser.error("--jobs must be positive")

root = Path(__file__).resolve().parent.parent
if not (root / "toolchain/sysroot/usr/include/stdio.h").is_file():
    parser.error("Extract the pinned sysroot with python3 toolchain/extract-sysroot.py first")
build = root / "build/es-de"
subprocess.run([
    "cmake", "-S", str(root / "sources/es-de"), "-B", str(build), "-G", "Ninja",
    f"-DCMAKE_TOOLCHAIN_FILE={root / 'toolchain/cmake/aarch64-linux-gnu.cmake'}",
    "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_INSTALL_PREFIX=/usr",
    "-DDEINIT_ON_LAUNCH=ON", "-DAPPLICATION_UPDATER=OFF",
    "-DCOMPILE_LOCALIZATIONS=ON", "-DCMAKE_POLICY_VERSION_MINIMUM=3.5",
], check=True)
subprocess.run(["cmake", "--build", str(build), "--parallel", str(args.jobs)], check=True)
