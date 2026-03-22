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

# The command to check is passed as the first argument
COMMAND="${1:-}"
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
if ! find . -maxdepth 3 -name "*.sln" -o -name "*.csproj" 2>/dev/null | head -1 | grep -q .; then
  exit 0
fi

# Run format verification
if ! dotnet format --verify-no-changes 2>/dev/null; then
  echo ""
  echo "BLOCKED by dotnet-ai-kit pre-commit-lint: Formatting issues found."
  echo "Run 'dotnet format' to fix formatting before committing."
  echo "To disable this hook, set DOTNET_AI_HOOK_COMMIT_LINT=false"
  exit 1
fi

exit 0
