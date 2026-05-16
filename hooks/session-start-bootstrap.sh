#!/usr/bin/env bash
# Session Start Bootstrap — lazy-default activation notice.
# Runs at SessionStart per hooks.json. Keep this short: every byte loads.

cat <<'EOF'
[dotnet-ai-kit] Active. Defaults:
  - Project context: query `codebase-memory-mcp` before broad file reads.
  - Skills: load on demand when the task triggers one. Do not pre-load.
  - Rules: 4 universal rules always loaded; 12 path-scoped activate only when a matching file is touched.

Fallback: if `codebase-memory-mcp` is unavailable or below >=0.6.1, use `csharp-ls` + grep/read.
EOF
