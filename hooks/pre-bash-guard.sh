#!/usr/bin/env bash
# pre-bash-guard: Block dangerous commands before execution.
# Hook type: PreToolUse (Bash) — blocking mode
#
# Default blocklist includes 20+ dangerous patterns.
# Users can extend via settings but cannot remove defaults.

set -euo pipefail

# Check if hook is enabled (default: true)
HOOK_ENABLED="${DOTNET_AI_HOOK_BASH_GUARD:-true}"
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

# Default blocklist — dangerous command patterns
BLOCKLIST=(
  "rm -rf /"
  "rm -r /"
  "rm -rf /*"
  "rmdir /s"
  "del /s /q"
  "del /s"
  "format C:"
  "format c:"
  "mkfs"
  "dd if="
  "DROP DATABASE"
  "DROP TABLE"
  "TRUNCATE TABLE"
  "DELETE FROM"
  "drop database"
  "drop table"
  "truncate table"
  "shutdown"
  "reboot"
  "chmod -R 777"
  "chown -R"
  "> /dev/sda"
  "wget|sh"
  "wget|bash"
  "curl|sh"
  "curl|bash"
  ":(){ :|:& };:"
)

# Load extra patterns from environment if set
if [[ -n "${DOTNET_AI_BASH_GUARD_EXTRA:-}" ]]; then
  IFS=',' read -ra EXTRA <<< "$DOTNET_AI_BASH_GUARD_EXTRA"
  BLOCKLIST+=("${EXTRA[@]}")
fi

# Split command on pipes and semicolons, check each segment
# We check the command verb/structure, not arbitrary substrings in arguments
IFS='|;&' read -ra SEGMENTS <<< "$COMMAND"

for segment in "${SEGMENTS[@]}"; do
  # Trim leading/trailing whitespace
  trimmed="$(echo "$segment" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"

  if [[ -z "$trimmed" ]]; then
    continue
  fi

  for pattern in "${BLOCKLIST[@]}"; do
    # Check if the segment starts with the dangerous pattern
    if [[ "$trimmed" == "$pattern"* ]] || [[ "$trimmed" == *"$pattern"* && "$pattern" == *" "* ]]; then
      echo "BLOCKED by dotnet-ai-kit bash-guard: '$trimmed'"
      echo "Matched dangerous pattern: '$pattern'"
      echo "To disable this hook, set DOTNET_AI_HOOK_BASH_GUARD=false"
      exit 1
    fi
  done
done

exit 0
