"""Verify repository Markdown links and dashboard JavaScript syntax."""

import ast
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    checked = 0
    for path in sorted(ROOT.rglob("*.md")):
        if any(part.startswith(".") for part in path.relative_to(ROOT).parts):
            continue
        for link in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if ":" in link or link.startswith("#"):
                continue
            target = (path.parent / link.split("#")[0]).resolve()
            if not target.is_relative_to(ROOT) or not target.exists():
                raise SystemExit(f"Broken local link: {path.relative_to(ROOT)} -> {link}")
            checked += 1
    node = shutil.which("node")
    if not node:
        raise SystemExit("Node.js is required for JavaScript syntax verification")
    tree = ast.parse((ROOT / "redblue_arena/dashboard.py").read_text(encoding="utf-8"))
    javascript = next(
        ast.literal_eval(item.value)
        for item in tree.body
        if isinstance(item, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "JAVASCRIPT" for target in item.targets
        )
    )
    with tempfile.TemporaryDirectory(prefix="redblue-assets-") as directory:
        path = Path(directory) / "dashboard.js"
        path.write_text(javascript, encoding="utf-8")
        subprocess.run([node, "--check", str(path)], check=True, timeout=10)
    print(f"Local Markdown links OK ({checked}); dashboard JavaScript syntax OK")


if __name__ == "__main__":
    main()
