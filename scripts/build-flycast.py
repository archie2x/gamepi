#!/usr/bin/env python3
"""Build the pinned Flycast Libretro core with native macOS Clang and LLD."""
import argparse
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--jobs', type=int, default=6)
args = parser.parse_args()
if args.jobs < 1:
    parser.error('--jobs must be positive')

root = Path(__file__).resolve().parent.parent
source = root / 'sources/flycast'
build = root / 'build/flycast-dev'
revision = 'de3eab3e832071ef110a15891144bd4969970057'

def run(*command, **kwargs):
    return subprocess.run(command, check=True, **kwargs)

if not (root / 'toolchain/sysroot/usr/include/stdio.h').is_file():
    parser.error('Extract the pinned sysroot with toolchain/extract-sysroot.py first')
if not (source / '.git').exists():
    source.parent.mkdir(exist_ok=True)
    run('git', 'clone', '--branch', 'dev', '--depth', '1',
        'https://github.com/flyinghead/flycast.git', str(source))
if subprocess.run(['git', '-C', str(source), 'cat-file', '-e', revision],
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
    run('git', '-C', str(source), 'fetch', '--no-recurse-submodules', '--depth', '1', 'https://github.com/flyinghead/flycast.git', revision)
head = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
if head != revision or not (source / 'CMakeLists.txt').exists():
    run('git', '-C', str(source), 'checkout', '--detach', revision)
run('git', '-C', str(source), 'submodule', 'update', '--init', '--recursive', '--depth', '1',
    'core/deps/libchdr', 'core/deps/glslang', 'core/deps/Vulkan-Headers',
    'core/deps/VulkanMemoryAllocator', 'core/deps/rcheevos', 'core/deps/asio',
    'core/deps/tinygettext', 'core/deps/libjuice', 'core/deps/basis_universal')
run('cmake', '-S', str(source), '-B', str(build), '-G', 'Ninja',
    f'-DCMAKE_TOOLCHAIN_FILE={root / "toolchain/cmake/aarch64-linux-gnu.cmake"}',
    '-DCMAKE_BUILD_TYPE=RelWithDebInfo', '-DCMAKE_OSX_ARCHITECTURES=',
    '-DARCHITECTURE=arm64', '-DLIBRETRO=ON', '-DUSE_VULKAN=ON', '-DUSE_OPENGL=ON',
    '-DUSE_OPENMP=OFF', '-DUSE_BREAKPAD=OFF', '-DUSE_LUA=OFF', '-DUSE_DISCORD=OFF',
    '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON')
run('cmake', '--build', str(build), '--parallel', str(args.jobs))
core = build / 'flycast_libretro.so'
names = {'PAGE_SIZE': 'PAGE_SIZE',
         'region_lock': '_ZN7virtmem11region_lockEPvm',
         'region_unlock': '_ZN7virtmem13region_unlockEPvm',
         'region_set_exec': '_ZN7virtmem15region_set_execEPvm'}
output = subprocess.check_output(['/opt/homebrew/opt/llvm/bin/llvm-nm',
                                  '--defined-only', str(core)], text=True)
symbols = {parts[2]: int(parts[0], 16) for line in output.splitlines()
           if len(parts := line.split()) == 3}
(build / 'page-symbols.json').write_text(json.dumps(
    {name: symbols[symbol] for name, symbol in names.items()}, indent=2) + '\n')
run('/opt/homebrew/opt/llvm/bin/llvm-strip', '--strip-debug', '-o',
    str(build / 'flycast-dev_libretro.so'), str(core))
print(build / 'flycast-dev_libretro.so')
