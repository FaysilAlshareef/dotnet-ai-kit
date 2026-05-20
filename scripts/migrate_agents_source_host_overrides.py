"""Feature 019 / commit 23 / T162: migrate agents-source/*.md to nest
Claude-allow-list fields under `host_overrides.claude:`.

Per Codex round-3 nit: do NOT add empty placeholder `host_overrides.cursor:`
or `host_overrides.copilot:` blocks unless values are meaningful.

Idempotent: re-runs are no-ops once migration has landed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "agents-source"

NEST_INTO_CLAUDE = ("role", "expertise", "complexity", "max_iterations")


def _parse(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    fm = yaml.safe_load(m.group(1)) or {}
    return fm, m.group(2)


def _serialize(fm: dict, body: str) -> str:
    yml = yaml.dump(fm, default_flow_style=False, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{yml}\n---\n{body if body.startswith(chr(10)) else chr(10) + body}"


def migrate_file(path: Path) -> bool:
    """Migrate one file. Returns True if modified."""
    text = path.read_text(encoding="utf-8")
    fm, body = _parse(text)
    if not fm:
        return False

    # Pull top-level forbidden keys
    pulled = {k: fm.pop(k) for k in NEST_INTO_CLAUDE if k in fm}
    if not pulled:
        return False

    # Merge into host_overrides.claude
    overrides = fm.get("host_overrides") or {}
    claude_block = overrides.get("claude") or {}
    claude_block.update(pulled)
    overrides["claude"] = claude_block
    fm["host_overrides"] = overrides

    path.write_text(_serialize(fm, body), encoding="utf-8")
    return True


def main() -> int:
    if not SRC.is_dir():
        print(f"ERROR: {SRC} not found", file=sys.stderr)
        return 1
    changed = 0
    for src in sorted(SRC.glob("*.md")):
        if migrate_file(src):
            changed += 1
            print(f"migrated: {src.name}")
    print(f"\n{changed}/{len(list(SRC.glob('*.md')))} files migrated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
