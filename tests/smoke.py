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
    report["schema_version"] != 2
    or report["mode"] != "synthetic-offline"
    or len(report["events"]) != 6
    or len(report["findings"]) != 1
    or report["findings"][0]["count"] != 6
    or len(report["audit"]) != 3
):
    raise SystemExit("Smoke test failed: unexpected report")
print("Smoke test OK: 6 synthetic events, 1 finding, 3 audit entries")

for config, event_count, finding_count in (
    ("examples/threshold.json", 5, 1),
    ("examples/benign.json", 6, 0),
    ("examples/spread.json", 6, 0),
):
    result = subprocess.run(
        [sys.executable, "-m", "redblue_arena", "--config", config],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    report = json.loads(result.stdout)
    if (
        report["schema_version"] != 2
        or report["mode"] != "synthetic-offline"
        or len(report["events"]) != event_count
        or len(report["findings"]) != finding_count
        or len(report["audit"]) != 3
    ):
        raise SystemExit(f"Smoke test failed: unexpected report for {config}")
    print(f"Smoke test OK: {config}, {event_count} events, {finding_count} findings")
