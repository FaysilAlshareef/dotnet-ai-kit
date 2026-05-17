#!/usr/bin/env python
"""Generate `agents-claude/<name>.md` files from `agents-source/<name>.md`.

Feature 019 commit 4 / T041 driver. Reads each source-of-truth agent under
`agents-source/` (or, until T054 renames `agents/` -> `agents-source/`, falls
back to `agents/`) and writes the Claude-shape generated file to
`agents-claude/<name>.md`. The Claude plugin manifest declared these paths
in commit 3; this script makes the files exist on disk.

Re-runnable. Idempotent.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ on path when run from repo root
REPO = Path(__file__).resolve().parent.parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from dotnet_ai_kit.agent_generators import generate_claude_agent  # noqa: E402


def main() -> int:
    source_dir = REPO / "agents-source"
    if not source_dir.is_dir() or not any(source_dir.glob("*.md")):
        # T054 hasn't landed yet — fall back to legacy `agents/` location.
        source_dir = REPO / "agents"

    if not source_dir.is_dir():
        print(f"error: source directory not found: {source_dir}", file=sys.stderr)
        return 2

    target_dir = REPO / "agents-claude"
    target_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for src_path in sorted(source_dir.glob("*.md")):
        try:
            content = generate_claude_agent(src_path)
        except Exception as exc:
            print(f"error: {src_path.name}: {exc}", file=sys.stderr)
            return 1

        target_path = target_dir / src_path.name
        target_path.write_text(content, encoding="utf-8")
        count += 1

    print(f"wrote {count} files to {target_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
