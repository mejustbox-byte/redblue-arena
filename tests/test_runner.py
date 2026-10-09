import os
import subprocess
import threading
import unittest
from unittest.mock import patch

from redblue_arena.runner import JobCancelled, Runner

CONFIG = {
    "authorized": True,
    "allowed_targets": ["lab://training"],
    "target": "lab://training",
    "scenario": "failed-logins",
}


class RunnerTests(unittest.TestCase):
    def test_local_worker_and_rejection(self):
        report = Runner("trusted-local").execute(CONFIG, threading.Event())
        self.assertEqual(report["schema_version"], 2)
        with self.assertRaises(RuntimeError):
            Runner("trusted-local").execute({**CONFIG, "authorized": False}, threading.Event())

    def test_cancel_and_timeout(self):
        signal = threading.Event()
        signal.set()
        with self.assertRaises(JobCancelled):
            Runner("trusted-local").execute(CONFIG, signal)
        with self.assertRaises(TimeoutError):
            Runner("trusted-local", timeout=0).execute(CONFIG, threading.Event())

    def test_no_implicit_isolation_fallback(self):
        with (
            patch("redblue_arena.runner.shutil.which", return_value=None),
            self.assertRaises(RuntimeError),
        ):
            Runner().execute(CONFIG, threading.Event())


@unittest.skipUnless(os.environ.get("REDBLUE_DOCKER_TESTS") == "1", "Docker integration is opt-in")
class DockerTests(unittest.TestCase):
    def test_container_worker(self):
        report = Runner().execute(CONFIG, threading.Event())
        self.assertEqual(report["mode"], "synthetic-offline")
        self.assertEqual(len(report["findings"]), 1)

    def test_runtime_boundaries(self):
        code = """import os,socket
assert os.geteuid()==65532
try:
 open('/app/forbidden','w')
except OSError:
 pass
else:
 raise AssertionError('Filesystem writable')
try:
 socket.create_connection(('192.0.2.1',443),timeout=0.2)
except OSError:
 pass
else:
 raise AssertionError('Network reachable')
print('Container boundaries OK')
"""
        result = subprocess.run(
            [
                "docker",
                "run",
                "--pull=never",
                "--rm",
                "--network=none",
                "--read-only",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                "--pids-limit=32",
                "--memory=128m",
                "--cpus=0.5",
                "--user=65532:65532",
                "--entrypoint=python",
                "redblue-arena:lab",
                "-c",
                code,
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        self.assertIn("Container boundaries OK", result.stdout)
