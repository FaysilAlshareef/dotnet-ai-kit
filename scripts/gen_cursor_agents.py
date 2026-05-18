#!/usr/bin/env python
"""Generate Cursor-shape build output under `agents/<name>.md`.

Feature 019 commit 6 / T057 driver. Per data-model.md § 1c and
contracts/cursor-fixture-decision.contract.md, the `.cursor-plugin/plugin.json`
manifest declares `"agents": "./agents/"` and Cursor loads sub-agents from
that path. This script reads source-of-truth markdown from
`agents-source/<name>.md` and writes Cursor-shape files to `agents/<name>.md`.

Re-runnable. Idempotent.

Until the A-005 spike outcome (CHK003 via tests/integration/test_smoke_cursor.py)
is recorded as passed, only the single dedicated fixture
(`dotnet-ai-architect`) is generated. The other 12 specialists are deferred
to spike-pass commits.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from dotnet_ai_kit.agent_generators import generate_cursor_agent  # noqa: E402

# Single Cursor sub-agent fixture per A-005 spike (CHK003).
# Expanded to all 13 once the spike outcome lands "passed" via T060.
_FIXTURE_NAMES = ("dotnet-ai-architect",)


def main() -> int:
    source_dir = REPO / "agents-source"
    target_dir = REPO / "agents"

    if not source_dir.is_dir():
        print(f"error: source directory not found: {source_dir}", file=sys.stderr)
        return 2

    target_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for name in _FIXTURE_NAMES:
        src_path = source_dir / f"{name}.md"
        if not src_path.is_file():
            print(f"error: source not found: {src_path}", file=sys.stderr)
            return 1

        try:
            content = generate_cursor_agent(src_path)
        except Exception as exc:
            print(f"error: {src_path.name}: {exc}", file=sys.stderr)
            return 1

        target_path = target_dir / src_path.name
        target_path.write_text(content, encoding="utf-8")
        count += 1

    print(f"wrote {count} Cursor-shape agent(s) to {target_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
