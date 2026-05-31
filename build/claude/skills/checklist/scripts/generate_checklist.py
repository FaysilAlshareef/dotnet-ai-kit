#!/usr/bin/env python3
"""Emit a feature quality-checklist skeleton derived from a spec.md.

Illustrative helper for the /dotnet-ai.checklist command. Reads a spec path
(for its title only) and prints a markdown checklist to stdout, or to --out.
Deterministic, stdlib-only, no network.
"""
from __future__ import annotations

import argparse
from pathlib import Path

AREAS = (
    "Functional requirements",
    "Data & persistence",
    "UX & accessibility",
    "Non-functional (perf, security)",
    "Edge cases & error handling",
)


def spec_title(spec: Path) -> str:
    if spec.exists():
        for line in spec.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    return spec.stem


def render(title: str) -> str:
    lines = [f"# Quality Checklist — {title}", ""]
    for area in AREAS:
        lines.append(f"## {area}")
        lines.append("- [ ] TODO: derive a concrete, testable item from the spec.")
        lines.append("- [ ] TODO: add the acceptance criterion that proves it.")
        lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("spec", type=Path, help="Path to the feature spec.md.")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write the checklist here instead of stdout.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    content = render(spec_title(args.spec))
    if args.out is None:
        print(content)
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(content + "\n", encoding="utf-8")
        print(f"wrote: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
