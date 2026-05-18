#!/usr/bin/env python
"""Round 4 — knowledge orphans, paths consistency, placeholder usage."""

from __future__ import annotations

import re
from collections import defaultdict
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


all_md = (
    list(REPO.glob("agents-claude/*.md"))
    + list(REPO.glob("agents-source/*.md"))
    + list(REPO.glob("agents/*.md"))
    + list(REPO.glob("rules/conventions/*.md"))
    + list(REPO.glob("rules/domain/*.md"))
    + list(REPO.glob("skills/**/SKILL.md"))
    + list(REPO.glob("commands/*.md"))
    + list(REPO.glob("knowledge/*.md"))
)

# --- KNOWLEDGE FILE ORPHANS ----------------------------------------------
print("=" * 70)
print("Knowledge files — referenced anywhere?")
print("=" * 70)
know_files = sorted((REPO / "knowledge").glob("*.md"))
ref_counts = defaultdict(int)
for k in know_files:
    fname = k.name
    stem = k.stem
    for f in all_md:
        if f == k:
            continue
        text = f.read_text(encoding="utf-8")
        if f"knowledge/{fname}" in text or f"`{stem}`" in text or stem in text:
            ref_counts[fname] += 1
for k in know_files:
    print(f"  {k.name}: referenced from {ref_counts[k.name]} other file(s)")

# --- SKILLS WITH `paths:` ------------------------------------------------
print()
print("=" * 70)
print("Skills with `paths:` frontmatter (9 total)")
print("=" * 70)
skill_paths = {}
for s in sorted(REPO.glob("skills/**/SKILL.md")):
    fm, _ = parse(s)
    if fm and "paths" in fm:
        skill_paths[str(s.relative_to(REPO))] = fm["paths"]
for sk, p in skill_paths.items():
    print(f"  {sk}: paths={p}")

# --- PLACEHOLDER USAGE ({Company}, {Domain}, etc.) ----------------------
print()
print("=" * 70)
print("Template placeholder usage")
print("=" * 70)
placeholders = defaultdict(int)
files_with = defaultdict(set)
for f in all_md:
    text = f.read_text(encoding="utf-8")
    for m in re.finditer(r"\{([A-Z][A-Za-z_]*)\}", text):
        ph = m.group(1)
        placeholders[ph] += 1
        files_with[ph].add(str(f.relative_to(REPO)))
print("Top placeholders:")
for ph, count in sorted(placeholders.items(), key=lambda x: -x[1])[:15]:
    print(f"  {{{ph}}}: {count} occurrences in {len(files_with[ph])} files")

# --- UNDOCUMENTED METADATA FIELDS ----------------------------------------
print()
print("=" * 70)
print("All distinct top-level frontmatter keys across assets")
print("=" * 70)
all_keys = defaultdict(int)
for f in all_md:
    fm, _ = parse(f)
    if fm:
        for k in fm.keys():
            all_keys[k] += 1
for k, count in sorted(all_keys.items(), key=lambda x: -x[1]):
    print(f"  {k}: {count}")

# --- RULES — RELATED SKILLS CONSISTENCY -----------------------------------
print()
print("=" * 70)
print("Rules — Related Skills sections")
print("=" * 70)
all_rules = sorted((REPO / "rules" / "conventions").glob("*.md")) + sorted(
    (REPO / "rules" / "domain").glob("*.md")
)
rules_without_related = []
rules_with_related = []
for r in all_rules:
    text = r.read_text(encoding="utf-8")
    has_related = bool(re.search(r"^## Related Skills", text, re.MULTILINE))
    if has_related:
        rules_with_related.append(r.relative_to(REPO))
    else:
        rules_without_related.append(r.relative_to(REPO))
print(f"With 'Related Skills' section: {len(rules_with_related)}/16")
for r in rules_with_related:
    print(f"  + {r}")
print()
print(f"Without 'Related Skills' section: {len(rules_without_related)}/16")
for r in rules_without_related:
    print(f"  - {r}")

# --- COMMAND-TO-SUBCOMMAND consistency ------------------------------------
print()
print("=" * 70)
print("Command flag references")
print("=" * 70)
# Look for --flag references in commands and verify they exist somewhere
for c in sorted((REPO / "commands").glob("*.md"))[:5]:
    text = c.read_text(encoding="utf-8")
    flags = sorted(set(re.findall(r"--([a-z][a-z-]+)", text)))
    print(f"  {c.name}: flags={flags[:8]}{'...' if len(flags) > 8 else ''}")
