#!/usr/bin/env bash
# PreToolUse domain-rules hook — injects path-scoped rules from rules/domain/.
#
# Why: Claude Code's plugin manifest has no `rules` key. The 5 universal
# conventions ride in CLAUDE.md (always loaded). The 11 path-scoped domain
# rules ride here — we inspect the file the user is about to edit, match it
# against each rule's `paths:` glob frontmatter, and prepend the matching
# rule bodies as additional context for the tool call.
#
# Hook type: PreToolUse on Edit|Write|MultiEdit. Exit 0 always (advisory).
# Output budget: ~24KB (~6k tokens) for matched bodies, deduplicated.
# Disable per-shell with: DOTNET_AI_HOOK_DOMAIN_RULES=false
set -uo pipefail

HOOK_ENABLED="${DOTNET_AI_HOOK_DOMAIN_RULES:-true}"
if [[ "$HOOK_ENABLED" != "true" ]]; then
  exit 0
fi

# No stdin → nothing to match against; quiet exit.
if [ -t 0 ]; then
  exit 0
fi

INPUT_JSON=$(cat)
ROOT="${CLAUDE_PLUGIN_ROOT:-${PLUGIN_ROOT:-.}}"
DOMAIN_DIR="$ROOT/rules/domain"
[ -d "$DOMAIN_DIR" ] || exit 0

# Resolve a working Python interpreter. On Windows, `python3` may resolve to
# the Microsoft Store shim which exits non-zero without running anything.
PY=""
for candidate in python3 python py; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c "import sys" >/dev/null 2>&1; then
      PY="$candidate"
      break
    fi
  fi
done
[ -n "$PY" ] || exit 0

INPUT_JSON="$INPUT_JSON" DOMAIN_DIR="$DOMAIN_DIR" "$PY" <<'PYEOF'
import json
import os
import re
import sys
from pathlib import Path

raw = os.environ.get("INPUT_JSON", "")
domain_dir = Path(os.environ.get("DOMAIN_DIR", ""))

try:
    data = json.loads(raw)
except (json.JSONDecodeError, ValueError):
    sys.exit(0)

tool_input = data.get("tool_input") or {}
file_path = tool_input.get("file_path") or ""
if not file_path:
    sys.exit(0)

# Normalise to forward slashes for portable glob matching.
norm = file_path.replace("\\", "/")

# Strip leading project-root absolute prefix so patterns like `src/**/*.cs`
# match both absolute and relative tool inputs.
cwd = os.getcwd().replace("\\", "/").rstrip("/")
if cwd and norm.startswith(cwd + "/"):
    norm = norm[len(cwd) + 1:]


def glob_to_regex(pattern):
    """Translate a gitignore-ish glob to a Python regex.

    Supports `**` (zero or more path components), `*` (non-slash run),
    `?` (single non-slash). Other characters are literal.
    """
    parts = []
    i = 0
    n = len(pattern)
    while i < n:
        if pattern[i:i + 3] == "**/":
            parts.append("(?:.*/)?")
            i += 3
        elif pattern[i:i + 2] == "**":
            parts.append(".*")
            i += 2
        elif pattern[i] == "*":
            parts.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            parts.append("[^/]")
            i += 1
        elif pattern[i] in r".+()|^$\{}[]":
            parts.append(re.escape(pattern[i]))
            i += 1
        else:
            parts.append(pattern[i])
            i += 1
    return re.compile("^" + "".join(parts) + "$")


def parse_paths(text):
    """Extract the `paths:` list from a rule's YAML frontmatter."""
    if not text.startswith("---"):
        return []
    m = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return []
    fm = m.group(1)
    pm = re.search(r"^paths:\s*\n((?:\s*-\s*.+\n?)+)", fm, re.MULTILINE)
    if not pm:
        return []
    out = []
    for line in pm.group(1).splitlines():
        s = line.strip()
        if s.startswith("-"):
            val = s[1:].strip().strip('"').strip("'")
            if val:
                out.append(val)
    return out


def strip_frontmatter(text):
    return re.sub(r"\A---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL).lstrip("\n")


emitted_names = set()
emitted = []
total = 0
BUDGET = 24000

for rule_path in sorted(domain_dir.glob("*.md")):
    if rule_path.name in emitted_names:
        continue
    text = rule_path.read_text(encoding="utf-8")
    patterns = parse_paths(text)
    if not patterns:
        continue
    for pat in patterns:
        try:
            rx = glob_to_regex(pat)
        except re.error:
            continue
        if rx.match(norm):
            body = strip_frontmatter(text).rstrip()
            if total + len(body) > BUDGET:
                break
            emitted_names.add(rule_path.name)
            emitted.append((rule_path.stem, body))
            total += len(body)
            break
    if total >= BUDGET:
        break

if emitted:
    print(f"Path-scoped rules for {file_path}:")
    print()
    for stem, body in emitted:
        print(f"--- rule: {stem} ---")
        print()
        print(body)
        print()
PYEOF
exit 0
