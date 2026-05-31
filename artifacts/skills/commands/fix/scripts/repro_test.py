#!/usr/bin/env python3
"""Scaffold a failing-test stub and print the TDD reproduce-fix-verify steps.

Illustrative helper for the /dotnet-ai.fix command. Given a symptom, suggests
a deterministic test path and (optionally) writes a placeholder stub there,
then prints the disciplined loop. Stdlib-only, no network.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

STUB = """// Failing reproduction stub for: {symptom}
// Replace the body with a test that fails for the RIGHT reason, then fix.
// using Xunit;  [Fact]  Assert.Equal(expected, actual);
"""


def slug(symptom: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", " ", symptom).title().replace(" ", "")
    return (cleaned or "Symptom") + "ReproTests"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("symptom", help="Short description of the reported bug.")
    parser.add_argument(
        "--tests-dir",
        type=Path,
        default=Path("tests"),
        help="Directory for the test stub (default: tests).",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write the stub file (otherwise just print the plan).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path = args.tests_dir / f"{slug(args.symptom)}.cs"

    print("TDD bug-fix loop:")
    print(f"  1. Reproduce: write a failing test at {path}")
    print("     - assert the CORRECT behaviour; confirm it fails for the right reason.")
    print("  2. Fix: make the minimal change to turn it green (no unrelated refactors).")
    print("  3. Verify: run build + tests; confirm green and no regressions.")

    if args.write:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            print(f"exists, leaving untouched: {path}")
        else:
            path.write_text(STUB.format(symptom=args.symptom), encoding="utf-8")
            print(f"wrote stub: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
