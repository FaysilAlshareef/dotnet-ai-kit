#!/usr/bin/env python
"""Markdown doc-lint for dotnet-ai-kit (feature 019 / T128).

Scans markdown files for:
1. Broken relative-link references (file paths that don't exist on disk).
2. Stale references to legacy v1.0.7 universal rule whitelist
   (`4 universal`, `naming` as universal, etc.).

Scope:
- `README.md`
- `CLAUDE.md`
- `docs/**/*.md`
- `planning/**/*.md`
- `specs/019-plugin-native-arch/**/*.md` (release-related)

Usage:
  python scripts/doc_lint.py            # check; exit 0 = clean, 1 = issues found
  python scripts/doc_lint.py --verbose  # print every file scanned
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Stale references that were valid in v1.0.7 but obsolete in v1.0.8
# Feature 019 / commit 28 / T191: scope extended per content-quality review O1.
STALE_PHRASES = (
    "4 universal rules",
    "4 universal (always loaded",
    # Feature 019: pre-019 / plugin-native architecture stale phrases.
    "9 always-loaded",
    "15 always-loaded",
    "5 safety hooks",
    "csharp-ls for C# intelligence",
    "re-copies commands",
    # Common pre-019 placeholder strings from output templates.
    "Copied: {N}",
)

# Stale phrases evaluated as regex (anchored partial-match) — flag if matched.
STALE_REGEX = (re.compile(r"Copied:\s*\{N\}"),)

SCAN_GLOBS = (
    "README.md",
    "CLAUDE.md",
    # Feature 019 / T191 / O1: scope expansion.
    "AGENTS.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "docs/**/*.md",
    "planning/**/*.md",
    "commands/**/*.md",
    "rules/**/*.md",
)

# Match markdown links like [text](url) where url is a relative path
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)#]+)(?:#[^)]*)?\)")


def _is_external(url: str) -> bool:
    """Skip http/https/mailto links."""
    return url.startswith(("http://", "https://", "mailto:", "#"))


def _check_broken_links(file_path: Path) -> list[str]:
    """Return error messages for broken relative-path links."""
    errors: list[str] = []
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError:
        return [f"{file_path}: cannot read"]
    for m in LINK_RE.finditer(text):
        url = m.group(2).strip()
        if _is_external(url):
            continue
        # Strip query strings
        url = url.split("?")[0]
        target = (file_path.parent / url).resolve()
        if not target.exists():
            errors.append(
                f"{file_path.relative_to(REPO)}: broken link '{url}' -> "
                f"{target.relative_to(REPO) if target.is_relative_to(REPO) else target}"
            )
    return errors


def _check_stale_phrases(file_path: Path) -> list[str]:
    """Return error messages for stale v1.0.7 phrases."""
    errors: list[str] = []
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError:
        return []
    for phrase in STALE_PHRASES:
        if phrase in text:
            errors.append(
                f"{file_path.relative_to(REPO)}: stale phrase '{phrase}' "
                f"(v1.0.7 wording; v1.0.8 has 5 universal rules)"
            )
    for pat in STALE_REGEX:
        if pat.search(text):
            errors.append(
                f"{file_path.relative_to(REPO)}: stale pattern '{pat.pattern}' "
                f"(pre-019 placeholder — replace with the per-solution file list "
                f"or 'served by plugin' wording per T165/T166)"
            )
    return errors


def _iter_md_files() -> list[Path]:
    out: list[Path] = []
    for pattern in SCAN_GLOBS:
        out.extend(REPO.glob(pattern))
    return [p for p in out if p.is_file() and p.suffix == ".md"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Markdown doc-lint.")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    files = _iter_md_files()
    all_errors: list[str] = []
    for f in files:
        if args.verbose:
            print(f"scanning {f.relative_to(REPO)}")
        all_errors.extend(_check_broken_links(f))
        all_errors.extend(_check_stale_phrases(f))

    if all_errors:
        print("Doc-lint FAILED:", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"[OK] Doc-lint passed ({len(files)} files scanned).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
