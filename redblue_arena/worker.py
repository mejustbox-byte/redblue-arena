"""Fixed worker protocol: one bounded JSON config in, one report out."""

import json
import sys

from .core import run


def main() -> int:
    try:
        raw = sys.stdin.buffer.read(65537)
        if len(raw) > 65536:
            raise ValueError("Config exceeds 64 KiB")
        report = run(json.loads(raw))
        print(json.dumps(report))
        return 0
    except (ValueError, TypeError):
        print("Worker rejected configuration", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
