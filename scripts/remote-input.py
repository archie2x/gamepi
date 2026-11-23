#!/usr/bin/env python3
"""SwiftBar controls for an on-demand, launchd-managed SSH input connection."""
import argparse
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import time

HOME = Path.home()
CONFIG = HOME / ".config/gamepi/remote-input.json"
CACHE = HOME / ".cache/gamepi/remote-input"
STATE = CACHE / "status.json"
LABEL = "io.github.archie2x.gamepi.remote-input"
SERVICE = f"gui/{os.getuid()}/{LABEL}"
PLUGIN = Path(os.environ.get("SWIFTBAR_PLUGIN_PATH", HOME / ".swiftbar/gamepi-input.5s.sh"))


def state(value, message=""):
    CACHE.mkdir(parents=True, exist_ok=True)
    temporary = STATE.with_suffix(f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps({"state": value, "message": message, "pid": os.getpid()}))
    temporary.replace(STATE)


def job_pid():
    result = subprocess.run(["/bin/launchctl", "print", SERVICE], capture_output=True, text=True)
    match = re.search(r"^\s*pid = (\d+)$", result.stdout, re.M)
    return int(match[1]) if result.returncode == 0 and match else None


def status():
    pid = job_pid()
    try:
        current = json.loads(STATE.read_text())
    except (OSError, ValueError):
        current = {}
    if pid:
        return current if current.get("pid") == pid else {"state": "connecting"}
    return current if current.get("state") == "error" else {"state": "disconnected"}


def run():
    state("connecting")
    tunnel = None

    def stop(*_):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        config = json.loads(CONFIG.read_text())
        try:
            connection = socket.create_connection(("127.0.0.1", 24800), timeout=0.5)
        except OSError:
            subprocess.run(["/usr/bin/open", "-g", "-a", "Deskflow"], check=True)
            for attempt in range(20):
                time.sleep(0.25)
                try:
                    connection = socket.create_connection(("127.0.0.1", 24800), timeout=0.5)
                    break
                except OSError:
                    if attempt == 19:
                        raise RuntimeError("Start the Deskflow server in its window")
        connection.close()
        ssh = ["/usr/bin/ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
               "-o", "ExitOnForwardFailure=yes", "-o", "ServerAliveInterval=10",
               "-o", "ServerAliveCountMax=3"]
        for key, option in (("hostname", "HostName"), ("host_key_alias", "HostKeyAlias")):
            if config.get(key):
                ssh += ["-o", option + "=" + config[key]]
        tunnel = subprocess.Popen(
            ssh + ["-R", "127.0.0.1:24805:127.0.0.1:24800", config.get("host", "gamepi"),
                   "exec /usr/bin/gamepi-remote-input"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1)
        for line in tunnel.stdout:
            print(line, end="", flush=True)
            if 'Connected as client "gamepi"' in line:
                state("connected")
            elif "[ERROR]" in line or "Server disconnected" in line:
                state("connecting", line.strip())
        result = tunnel.wait()
        raise RuntimeError(f"Connection ended ({result}); see connection log")
    except KeyboardInterrupt:
        state("disconnected")
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr, flush=True)
        state("error", str(error))
    finally:
        if tunnel:
            if tunnel.stdin:
                tunnel.stdin.close()
            try:
                tunnel.wait(timeout=5)
            except subprocess.TimeoutExpired:
                tunnel.terminate()
                try:
                    tunnel.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    tunnel.kill()
                    tunnel.wait()


def menu():
    current = status()
    value = current["state"]
    labels = {"connected": ("●", "green"), "connecting": ("…", "orange"),
              "disconnected": ("○", "gray"), "error": ("!", "red")}
    icon, color = labels[value]
    print(f"{icon} Gamepi Input | color={color}")
    print("---")
    print(value.capitalize() + " | disabled=true")
    if current.get("message"):
        message = current["message"].replace("|", "/").replace("\n", " ")[:160]
        print(message + " | disabled=true")
    action = "stop" if value in ("connected", "connecting") else "start"
    title = "Disconnect" if action == "stop" else "Connect"
    print(f'{title} | bash="{PLUGIN}" param1={action} terminal=false refresh=true')
    print("---")
    print("Move off the Mac’s left screen edge to use gamepi | disabled=true")
    for title, action in (("Open Deskflow", "deskflow"), ("Show connection log", "logs")):
        print(f'{title} | bash="{PLUGIN}" param1={action} terminal=false')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", default="menu",
                        choices=("menu", "start", "stop", "status", "run", "deskflow", "logs"))
    action = parser.parse_args().action
    if action == "run":
        run()
    elif action == "menu":
        menu()
    elif action == "status":
        print(json.dumps(status()))
    elif action == "start":
        if not job_pid():
            state("connecting")
            subprocess.run(["/bin/launchctl", "kickstart", SERVICE], check=True)
    elif action == "stop":
        if job_pid():
            subprocess.run(["/bin/launchctl", "kill", "SIGTERM", SERVICE], check=True)
        state("disconnected")
    elif action == "deskflow":
        subprocess.run(["/usr/bin/open", "-a", "Deskflow"], check=True)
    elif action == "logs":
        subprocess.run(["/usr/bin/open", "-a", "TextEdit", str(CACHE / "receiver.log")], check=True)


if __name__ == "__main__":
    main()
