"""Repository-owned development setup and checks; never creates lab credentials."""

import argparse
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".venv"
PYTHON = ENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(*args: str, docker: bool = False) -> None:
    env = os.environ.copy()
    env.pop("REDBLUE_DOCKER_TESTS", None)
    if docker:
        env["REDBLUE_DOCKER_TESTS"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(args, cwd=ROOT, env=env, check=True, timeout=300)


def require_python() -> None:
    if sys.version_info[:2] != (3, 12):
        raise SystemExit("Use CPython 3.12.x to run scripts/dev.py")


def require_env() -> None:
    if not PYTHON.is_file():
        raise SystemExit("Run python3.12 scripts/dev.py setup first")
    run(str(PYTHON), "-c", "import sys; assert sys.version_info[:2] == (3, 12)")


def check(docker: bool) -> None:
    require_env()
    run(str(PYTHON), "-m", "pip", "check")
    run(str(PYTHON), "-m", "ruff", "check", "redblue_arena", "tests", "scripts")
    run(str(PYTHON), "-m", "ruff", "format", "--check", "redblue_arena", "tests", "scripts")
    run(
        str(PYTHON),
        "-W",
        "error::ResourceWarning",
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-v",
    )
    run(str(PYTHON), "tests/smoke.py")
    run(str(PYTHON), "-m", "redblue_arena", "--config", "examples/lab.json", "--evaluate")
    if docker:
        executable = shutil.which("docker")
        if not executable:
            raise SystemExit("Docker is required for --docker; no trusted-local fallback")
        run(executable, "build", "-t", "redblue-arena:lab", ".")
        run(
            str(PYTHON),
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-p",
            "test_runner.py",
            "-v",
            docker=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("setup", "check", "doctor"))
    parser.add_argument("--docker", action="store_true", help="Build and test isolated workers")
    args = parser.parse_args()
    require_python()
    if args.command == "setup":
        if ENV.exists():
            require_env()
        else:
            venv.EnvBuilder(with_pip=True).create(ENV)
        run(str(PYTHON), "-m", "pip", "install", "-r", "requirements-dev.txt")
        check(args.docker)
    elif args.command == "check":
        check(args.docker)
    else:
        print(f"Python: {sys.version.split()[0]}")
        print(f"Platform: {sys.platform}; control plane requires POSIX")
        print(f"Development venv: {'present' if PYTHON.is_file() else 'missing'}")
        print(f"Docker command: {'present' if shutil.which('docker') else 'missing'}")
        print("Docker daemon/image readiness is verified by check --docker")


if __name__ == "__main__":
    try:
        main()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        raise SystemExit(f"Development command failed: {type(exc).__name__}") from None
