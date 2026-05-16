#!/usr/bin/env python
"""Local pre-commit entry point (T003 / FR-038).

Runs the static + unit pytest suite (skipping smoke). Returns pytest's exit code.

Usage:
    python scripts/check.py              # check the current repo
    python scripts/check.py --root <dir> # check a different repo (e.g. tmp fixture)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run dotnet-ai-kit static + unit tests.")
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root to check (defaults to the current directory).",
    )
    args, extra = parser.parse_known_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"error: --root path does not exist: {root}", file=sys.stderr)
        return 2

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "-x",
        "--ignore=tests/smoke",
        f"--rootdir={root}",
    ]
    cmd.extend(extra)
    return subprocess.run(cmd, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
