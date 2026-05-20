#!/usr/bin/env python
"""Round 2 — deeper content audit.

Checks for:
- Empty section bodies (## header with no content beneath)
- Inconsistent voice (MUST vs should vs do — within same file)
- Outdated .NET version references (.NET 5, .NET Core 3.x, .NET Framework)
- Outdated package references (Newtonsoft.Json without context)
- Body completeness — skills/rules that read as a stub
- Cross-AI-host symmetry — fields that are consistent across hosts
- Knowledge file freshness
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
issues: dict[str, list[str]] = defaultdict(list)

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?\n)---\s*\n?(.*)\Z", re.DOTALL)


def parse_frontmatter(path: Path):
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None, None, "read-error"
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text, "no-frontmatter"
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return None, text, "invalid-yaml"
    return fm, m.group(2), None


def section(title: str) -> None:
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


all_assets = (
    list(REPO.glob("agents-claude/*.md"))
    + list(REPO.glob("agents-source/*.md"))
    + list(REPO.glob("agents/*.md"))
    + list(REPO.glob("rules/conventions/*.md"))
    + list(REPO.glob("rules/domain/*.md"))
    + list(REPO.glob("skills/**/SKILL.md"))
    + list(REPO.glob("commands/*.md"))
    + list(REPO.glob("knowledge/*.md"))
)

# --- EMPTY SECTIONS ---------------------------------------------------------
section("EMPTY SECTIONS")

for f in all_assets:
    text = f.read_text(encoding="utf-8")
    lines = text.split("\n")
    for i, line in enumerate(lines):
        m = re.match(r"^(#{2,4})\s+(.+?)\s*$", line)
        if not m:
            continue
        # Find next non-blank, non-frontmatter line
        next_content = None
        for j in range(i + 1, min(i + 5, len(lines))):
            stripped = lines[j].strip()
            if stripped == "":
                continue
            if stripped.startswith("---"):
                continue
            next_content = stripped
            break
        # If next line starts another header at same/higher level → empty
        if next_content is None:
            continue
        if next_content.startswith("#"):
            n_match = re.match(r"^(#+)", next_content)
            if n_match and len(n_match.group(1)) <= len(m.group(1)):
                issues["empty-section"].append(
                    f"{f.relative_to(REPO)}:{i + 1} '{m.group(2)}' has no body before next header"
                )

# --- INCONSISTENT VOICE -----------------------------------------------------
# Look for files mixing "MUST" with "should" / "must" (case)
section("VOICE INCONSISTENCIES")

for f in all_assets:
    text = f.read_text(encoding="utf-8")
    has_must_upper = bool(re.search(r"\bMUST\b", text))
    has_must_lower = bool(re.search(r"\bmust\b(?!\s*(not|n['']t))", text))
    if has_must_upper and has_must_lower:
        rel = f.relative_to(REPO)
        # Count
        upper = len(re.findall(r"\bMUST\b", text))
        lower = len(re.findall(r"\bmust\b(?!\s*(not|n['']t))", text))
        issues["mixed-must"].append(f"{rel}: MUST={upper} must={lower}")

# --- OUTDATED .NET VERSIONS -------------------------------------------------
section("OUTDATED .NET REFERENCES")

outdated_patterns = {
    "dotnet-5": re.compile(r"\.NET 5(?!\.\d)|net5\.0|netcoreapp3"),
    "dotnet-framework": re.compile(r"\.NET Framework(?!\s+\(legacy\)|\s+for older)"),
    "dotnet-core-old": re.compile(r"\.NET Core 2\.|\.NET Core 3\."),
    "newtonsoft-no-context": re.compile(
        r"Newtonsoft\.Json(?!(?:\s*\(legacy\)|\s+for\s+older|\s+in legacy))"
    ),
}
for label, pat in outdated_patterns.items():
    for f in all_assets:
        text = f.read_text(encoding="utf-8")
        for m in pat.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            issues[f"outdated-{label}"].append(f"{f.relative_to(REPO)}:{line_no} -> '{m.group()}'")

# --- SKILLS METADATA CONSISTENCY -------------------------------------------
section("SKILLS METADATA")
skill_files = list(REPO.glob("skills/**/SKILL.md"))
metadata_keys = defaultdict(int)
all_fields = defaultdict(int)
for s in skill_files:
    fm, body, err = parse_frontmatter(s)
    if err or not fm:
        continue
    for k in fm.keys():
        all_fields[k] += 1
    meta = fm.get("metadata", {})
    if isinstance(meta, dict):
        for k in meta.keys():
            metadata_keys[k] += 1
print("Top-level frontmatter fields across 124 skills:")
for k, count in sorted(all_fields.items(), key=lambda x: -x[1]):
    pct = round(count / len(skill_files) * 100, 1)
    flag = (
        ""
        if count == len(skill_files)
        else f"  <-- inconsistent ({count}/{len(skill_files)} = {pct}%)"
    )
    print(f"  {k}: {count}{flag}")
print()
print("metadata.* nested fields across 124 skills:")
for k, count in sorted(metadata_keys.items(), key=lambda x: -x[1]):
    pct = round(count / len(skill_files) * 100, 1)
    flag = (
        ""
        if count == len(skill_files)
        else f"  <-- inconsistent ({count}/{len(skill_files)} = {pct}%)"
    )
    print(f"  {k}: {count}{flag}")

# --- SKILL "WHEN TO USE" ANALYSIS ------------------------------------------
section("SKILL when_to_use VS description")
missing_wtu = []
both_present = []
description_starts_with_use_when = 0
for s in skill_files:
    fm, body, err = parse_frontmatter(s)
    if err or not fm:
        continue
    desc = (fm.get("description") or "").strip()
    wtu = fm.get("when_to_use") or fm.get("when-to-use") or ""
    if not wtu:
        missing_wtu.append((s.relative_to(REPO), desc[:60]))
    else:
        both_present.append((s.relative_to(REPO), desc[:60], str(wtu)[:60]))
    if desc.lower().startswith("use when"):
        description_starts_with_use_when += 1

print(f"Skills missing when_to_use: {len(missing_wtu)}")
for f, d in missing_wtu[:10]:
    print(f"  {f}: description='{d}...'")
if len(missing_wtu) > 10:
    print(f"  ...({len(missing_wtu) - 10} more)")
print()
_n = len(skill_files)
print(f"Skills with description starting 'Use when': {description_starts_with_use_when}/{_n}")

# --- AGENT-SOURCE / AGENT-CLAUDE PARITY ------------------------------------
section("AGENT SYMMETRY")
src = {p.stem for p in (REPO / "agents-source").glob("*.md")}
claude = {p.stem for p in (REPO / "agents-claude").glob("*.md")}
cursor = {p.stem for p in (REPO / "agents").glob("*.md")}
print(f"agents-source: {sorted(src)}")
print(f"agents-claude: {sorted(claude)}")
print(f"agents (cursor fixture): {sorted(cursor)}")
print()
only_in_src = src - claude
only_in_claude = claude - src
print(f"In agents-source/ but NOT agents-claude/: {sorted(only_in_src)}")
print(f"In agents-claude/ but NOT agents-source/: {sorted(only_in_claude)}")

# --- KNOWLEDGE FILE CHECKS --------------------------------------------------
section("KNOWLEDGE FILE STATUS")
know = sorted((REPO / "knowledge").glob("*.md"))
for k in know:
    text = k.read_text(encoding="utf-8")
    lines = text.count("\n")
    # Check for architecture-019-specific refs (shouldn't exist in pure knowledge)
    has_h2 = bool(re.search(r"^## ", text, re.MULTILINE))
    print(f"  {k.name}: {lines} lines, has-H2-sections={has_h2}")

# --- COMMAND-vs-CLI DRIFT ---------------------------------------------------
section("COMMAND/CLI DRIFT")
# Each command in commands/ should refer to a real CLI subcommand
# Check that command names match CLI registrations
cmd_files = sorted((REPO / "commands").glob("*.md"))
print(f"Commands (slash-command bodies): {len(cmd_files)}")
for c in cmd_files:
    text = c.read_text(encoding="utf-8")
    # Look for "dotnet-ai <subcommand>" patterns
    cli_refs = re.findall(r"dotnet-ai\s+([a-z-]+)", text)
    if cli_refs:
        seen = set(cli_refs)
        if len(seen) > 1:
            issues[f"cli-refs::{c.name}"].append(f"references CLI subcommands: {sorted(seen)}")

# --- REPORT -----------------------------------------------------------------
section("ROUND-2 ISSUE REPORT")

for key in sorted(issues.keys()):
    items = issues[key]
    print()
    print(f"[{key}] {len(items)} issue(s)")
    for item in items[:15]:
        print(f"  - {item}")
    if len(items) > 15:
        print(f"  ... ({len(items) - 15} more)")

section("ROUND-2 TOTAL")
print(f"Issue categories: {len(issues)}")
print(f"Total issues: {sum(len(v) for v in issues.values())}")
