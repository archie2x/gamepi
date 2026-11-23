import configparser
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("receiver", str(
    ROOT / "packaging/gamepi-remote-input/usr/bin/gamepi-remote-input"))
spec = importlib.util.spec_from_loader(loader.name, loader)
receiver = importlib.util.module_from_spec(spec)
loader.exec_module(receiver)


class RemoteInputTests(unittest.TestCase):
    def test_mac_arrows_and_letters_do_not_emit_power_key(self):
        config = configparser.ConfigParser()
        config.read_string("[DEFAULT]\n" + (ROOT / "runtime/input/waynergy.ini").read_text())
        self.assertNotIn("width", config.defaults())
        self.assertNotIn("height", config.defaults())
        mapping = config["raw-keymap"]
        self.assertEqual(mapping.getint("offset"), 8)
        self.assertTrue(mapping.getboolean("offset_on_explicit"))
        for raw, expected in ((1, 30), (37, 28), (124, 105), (125, 106), (126, 108), (127, 103)):
            self.assertEqual(mapping.getint(str(raw)), expected)
        self.assertNotIn(116, [mapping.getint(str(code), fallback=code) for code in range(128)])

    def test_ssh_eof_reaps_receiver(self):
        with tempfile.TemporaryDirectory() as directory:
            pidfile = Path(directory) / "pid"
            read_fd, write_fd = os.pipe()

            def disconnect():
                deadline = time.monotonic() + 5
                while not pidfile.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                os.close(write_fd)

            thread = threading.Thread(target=disconnect)
            thread.start()
            with os.fdopen(read_fd, "rb") as stream:
                code = "import os,time,pathlib;pathlib.Path(%r).write_text(str(os.getpid()));time.sleep(30)" % str(pidfile)
                self.assertEqual(receiver.supervise([sys.executable, "-c", code], stream), 0)
            thread.join()
            with self.assertRaises(ProcessLookupError):
                os.kill(int(pidfile.read_text()), 0)


if __name__ == "__main__":
    unittest.main()
