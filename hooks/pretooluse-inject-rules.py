#!/usr/bin/env python3
"""Claude PreToolUse hook (T1 advisory injection — FR-020, Claude-scoped).

When the assistant is about to edit a file that matches a project-local rule's `paths:` glob,
inject that rule's body as `additionalContext`. Reads the tool event from stdin; no network.
This is the runtime delivery half of the v1 rule-delivery fix.
"""
import fnmatch
import json
import pathlib
import re
import sys


def glob_to_regex(glob: str) -> str:
    # Minimal **/* aware translation good enough for path scoping.
    escaped = re.escape(glob).replace(r"\*\*/", ".*").replace(r"\*\*", ".*").replace(r"\*", "[^/]*")
    return "^" + escaped + "$"


def parse_rule(path: pathlib.Path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return None
    frontmatter, body = m.group(1), m.group(2)
    globs = re.findall(r'-\s*"([^"]+)"', frontmatter)
    return globs, body.strip()


def matches(rel: str, globs: list[str]) -> bool:
    name = pathlib.PurePosixPath(rel).name
    return any(
        re.match(glob_to_regex(g), rel) or fnmatch.fnmatch(name, g.rsplit("/", 1)[-1])
        for g in globs
    )


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    file_path = (event.get("tool_input") or {}).get("file_path") or ""
    rules_dir = pathlib.Path(".claude/rules")
    if not file_path or not rules_dir.is_dir():
        sys.exit(0)

    rel = file_path.replace("\\", "/")
    parts: list[str] = []
    for rule in sorted(rules_dir.glob("*.md")):
        parsed = parse_rule(rule)
        if not parsed:
            continue
        globs, body = parsed
        # Universal rules (no paths) always apply; domain rules apply on a path match.
        if not globs or matches(rel, globs):
            parts.append(body)

    if parts:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": "\n\n".join(parts),
            }
        }))
    sys.exit(0)


if __name__ == "__main__":
    main()
