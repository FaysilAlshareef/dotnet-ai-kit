#!/usr/bin/env python
"""Comprehensive content quality scan across all tool-surface markdown.

One-shot diagnostic for the v1.0.0 review. Scans:
- agents-claude/, agents-source/, agents/
- rules/conventions/, rules/domain/
- skills/**/SKILL.md (124 files)
- commands/*.md (27 files)
- knowledge/*.md (16 files)

Detects:
- Missing/invalid frontmatter
- Token-budget overruns
- Stale references (pre-019 patterns)
- Broken cross-references
- Thin/empty content
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent

issues: dict[str, list[str]] = defaultdict(list)
totals: dict[str, int] = defaultdict(int)

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?\n)---\s*\n?(.*)\Z", re.DOTALL)


def parse_frontmatter(path: Path):
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return None, None, f"read-error: {e}"
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text, "no-frontmatter"
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        return None, text, f"invalid-yaml: {e}"
    return fm, m.group(2), None


def section(title: str) -> None:
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


# --- AGENTS -----------------------------------------------------------------
section("AGENTS")

agent_configs = [
    ("agents-claude", {"name", "description"}),
    ("agents-source", {"name", "description"}),
    ("agents", {"name", "description"}),
]
for d, required in agent_configs:
    folder = REPO / d
    if not folder.exists():
        print(f"{d}: MISSING")
        continue
    files = sorted(folder.glob("*.md"))
    totals[f"{d}-count"] = len(files)
    print(f"{d}: {len(files)} files")
    for f in files:
        fm, body, err = parse_frontmatter(f)
        rel = f.relative_to(REPO)
        if err:
            issues[f"{d}-fm-err"].append(f"{rel}: {err}")
            continue
        for r in required:
            if r not in fm or not fm[r]:
                issues[f"{d}-missing-required"].append(f"{rel}: missing `{r}`")
        if body is None or len(body.strip()) < 50:
            issues[f"{d}-thin-body"].append(f"{rel}: body <50 chars")
        lines = f.read_text(encoding="utf-8").count("\n")
        if lines > 50:
            issues[f"{d}-over-50-lines"].append(f"{rel}: {lines} lines")

# --- RULES ------------------------------------------------------------------
section("RULES")

for d, required, expected in [
    ("rules/conventions", {"description"}, 5),
    ("rules/domain", {"description"}, 11),
]:
    folder = REPO / d
    files = sorted(folder.glob("*.md"))
    totals[f"{d}-count"] = len(files)
    print(f"{d}: {len(files)} files (expected {expected})")
    if len(files) != expected:
        issues["rule-count-mismatch"].append(f"{d}: {len(files)} (expected {expected})")
    for f in files:
        fm, body, err = parse_frontmatter(f)
        rel = f.relative_to(REPO)
        if err:
            issues[f"{d}-fm-err"].append(f"{rel}: {err}")
            continue
        for r in required:
            if r not in fm or not fm[r]:
                issues[f"{d}-missing"].append(f"{rel}: missing `{r}`")
        lines = f.read_text(encoding="utf-8").count("\n")
        if lines > 100:
            issues[f"{d}-over-100"].append(f"{rel}: {lines} lines")
        if d == "rules/conventions" and "paths" in fm:
            issues["universal-rule-has-paths"].append(
                f"{rel}: universal rule has `paths:` frontmatter"
            )
        if d == "rules/domain" and "paths" not in fm:
            issues["domain-rule-missing-paths"].append(
                f"{rel}: domain rule missing `paths:` frontmatter"
            )

# --- SKILLS -----------------------------------------------------------------
section("SKILLS")
skills = sorted(REPO.glob("skills/**/SKILL.md"))
totals["skills-count"] = len(skills)
print(f"skills/**/SKILL.md: {len(skills)} files")

for s in skills:
    fm, body, err = parse_frontmatter(s)
    rel = s.relative_to(REPO)
    if err:
        issues["skill-fm-err"].append(f"{rel}: {err}")
        continue
    if "name" not in fm:
        issues["skill-no-name"].append(f"{rel}")
    if "description" not in fm:
        issues["skill-no-description"].append(f"{rel}")
    if "when_to_use" not in fm and "when-to-use" not in fm:
        issues["skill-no-when-to-use"].append(f"{rel}")
    if "when-to-use" in fm:
        issues["skill-hyphenated-key"].append(f"{rel}")
    if "alwaysApply" in fm:
        issues["skill-legacy-alwaysApply"].append(f"{rel}")
    lines = s.read_text(encoding="utf-8").count("\n")
    if lines > 400:
        issues["skill-over-400"].append(f"{rel}: {lines}")
    if lines < 80:
        issues["skill-thin"].append(f"{rel}: {lines}")
    if body is None or len(body.strip()) < 100:
        issues["skill-empty-body"].append(f"{rel}")

# --- COMMANDS ---------------------------------------------------------------
section("COMMANDS")
cmds = sorted((REPO / "commands").glob("*.md"))
totals["commands-count"] = len(cmds)
print(f"commands/*.md: {len(cmds)} files")
for c in cmds:
    fm, body, err = parse_frontmatter(c)
    rel = c.relative_to(REPO)
    if err:
        issues["cmd-fm-err"].append(f"{rel}: {err}")
        continue
    if "description" not in fm:
        issues["cmd-no-description"].append(f"{rel}")
    lines = c.read_text(encoding="utf-8").count("\n")
    if lines > 200:
        issues["cmd-over-200"].append(f"{rel}: {lines}")

# --- KNOWLEDGE --------------------------------------------------------------
section("KNOWLEDGE")
know = sorted((REPO / "knowledge").glob("*.md"))
totals["knowledge-count"] = len(know)
print(f"knowledge/*.md: {len(know)} files")
for k in know:
    lines = k.read_text(encoding="utf-8").count("\n")
    if lines < 50:
        issues["knowledge-thin"].append(f"{k.relative_to(REPO)}: {lines}")

# --- STALE REFERENCES (all asset files) -------------------------------------
section("STALE REFERENCES")

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
print(f"Scanning {len(all_md)} markdown files for stale patterns")

stale_patterns = {
    "pre-019-bulk-copy-Copied": re.compile(r"Copied:\s*\{N\}"),
    "pre-019-bulk-copy-copies": re.compile(r"copies commands/rules"),
    "pre-019-bulk-copy-recopies": re.compile(r"re-copies commands"),
    "pre-019-per-solution-claude-commands": re.compile(r"\.claude/commands/"),
    "pre-019-per-solution-claude-rules": re.compile(r"\.claude/rules/"),
    "pre-019-per-solution-claude-skills": re.compile(r"\.claude/skills/"),
    "pre-019-per-solution-claude-agents": re.compile(r"\.claude/agents/"),
    "pre-019-4-universal": re.compile(r"4 universal rules"),
    "pre-019-9-always-loaded": re.compile(r"9 always-loaded"),
    "pre-019-15-always-loaded": re.compile(r"15 always-loaded"),
    "pre-018-alwaysApply": re.compile(r"\balwaysApply\b"),
    "todo": re.compile(r"\bTODO[:(]"),
    "fixme": re.compile(r"\bFIXME[:(]"),
    "xxx-marker": re.compile(r"\bXXX[:(]"),
    "csharp-ls-mcp-ref": re.compile(r"csharp-ls\s+for\s+C#"),
}

for label, pat in stale_patterns.items():
    for f in all_md:
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in pat.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            issues[f"stale::{label}"].append(f"{f.relative_to(REPO)}:{line_no} -> '{m.group()}'")

# --- BROKEN CROSS-REFERENCES (skill paths in rules/commands/agents) ---------
section("BROKEN CROSS-REFERENCES")

ref_re = re.compile(r"`(skills/[^`]+SKILL\.md)`")
for f in all_md:
    try:
        text = f.read_text(encoding="utf-8")
    except Exception:
        continue
    for m in ref_re.finditer(text):
        ref = m.group(1)
        target = REPO / ref
        if not target.exists():
            line_no = text[: m.start()].count("\n") + 1
            issues["broken-skill-ref"].append(f"{f.relative_to(REPO)}:{line_no} -> {ref}")

# --- DUPLICATE DESCRIPTIONS (potential copy-paste) -------------------------
section("DUPLICATE DESCRIPTIONS")
desc_to_files: dict[str, list[str]] = defaultdict(list)
for s in skills:
    fm, _, err = parse_frontmatter(s)
    if err or not fm:
        continue
    d = (fm.get("description") or "").strip()
    if d:
        desc_to_files[d].append(str(s.relative_to(REPO)))
for d, paths in desc_to_files.items():
    if len(paths) > 1:
        issues["dup-skill-description"].append(f"{len(paths)}x: '{d[:80]}'")
        for p in paths:
            issues["dup-skill-description"].append(f"    - {p}")

# --- REPORT -----------------------------------------------------------------
section("ISSUE REPORT")

if not issues:
    print("CLEAN. No issues found.")
else:
    for key in sorted(issues.keys()):
        items = issues[key]
        print()
        print(f"[{key}] {len(items)} issue(s)")
        for item in items[:12]:
            print(f"  - {item}")
        if len(items) > 12:
            print(f"  ... ({len(items) - 12} more)")

section("TOTALS")
for k, v in sorted(totals.items()):
    print(f"  {k}: {v}")
print()
print(f"Issue categories: {len(issues)}")
print(f"Total issues: {sum(len(v) for v in issues.values())}")
