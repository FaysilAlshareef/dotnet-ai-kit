#!/usr/bin/env python
"""T025 / FR-006-008 — One-shot rewrite of all skills/**/SKILL.md frontmatter.

Lifts the following keys from ``metadata`` to top-level:
  - ``paths``
  - ``when-to-use`` (also renamed to ``when_to_use``)
  - ``alwaysApply``  (dropped entirely — Claude Code has no such concept)
  - ``disable-model-invocation``
  - ``user-invocable``

Preserves the remaining ``metadata`` block (typically ``category`` and ``agent``).

Usage:
    python scripts/rewrite_skill_frontmatter.py --dry-run
    python scripts/rewrite_skill_frontmatter.py            # writes in place
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

LIFT_KEYS = {"paths", "when-to-use", "disable-model-invocation", "user-invocable"}
DROP_KEYS = {"alwaysApply"}


def _split_frontmatter(text: str) -> tuple[str, str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    return text[4:end], text[end + 5 :]


def _render(front: dict, body: str) -> str:
    front_yaml = yaml.safe_dump(front, sort_keys=False, allow_unicode=True, width=120)
    return f"---\n{front_yaml}---\n{body}"


def rewrite_one(path: Path) -> tuple[bool, str]:
    raw = path.read_text(encoding="utf-8")
    parts = _split_frontmatter(raw)
    if parts is None:
        return False, "no frontmatter"

    front_text, body = parts
    front = yaml.safe_load(front_text) or {}
    if not isinstance(front, dict):
        return False, "frontmatter is not a mapping"

    metadata = front.get("metadata") or {}
    if not isinstance(metadata, dict):
        return False, "metadata is not a mapping"

    changed = False
    for key in list(metadata.keys()):
        if key in DROP_KEYS:
            metadata.pop(key)
            changed = True
        elif key in LIFT_KEYS:
            value = metadata.pop(key)
            top_key = "when_to_use" if key == "when-to-use" else key
            if top_key not in front:
                front[top_key] = value
            changed = True

    # Also drop top-level alwaysApply if some skill set it there.
    if "alwaysApply" in front:
        front.pop("alwaysApply")
        changed = True

    if metadata:
        front["metadata"] = metadata
    elif "metadata" in front:
        front.pop("metadata")
        changed = True

    if not changed:
        return False, "no change"

    path.write_text(_render(front, body), encoding="utf-8")
    return True, "rewritten"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--root", default="skills")
    args = ap.parse_args()

    root = Path(args.root)
    files = sorted(root.rglob("SKILL.md"))
    if not files:
        print(f"no SKILL.md under {root}", file=sys.stderr)
        return 1

    changes = 0
    for f in files:
        if args.dry_run:
            raw = f.read_text(encoding="utf-8")
            parts = _split_frontmatter(raw)
            if parts is None:
                continue
            front = yaml.safe_load(parts[0]) or {}
            md = front.get("metadata") or {}
            keys = [k for k in md if k in LIFT_KEYS or k in DROP_KEYS]
            if "alwaysApply" in front:
                keys.append("alwaysApply(top)")
            if keys:
                print(f"DRY {f}: would lift/drop {keys}")
                changes += 1
            continue
        ok, note = rewrite_one(f)
        if ok:
            changes += 1
            print(f"{f}: {note}")

    print(
        f"{'dry-run: ' if args.dry_run else ''}{changes} file(s) {'would be' if args.dry_run else ''} changed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
