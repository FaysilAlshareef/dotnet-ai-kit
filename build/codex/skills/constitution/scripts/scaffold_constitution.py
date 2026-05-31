#!/usr/bin/env python3
"""Scaffold/validate a .dotnet-ai-kit/constitution.md skeleton.

Illustrative helper for the /dotnet-ai.constitution command. Deterministic,
stdlib-only, no network. Writes the skeleton when missing; with --check it
verifies the required sections are present and exits non-zero if not.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REQUIRED_SECTIONS = ("Principles", "Constraints", "Amendments")

SKELETON = """# Project Constitution

Version: 0.1.0

## Principles

- TODO: state each governing principle the SDD cycle must obey.

## Constraints

- TODO: list non-negotiable technical/process constraints.

## Amendments

- TODO: record version, date, and rationale for each change.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--path",
        type=Path,
        default=Path(".dotnet-ai-kit") / "constitution.md",
        help="Target constitution path (default: .dotnet-ai-kit/constitution.md).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate required sections exist instead of writing.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path: Path = args.path

    if args.check:
        if not path.exists():
            print(f"missing: {path}", file=sys.stderr)
            return 1
        text = path.read_text(encoding="utf-8")
        missing = [s for s in REQUIRED_SECTIONS if f"## {s}" not in text]
        if missing:
            print("missing sections: " + ", ".join(missing), file=sys.stderr)
            return 1
        print(f"ok: {path}")
        return 0

    if path.exists():
        print(f"exists, leaving untouched: {path}")
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(SKELETON, encoding="utf-8")
    print(f"wrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
