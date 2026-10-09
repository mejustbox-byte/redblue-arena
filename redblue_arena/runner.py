"""Fixed-command workers. Docker is the default isolation boundary."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from threading import Event


class JobCancelled(Exception):
    pass


class Runner:
    def __init__(self, mode: str = "docker", timeout: float = 10):
        if mode not in {"docker", "trusted-local"}:
            raise ValueError("Unknown runner mode")
        self.mode, self.timeout = mode, timeout

    def execute(self, config: dict, cancel: Event) -> dict:
        name = "redblue-" + uuid.uuid4().hex
        docker = shutil.which("docker")
        if self.mode == "docker":
            if not docker:
                raise RuntimeError("Docker required; no fallback to local execution")
            command = [
                docker,
                "run",
                "--pull=never",
                "--rm",
                "--name",
                name,
                "--network=none",
                "--read-only",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                "--pids-limit=32",
                "--memory=128m",
                "--cpus=0.5",
                "--user=65532:65532",
                "--log-driver=none",
                "-i",
                "--entrypoint=python",
                "redblue-arena:lab",
                "-m",
                "redblue_arena.worker",
            ]
        else:
            command = [sys.executable, "-m", "redblue_arena.worker"]
        environment = {
            "PATH": os.defpath,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
            "LANG": "C.UTF-8",
        }
        with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=output,
                stderr=errors,
                cwd=Path(__file__).resolve().parents[1],
                env=environment,
            )
            deadline = time.monotonic() + self.timeout
            try:
                payload = json.dumps(config).encode()
                while True:
                    if cancel.is_set():
                        raise JobCancelled()
                    if time.monotonic() > deadline:
                        raise TimeoutError("Worker time limit exceeded")
                    try:
                        process.communicate(payload, timeout=0.1)
                        break
                    except subprocess.TimeoutExpired:
                        payload = None
                if process.returncode:
                    raise RuntimeError("Worker failed")
                output.seek(0)
                raw = output.read(2 * 1024 * 1024 + 1)
                if len(raw) > 2 * 1024 * 1024:
                    raise RuntimeError("Worker report exceeds limit")
                report = json.loads(raw)
                if not isinstance(report, dict) or report.get("mode") != "synthetic-offline":
                    raise RuntimeError("Worker returned invalid report")
                return report
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)
                if process.stdin and not process.stdin.closed:
                    process.stdin.close()
                if self.mode == "docker":
                    subprocess.run(
                        [docker, "rm", "-f", name],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=5,
                        check=False,
                    )
