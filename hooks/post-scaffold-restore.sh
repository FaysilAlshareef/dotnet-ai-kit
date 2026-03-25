#!/usr/bin/env bash
# post-scaffold-restore: Auto-run `dotnet restore` after scaffolding.
# Hook type: PostToolUse (Bash containing `dotnet new`) — warn mode (non-blocking)
#
# Runs `dotnet restore` after `dotnet new` commands create new project files.
# Skips silently if dotnet is not installed.

set -uo pipefail

# Check if hook is enabled (default: true)
HOOK_ENABLED="${DOTNET_AI_HOOK_SCAFFOLD_RESTORE:-true}"
if [[ "$HOOK_ENABLED" != "true" ]]; then
  exit 0
fi

# Read command from Claude Code hook stdin (JSON) or fallback to $1
if [ ! -t 0 ]; then
  INPUT_JSON=$(cat)
  COMMAND=$(echo "$INPUT_JSON" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")
fi
COMMAND="${COMMAND:-${1:-}}"
if [[ -z "$COMMAND" ]]; then
  exit 0
fi

# Only trigger after dotnet new commands
if [[ "$COMMAND" != *"dotnet new"* ]]; then
  exit 0
fi

# Check if dotnet is available
if ! command -v dotnet &>/dev/null; then
  exit 0
fi

# Run dotnet restore in the current directory
echo "dotnet-ai-kit: Running dotnet restore after scaffold..."
dotnet restore 2>/dev/null || true

exit 0
