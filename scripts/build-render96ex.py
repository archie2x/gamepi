#!/usr/bin/env python3
"""Cross-build the pinned Render96ex (SM64 PC port) for Linux ARM64.

The build needs the user's own US ROM for asset extraction. Asset tools run
natively on macOS; game code is compiled by Homebrew Clang against the sysroot.
"""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "sources/render96ex"
SYSROOT = ROOT / "toolchain/sysroot"
BUILD = ROOT / "build/render96ex"
WRAPPERS = BUILD / "cross-bin"
REPOSITORY = "https://github.com/Render96/Render96ex.git"
# Branch "tester": the DynOS-enabled release line. "master" lacks DynOS.
REVISION = "61480c4e6e5c7e7bed40341c0aa76b75d405c3c7"
ROM_SHA1 = "9bef1128717f958171a4afac3ed78ee2bb4e86ce"
# luigi-cap: Clang rejects integer literals wider than 64 bits; GCC truncates
# them with a warning. The patch writes the 16-bit values that GCC produces.
# sorted-language: language 0, the default, was the first file readdir returned
# (French on the Pi's ext4). Sorting makes it AM_us, English.
# precache-loading-screen: a progress bar while textures are precached; without
# it the window shows nothing and the frontend stays visible during loading.
# mupen-style-controls: right trigger shifts the face buttons to C buttons and
# Capture pressed twice exits, as in the RetroArch N64 setup.
PATCHES = [ROOT / "patches/render96ex" / name for name in
           ("luigi-cap-texcoord-literals.patch", "sorted-language-files.patch",
            "mupen-style-controls.patch", "precache-loading-screen.patch")]
LLVM = Path("/opt/homebrew/opt/llvm/bin")
PREFIX = "aarch64-linux-gnu-"

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--rom", type=Path, help="Super Mario 64 (USA) .z64; needed once, for asset extraction")
parser.add_argument("--jobs", type=int, default=6)
args = parser.parse_args()
if args.jobs < 1:
    parser.error("--jobs must be positive")


def run(*command, **kwargs):
    print("Running:", " ".join(map(str, command)), flush=True)
    return subprocess.run([str(part) for part in command], check=True, **kwargs)


def sha1(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha1").hexdigest()


def wrapper(name, body):
    path = WRAPPERS / name
    path.write_text("#!/bin/sh\n" + body + "\n")
    path.chmod(0o755)


if not (SYSROOT / "usr/include/SDL2/SDL.h").exists():
    parser.error("Extract the pinned toolchain sysroot first")
GMAKE = shutil.which("gmake")
if not GMAKE:
    parser.error("GNU Make 4 is required: brew install make")

if not (SOURCE / ".git").exists():
    run("git", "init", "--quiet", SOURCE)
    run("git", "-C", SOURCE, "remote", "add", "origin", REPOSITORY)
if subprocess.run(["git", "-C", str(SOURCE), "cat-file", "-e", REVISION],
                  capture_output=True).returncode:
    run("git", "-C", SOURCE, "fetch", "--depth", "1", REPOSITORY, REVISION)
head = subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"], text=True).strip()
if head != REVISION:
    run("git", "-C", SOURCE, "checkout", "--detach", REVISION)

for patch in PATCHES:
    if subprocess.run(["git", "apply", "--reverse", "--check", str(patch)],
                      cwd=SOURCE, capture_output=True).returncode:
        run("git", "apply", patch, cwd=SOURCE)

baserom = SOURCE / "baserom.us.z64"
if not baserom.exists():
    if not args.rom:
        parser.error("Pass --rom on the first build")
    if sha1(args.rom) != ROM_SHA1:
        parser.error("The ROM is not the expected US release (SHA-1 mismatch)")
    shutil.copyfile(args.rom, baserom)
if sha1(baserom) != ROM_SHA1:
    raise SystemExit("baserom.us.z64 does not match the expected US release")

# GCC-named front ends for the upstream Makefile's CROSS prefix. They are
# generated, as they embed this checkout's absolute sysroot path.
WRAPPERS.mkdir(parents=True, exist_ok=True)
target = (f"--no-default-config --target=aarch64-linux-gnu --sysroot={SYSROOT} "
          f"--gcc-toolchain={SYSROOT}/usr -Wno-unused-command-line-argument")
link = "--ld-path=/opt/homebrew/bin/ld.lld -Wl,-z,max-page-size=65536"
# The source predates GCC 14 and Clang 16, which made these C diagnostics errors.
lenient = " ".join("-Wno-error=" + name for name in (
    "incompatible-pointer-types", "incompatible-function-pointer-types",
    "int-conversion", "implicit-function-declaration", "implicit-int"))
wrapper(PREFIX + "gcc", f'exec {LLVM}/clang {target} {link} {lenient} "$@"')
wrapper(PREFIX + "g++", f'exec {LLVM}/clang++ {target} {link} "$@"')
# Inputs include .h.in files, which Clang would otherwise pass to the linker.
wrapper(PREFIX + "cpp", f'exec {LLVM}/clang {target} -E -x c "$@"')
# GNU as command line -> Clang's integrated assembler.
wrapper(PREFIX + "as", f'''set --  "$@" --end--
while [ "$1" != --end-- ]; do
  case "$1" in
    --defsym) set -- "$@" "-Wa,--defsym,$2"; shift ;;
    -MD) set -- "$@" -MD -MF "$2"; shift ;;
    *) set -- "$@" "$1" ;;
  esac
  shift
done
shift
exec {LLVM}/clang {target} -c -x assembler "$@"''')
wrapper(PREFIX + "objcopy", f'exec {LLVM}/llvm-objcopy "$@"')
wrapper(PREFIX + "objdump", f'exec {LLVM}/llvm-objdump "$@"')
wrapper("sdl2-config", f'''export PKG_CONFIG_PATH= PKG_CONFIG_SYSROOT_DIR={SYSROOT}
export PKG_CONFIG_LIBDIR={SYSROOT}/usr/lib/aarch64-linux-gnu/pkgconfig:{SYSROOT}/usr/share/pkgconfig
exec pkg-config sdl2 "$@"''')
# Upstream scripts call "make"; macOS ships 3.81, which lacks the != operator.
make = WRAPPERS / "make"
make.unlink(missing_ok=True)
make.symlink_to(GMAKE)
# The tools request _XOPEN_SOURCE 500, under which macOS hides vsnprintf.
wrapper("host-cc", 'exec cc -D_DARWIN_C_SOURCE "$@"')

environment = dict(os.environ, PATH=f"{WRAPPERS}:{os.environ['PATH']}")
for name in ("CC", "CXX", "CPP", "CFLAGS", "CXXFLAGS", "LDFLAGS", "MAKEFLAGS"):
    environment.pop(name, None)

# Upstream forwards the game's CC/CXX to the asset tools. Build those first
# with the Mac's compiler so that the later nested invocation finds them current.
# Serial: tabledesign lacks a dependency on the audiofile library it links.
run("make", "-C", SOURCE / "tools", "CC=host-cc", "CXX=c++", env=environment)
run("./extract_assets.py", "us", cwd=SOURCE, env=environment)

# HOST_OS=Linux: skip the Makefile's macOS-target branch. TARGET_RPI stays 0:
# that option selects GLES2 for the Pi's own GPU and derives -march from the
# build machine; this build uses desktop OpenGL for the AMD card.
run("make", "-C", SOURCE, f"-j{args.jobs}", "HOST_OS=Linux", "NOEXTRACT=1",
    "TARGET_ARCH=armv8-a", f"CROSS={PREFIX}", f"CC={PREFIX}gcc", f"CXX={PREFIX}g++",
    env=environment)

output = SOURCE / "build/us_pc"
executable = output / "sm64.us.f3dex2e"
run(LLVM / "llvm-readelf", "-h", "-l", "-d", executable)
print("Built:", executable)
print("Runtime directory (executable, res/, dynos/):", output)
