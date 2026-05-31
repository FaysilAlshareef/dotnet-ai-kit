#!/usr/bin/env python3
"""Bump a semver in a file and append a Keep-a-Changelog entry.

Illustrative helper for the /dotnet-ai.release command. Reads the first
MAJOR.MINOR.PATCH found in --version-file, bumps it, writes it back, and
appends a changelog entry. Deterministic (date is an explicit arg),
stdlib-only, no network.
"""
from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

SEMVER = re.compile(r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)")


def bump(version: str, part: str) -> str:
    m = SEMVER.search(version)
    if not m:
        raise ValueError(f"no semver found in: {version!r}")
    major, minor, patch = (int(m.group(k)) for k in ("major", "minor", "patch"))
    if part == "major":
        major, minor, patch = major + 1, 0, 0
    elif part == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--major", action="store_true")
    group.add_argument("--minor", action="store_true")
    group.add_argument("--patch", action="store_true")
    parser.add_argument("--version-file", type=Path, required=True)
    parser.add_argument("--changelog", type=Path, default=Path("CHANGELOG.md"))
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Release date (ISO, default today) — explicit for deterministic output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    part = "major" if args.major else "minor" if args.minor else "patch"

    text = args.version_file.read_text(encoding="utf-8")
    current = SEMVER.search(text)
    if not current:
        raise SystemExit(f"no semver found in {args.version_file}")
    new_version = bump(current.group(0), part)
    args.version_file.write_text(text.replace(current.group(0), new_version, 1), encoding="utf-8")

    entry = f"\n## [{new_version}] - {args.date}\n\n### Changed\n\n- TODO: summarize the merged change.\n"
    with args.changelog.open("a", encoding="utf-8") as fh:
        fh.write(entry)

    print(f"bumped {current.group(0)} -> {new_version}; appended to {args.changelog}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
