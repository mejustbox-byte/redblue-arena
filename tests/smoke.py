"""Run the real CLI without network, credentials or persistent test data."""

import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
result = subprocess.run(
    [sys.executable, "-m", "redblue_arena", "--config", "examples/lab.json"],
    cwd=root,
    capture_output=True,
    text=True,
    timeout=10,
    check=True,
)
report = json.loads(result.stdout)
if (
    report["mode"] != "synthetic-offline"
    or len(report["events"]) != 6
    or len(report["findings"]) != 1
    or report["findings"][0]["count"] != 6
    or len(report["audit"]) != 3
):
    raise SystemExit("Smoke test failed: unexpected report")
print("Smoke test OK: 6 synthetic events, 1 finding, 3 audit entries")
