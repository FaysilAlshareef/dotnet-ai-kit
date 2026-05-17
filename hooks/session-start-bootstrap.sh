#!/usr/bin/env bash
# SessionStart bootstrap — compact index, NO bulk rule bodies.
# Per feature 019 / FR-013 / SC-013 / contracts/session-start-bootstrap.contract.md.
# Output budget: <=500 tokens (verified by tests/unit/test_session_start_budget.py).
set -eu
PYM=".dotnet-ai-kit/project.yml"
prof="(unknown)"
if [ -f "$PYM" ]; then
  prof=$(grep -E '^[[:space:]]*architecture_profile_name:' "$PYM" 2>/dev/null \
    | head -n1 | sed -E 's/.*:[[:space:]]*//; s/[[:space:]]+$//' || true)
  [ -z "$prof" ] && prof=$(grep -E '^[[:space:]]*project_type:' "$PYM" 2>/dev/null \
    | head -n1 | sed -E 's/.*:[[:space:]]*//; s/[[:space:]]+$//' || true)
  [ -z "$prof" ] && prof="(unset)"
  cat <<EOF
dotnet-ai-kit active
Project metadata: $PYM
Architecture profile: $prof
Run \`dotnet-ai check\` to verify state
Skills and rules load on-demand via plugin namespace
Persistent memory: codebase-memory-mcp (call on demand for cross-session context)
EOF
else
  cat <<EOF
dotnet-ai-kit active
Project metadata not initialized; run \`dotnet-ai init\`
Skills and rules load on-demand via plugin namespace
Persistent memory: codebase-memory-mcp (call on demand for cross-session context)
EOF
fi
