#!/usr/bin/env python3
"""Install Gamepi Input into SwiftBar and a manually started launchd job."""
import argparse
import json
import os
from pathlib import Path
import plistlib
import shlex
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
home = Path.home()
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--hostname", help="Optional SSH address override; otherwise use the gamepi SSH alias")
parser.add_argument("--host-key-alias", default="gamepi.local")
args = parser.parse_args()
controller = home / ".local/share/gamepi/mac/remote-input.py"
controller.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(root / "scripts/remote-input.py", controller)
config = home / ".config/gamepi/remote-input.json"
config.parent.mkdir(parents=True, exist_ok=True)
if not config.exists():
    settings = {"host": "gamepi"}
    if args.hostname:
        settings.update(hostname=args.hostname, host_key_alias=args.host_key_alias)
    config.write_text(json.dumps(settings, indent=2) + "\n")
plugin_dir = Path(subprocess.check_output(
    ["/usr/bin/defaults", "read", "com.ameba.SwiftBar", "PluginDirectory"], text=True).strip())
plugin_dir.mkdir(parents=True, exist_ok=True)
plugin = plugin_dir / "gamepi-input.5s.sh"
template = (root / "runtime/input/gamepi-input.5s.sh").read_text()
plugin.write_text(template.replace("@PYTHON@", shlex.quote(sys.executable))
                  .replace("@CONTROLLER@", shlex.quote(str(controller))))
plugin.chmod(0o755)
label = "io.github.archie2x.gamepi.remote-input"
cache = home / ".cache/gamepi/remote-input"
cache.mkdir(parents=True, exist_ok=True)
agent = home / "Library/LaunchAgents" / (label + ".plist")
agent.parent.mkdir(parents=True, exist_ok=True)
agent.write_bytes(plistlib.dumps({"Label": label,
    "ProgramArguments": [sys.executable, str(controller), "run"],
    "RunAtLoad": False, "KeepAlive": False, "ProcessType": "Interactive",
    "StandardOutPath": str(cache / "receiver.log"),
    "StandardErrorPath": str(cache / "receiver.log")}))
service = f"gui/{os.getuid()}/{label}"
loaded = subprocess.run(["/bin/launchctl", "print", service], capture_output=True).returncode == 0
if not loaded:
    subprocess.run(["/bin/launchctl", "bootstrap", f"gui/{os.getuid()}", str(agent)], check=True)
print("Installed:", plugin)
print("SSH settings:", config)
print("Use Connect in the Gamepi Input menu. Sharing does not start at login.")
