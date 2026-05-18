#!/usr/bin/env python
"""Round 3 — pinpoint the remaining issues."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?\n)---\s*\n?(.*)\Z", re.DOTALL)


def parse(path: Path):
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


# Find skills missing metadata.agent
print("=" * 70)
print("Skills missing metadata.agent")
print("=" * 70)
for s in sorted(REPO.glob("skills/**/SKILL.md")):
    fm, _ = parse(s)
    meta = fm.get("metadata", {}) if fm else {}
    if not isinstance(meta, dict) or "agent" not in meta:
        print(f"  {s.relative_to(REPO)}: metadata.agent missing (metadata={meta!r})")

# Show context for empty sections
print()
print("=" * 70)
print("Empty section contexts")
print("=" * 70)
empty_section_locs = [
    ("skills/workflow/plan-templates/SKILL.md", 70),
    ("skills/workflow/plan-templates/SKILL.md", 73),
    ("skills/workflow/session-management/SKILL.md", 38),
    ("skills/workflow/session-management/SKILL.md", 39),
    ("skills/workflow/session-management/SKILL.md", 40),
    ("commands/review.md", 144),
    ("commands/specify.md", 101),
]
for rel, line_no in empty_section_locs:
    p = REPO / rel
    text = p.read_text(encoding="utf-8")
    lines = text.split("\n")
    start = max(0, line_no - 2)
    end = min(len(lines), line_no + 4)
    print(f"\n--- {rel}:{line_no} ---")
    for i in range(start, end):
        marker = ">>> " if i + 1 == line_no else "    "
        print(f"{marker}{i + 1}: {lines[i]}")

# Check Newtonsoft.Json context (is its use explained?)
print()
print("=" * 70)
print("Newtonsoft.Json usage contexts (5 lines around each)")
print("=" * 70)
nj_locs = [
    ("skills/microservice/command/event-store/SKILL.md", 17),
    ("skills/microservice/command/outbox/SKILL.md", 139),
    ("skills/microservice/processor/event-routing/SKILL.md", 200),
    ("knowledge/outbox-pattern.md", 251),
]
for rel, line_no in nj_locs:
    p = REPO / rel
    text = p.read_text(encoding="utf-8")
    lines = text.split("\n")
    start = max(0, line_no - 3)
    end = min(len(lines), line_no + 4)
    print(f"\n--- {rel}:{line_no} ---")
    for i in range(start, end):
        marker = ">>> " if i + 1 == line_no else "    "
        print(f"{marker}{i + 1}: {lines[i]}")

# What does FR-026 / agent-source contract say about metadata?
print()
print("=" * 70)
print("`metadata.agent` policy — is it required?")
print("=" * 70)
# Sample the 6 missing skills to see if they have alternative
for f in sorted((REPO / "skills" / "workflow").glob("*/SKILL.md")):
    fm, _ = parse(f)
    _rel = f.relative_to(REPO)
    _keys = list(fm.keys())
    _meta = fm.get("metadata", {})
    print(f"  {_rel}: top-level keys = {_keys}, metadata = {_meta}")

# Look at the configuration & multi-repo files to see the must/MUST mix
print()
print("=" * 70)
print("Mixed MUST/must contexts")
print("=" * 70)
for rel in ["rules/domain/configuration.md", "rules/domain/multi-repo.md"]:
    p = REPO / rel
    text = p.read_text(encoding="utf-8")
    print(f"\n--- {rel} ---")
    for m in re.finditer(r"\b(?:MUST|must)\b", text):
        line_no = text[: m.start()].count("\n") + 1
        # Get the line
        lines = text.split("\n")
        if line_no - 1 < len(lines):
            print(f"  {line_no}: {lines[line_no - 1].strip()[:100]}")
