#!/usr/bin/env python3
"""Exercise a built core's actual page-protection routines on the current kernel.

The symbol offsets come from the matching unstripped ELF, not a public core ABI.
No game, display server, or RetroArch process is needed for this regression check.
"""
import ctypes
import json
import os
from pathlib import Path
import sys

core_path = Path(sys.argv[1]).resolve()
symbols = json.loads(Path(sys.argv[2]).read_text())
core = ctypes.CDLL(str(core_path))
bases = []
for line in Path('/proc/self/maps').read_text().splitlines():
    parts = line.split(maxsplit=5)
    if len(parts) == 6 and parts[5] == str(core_path):
        bases.append(int(parts[0].split('-')[0], 16) - int(parts[2], 16))
base = min(bases)
host_page_size = os.sysconf('SC_PAGE_SIZE')
core_page_size = ctypes.c_ulong.from_address(base + symbols['PAGE_SIZE']).value
assert core_page_size == host_page_size, (core_page_size, host_page_size)

libc = ctypes.CDLL(None, use_errno=True)
libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int,
                      ctypes.c_int, ctypes.c_int, ctypes.c_long]
libc.mmap.restype = ctypes.c_void_p
libc.munmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
size = host_page_size * 3
memory = libc.mmap(None, size, 0, 0x22, -1, 0)  # PROT_NONE, PRIVATE|ANONYMOUS
if memory == ctypes.c_void_p(-1).value:
    raise OSError(ctypes.get_errno(), 'mmap')
try:
    # Exercise an offset aligned to 4 KB but inside a page on 16/64 KB kernels.
    address = memory + 4096
    functions = {
        name: ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_size_t)(
            base + symbols[name])
        for name in ('region_lock', 'region_unlock', 'region_set_exec')
    }
    assert functions['region_unlock'](address, 4096)
    ctypes.c_ubyte.from_address(address).value = 0x5A
    assert functions['region_lock'](address, 4096)
    assert ctypes.c_ubyte.from_address(address).value == 0x5A
    assert functions['region_unlock'](address, 4096)
    assert functions['region_set_exec'](address, 4096)
    ctypes.c_ubyte.from_address(address).value = 0xA5
    print(json.dumps({'host_page_size': host_page_size,
                      'core_page_size': core_page_size,
                      'protection_calls': 'passed'}))
finally:
    libc.munmap(memory, size)
