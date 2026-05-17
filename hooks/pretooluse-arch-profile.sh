#!/usr/bin/env bash
# PreToolUse architecture-profile hook (feature 019 / FR-034 / US3).
# Per contracts/pretooluse-arch-profile.contract.md.
# Reads .dotnet-ai-kit/project.yml at FIRE-TIME (no caching) — mid-session
# profile changes are observed by the next tool use.
# Output: profile body + convention pointers. Exit code: always 0 (advisory).
set -eu
PYM=".dotnet-ai-kit/project.yml"
[ -f "$PYM" ] || { echo "Project metadata not initialized; run \`dotnet-ai init\`"; exit 0; }
prof=$(grep -E '^[[:space:]]*architecture_profile_name:' "$PYM" 2>/dev/null \
  | head -n1 | sed -E 's/.*:[[:space:]]*//; s/[[:space:]]+$//' || true)
[ -z "$prof" ] && prof=$(grep -E '^[[:space:]]*project_type:' "$PYM" 2>/dev/null \
  | head -n1 | sed -E 's/.*:[[:space:]]*//; s/[[:space:]]+$//' || true)
[ -z "$prof" ] && { echo "Project metadata corrupt; run \`dotnet-ai check\` for details"; exit 0; }
branch=$(grep -E '^[[:space:]]*architecture_branch:' "$PYM" 2>/dev/null \
  | head -n1 | sed -E 's/.*:[[:space:]]*//; s/[[:space:]]+$//' || true)
[ -z "$branch" ] && branch="generic"
ROOT="${CLAUDE_PLUGIN_ROOT:-${PLUGIN_ROOT:-.}}"
profile_file="$ROOT/profiles/$branch/$prof.md"
echo "Active architecture profile: $prof ($branch)"
if [ -f "$profile_file" ]; then
  cat "$profile_file"
else
  echo "Unknown architecture profile: $prof; run \`dotnet-ai check\` for valid values"
fi
echo "Always-on conventions: rules/conventions/{async-concurrency,coding-style,existing-projects,security,tool-calls}.md"
