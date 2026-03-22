#!/usr/bin/env bash
# post-edit-format: Auto-format .cs files after edits.
# Hook type: PostToolUse (Edit|Write on *.cs) — warn mode (non-blocking)
#
# Runs `dotnet format` on the edited file if dotnet CLI is available.
# Skips silently if dotnet is not installed.

set -uo pipefail

# Check if hook is enabled (default: true)
HOOK_ENABLED="${DOTNET_AI_HOOK_EDIT_FORMAT:-true}"
if [[ "$HOOK_ENABLED" != "true" ]]; then
  exit 0
fi

# The edited file path is passed as the first argument
FILE_PATH="${1:-}"
if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# Only process .cs files
if [[ "$FILE_PATH" != *.cs ]]; then
  exit 0
fi

# Check if dotnet is available
if ! command -v dotnet &>/dev/null; then
  exit 0
fi

# Check if the file exists
if [[ ! -f "$FILE_PATH" ]]; then
  exit 0
fi

# Run dotnet format on the specific file
dotnet format --include "$FILE_PATH" 2>/dev/null || true

exit 0
