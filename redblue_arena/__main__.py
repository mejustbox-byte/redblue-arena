import argparse
import json
import sys
from pathlib import Path

from .core import run


def main() -> int:
    parser = argparse.ArgumentParser(description="RedBlue Arena: offline synthetic lab")
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    try:
        with args.config.open("rb") as stream:
            raw = stream.read(65537)
        if len(raw) > 65536:
            raise ValueError("Config exceeds 64 KiB")
        report = run(json.loads(raw))
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "rejected", "error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
