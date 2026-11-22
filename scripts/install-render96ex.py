#!/usr/bin/env python3
"""Stage the built Render96ex with its model and texture packs; install on the Pi.

Run scripts/build-render96ex.py first. Saves and settings on the Pi live in
~/.local/share/sm64ex and are not touched.
"""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "sources/render96ex/build/us_pc"
CACHE = ROOT / "build/downloads/render96ex"
PACKS = ROOT / "build/render96ex/packs"
STAGE = ROOT / "build/render96ex/stage"
RUNTIME = ROOT / "runtime/render96ex"
EXECUTABLE = "sm64.us.f3dex2e"
# Each archive holds one or more top-level directories whose contents go to the destination.
ARCHIVES = (
    ("models", "dynos/packs", False,
     "https://github.com/Render96/ModelPack/releases/download/3.25/Render96_DynOs_v3.25.7z",
     "22eea6dafcc0a87659d60513eb6a6b0f4ea0acbc6645a6b1b445de9e5812e6df"),
    ("textures", "res/gfx", True,
     "https://github.com/pokeheadroom/RENDER96-HD-TEXTURE-PACK/releases/download/1.3.26.7.7/"
     "Render96.HD.Texture.Pack.1.3.26.7.7.7z",
     "a9ea999c8a4a2bd68954b0f9eecee62db481ef31f6189cf362cc72c9edc4191c"),
)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--host", help="SSH destination; omit to stage only")
parser.add_argument("--expected-root", help="Root device the Pi must have booted from, e.g. /dev/sda2")
parser.add_argument("--ssh-option", action="append", default=[], metavar="KEY=VALUE")
args = parser.parse_args()
if args.host and not args.expected_root:
    parser.error("--host requires --expected-root")


def run(*command, **kwargs):
    print("Running:", " ".join(map(str, command)), flush=True)
    return subprocess.run([str(part) for part in command], check=True, **kwargs)


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


if not (OUTPUT / EXECUTABLE).exists():
    parser.error("Run scripts/build-render96ex.py first")
if not shutil.which("7zz"):
    parser.error("7-Zip is required: brew install sevenzip")
CACHE.mkdir(parents=True, exist_ok=True)
game = STAGE / "render96ex"
game.mkdir(parents=True, exist_ok=True)
run("rsync", "-a", OUTPUT / EXECUTABLE, OUTPUT / "res", OUTPUT / "dynos", game)
for name, destination, flatten, url, checksum in ARCHIVES:
    archive = CACHE / url.rsplit("/", 1)[1]
    if not archive.exists():
        partial = archive.with_suffix(".partial")
        run("curl", "-L", "--fail", "--retry", "2", "--output", partial, url)
        partial.replace(archive)
    if sha256(archive) != checksum:
        raise SystemExit("Checksum mismatch: " + archive.name)
    extracted = PACKS / name
    if not (extracted / ".complete").exists():
        shutil.rmtree(extracted, ignore_errors=True)
        extracted.mkdir(parents=True)
        run("7zz", "x", "-bso0", f"-o{extracted}", archive)
        (extracted / ".complete").touch()
    target = game / destination
    target.mkdir(parents=True, exist_ok=True)
    for directory in sorted(path for path in extracted.iterdir() if path.is_dir()):
        # Model packs keep their directory names; texture files overlay res/gfx.
        run("rsync", "-a", f"{directory}/" if flatten else directory, target)
print("Staged:", game)


def pack_option(name):
    """DynOS's configuration key for a model pack directory (data/dynos_opt.cpp)."""
    value = 5381
    for byte in name.encode():
        value = (value * 33 + byte) & 0xFFFFFFFF
    return f"dynos_pack_{value:08X}"


# Packs are off by default. This seeds a first-run DynOS configuration enabling them.
defaults = STAGE / "DynOS.1.1.alpha.config.txt"
defaults.write_text("".join(pack_option(path.name) + "=1\n"
                            for path in sorted((game / "dynos/packs").iterdir()) if path.is_dir()))

if args.host:
    ssh = ["ssh", "-o", "BatchMode=yes"]
    for option in args.ssh_option:
        ssh += ["-o", option]
    device = subprocess.check_output([*ssh, args.host, "findmnt -no SOURCE /"], text=True).strip()
    if device != args.expected_root:
        raise SystemExit(f"Root is {device}, expected {args.expected_root}")
    if subprocess.run([*ssh, args.host, f"pgrep -x {EXECUTABLE[:15]}"],
                      capture_output=True).returncode == 0:
        raise SystemExit("Render96ex is running on the Pi; exit it before updating")
    run(*ssh, args.host, "mkdir -p .local/share/gamepi .local/bin .local/share/sm64ex /srv/ROMs/ports")
    shell = " ".join(ssh)
    run("rsync", "-a", "--info=stats1", "-e", shell, game, f"{args.host}:.local/share/gamepi/")
    run("rsync", "-p", "-e", shell, RUNTIME / "gamepi-render96ex", f"{args.host}:.local/bin/")
    run("rsync", "-p", "-e", shell, RUNTIME / "Super Mario 64 (Render96).sh",
        f"{args.host}:/srv/ROMs/ports/")
    run("rsync", "--ignore-existing", "-e", shell, defaults, f"{args.host}:.local/share/sm64ex/")
    # Replace only the settings listed in controls.txt; the game rewrites the
    # whole file on exit, which is why it must not be running here.
    merge = ("import pathlib,sys; new=dict(l.split(' ',1) for l in sys.stdin.read().splitlines() if l); "
             "p=pathlib.Path.home()/'.local/share/sm64ex/sm64config.txt'; "
             "old=p.read_text().splitlines() if p.exists() else []; "
             "kept=[l for l in old if l.split(' ',1)[0] not in new]; "
             "p.write_text('\\n'.join(kept+[k+' '+v for k,v in new.items()])+'\\n')")
    run(*ssh, args.host, f'python3 -c "{merge}"', stdin=(RUNTIME / "controls.txt").open())
    print("Installed. Restart ES-DE to show the Ports system.")
