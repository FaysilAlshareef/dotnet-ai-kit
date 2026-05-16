#!/usr/bin/env bash
# pre-commit-lint: Verify formatting before git commits.
# Hook type: PreToolUse (Bash containing `git commit`) — blocking mode
#
# Runs `dotnet format --verify-no-changes` before commits.
# Blocks the commit if formatting issues are found.
# Skips silently if dotnet is not installed.

set -uo pipefail

# Check if hook is enabled (default: true)
HOOK_ENABLED="${DOTNET_AI_HOOK_COMMIT_LINT:-true}"
if [[ "$HOOK_ENABLED" != "true" ]]; then
  exit 0
fi

# Read command from Claude Code hook stdin (JSON) or fallback to $1.
# Smoke-test each candidate so we ignore the Windows Store python3 stub.
PY_BIN=""
for cand in python3 python py; do
  if command -v "$cand" >/dev/null 2>&1 \
     && "$cand" -c "import sys" >/dev/null 2>&1; then
    PY_BIN="$cand"
    break
  fi
done
if [ ! -t 0 ] && [ -n "$PY_BIN" ]; then
  INPUT_JSON=$(cat)
  COMMAND=$(echo "$INPUT_JSON" | "$PY_BIN" -c "import sys,json;d=json.load(sys.stdin);print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")
fi
COMMAND="${COMMAND:-${1:-}}"
if [[ -z "$COMMAND" ]]; then
  exit 0
fi

# Only trigger before git commit commands
if [[ "$COMMAND" != *"git commit"* ]]; then
  exit 0
fi

# Check if dotnet is available
if ! command -v dotnet &>/dev/null; then
  exit 0
fi

# Check if there's a .sln or .csproj in the current directory tree
if ! find . -maxdepth 3 \( -name "*.sln" -o -name "*.csproj" \) 2>/dev/null | head -1 | grep -q .; then
  exit 0
fi

# Run format verification
if ! dotnet format --verify-no-changes 2>/dev/null; then
  echo ""
  echo "BLOCKED by dotnet-ai-kit pre-commit-lint: Formatting issues found."
  echo "Run 'dotnet format' to fix formatting before committing."
  echo "To disable this hook, set DOTNET_AI_HOOK_COMMIT_LINT=false"
  exit 2
fi

exit 0
