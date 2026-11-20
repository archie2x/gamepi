#!/usr/bin/env python3
"""Connect gamepi to the running Mac Deskflow app over an SSH tunnel."""

from pathlib import Path
import shlex
import socket
import subprocess
import time


ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
CONFIG = HOME / ".config/gamepi/remote-input"
CACHE = HOME / ".cache/gamepi/remote-input"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]


def main():
    try:
        with socket.create_connection(("127.0.0.1", 24800), timeout=0.3):
            pass
    except OSError as error:
        raise SystemExit("Start the configured Deskflow server on the Mac first.") from error
    CONFIG.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    install = (
        "from pathlib import Path;import sys;"
        "p=Path.home()/'.config/gamepi/remote-input/config.ini';"
        "p.parent.mkdir(parents=True,exist_ok=True);"
        "p.write_bytes(sys.stdin.buffer.read());p.chmod(0o600)"
    )
    subprocess.run(
        SSH + ["gamepi", "python3 -c " + shlex.quote(install)],
        input=(ROOT / "runtime/input/waynergy.ini").read_bytes(), check=True,
    )
    tunnel = None
    with (CACHE / "receiver.log").open("ab", buffering=0) as receiver_log:
        try:
            remote = (
                'env XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}" '
                'WAYLAND_DISPLAY=wayland-0 '
                'WAYNERGY_CONF_PATH="$HOME/.config/gamepi/remote-input" '
                '"$HOME/.local/bin/waynergy" -b uinput -c 127.0.0.1 -p 24805 '
                '-N gamepi -E -n -L info'
            )
            tunnel = subprocess.Popen(
                SSH + ["-T", "-o", "ExitOnForwardFailure=yes", "-o", "ServerAliveInterval=10",
                       "-o", "ServerAliveCountMax=3", "-R",
                       "127.0.0.1:24805:127.0.0.1:24800", "gamepi", remote],
                stdin=subprocess.DEVNULL, stdout=receiver_log, stderr=subprocess.STDOUT,
            )
            print("Move the pointer across the configured screen edge to switch computers. Ctrl+C here stops sharing.", flush=True)
            while tunnel.poll() is None:
                time.sleep(0.25)
            raise SystemExit("Input sharing ended; see the logs in " + str(CACHE))
        except KeyboardInterrupt:
            pass
        finally:
            for process in [tunnel]:
                if process and process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()


if __name__ == "__main__":
    main()
