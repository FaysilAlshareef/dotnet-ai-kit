# dotnet-ai-kit - Permission & Bypass Configuration

## Problem

Claude Code asks for permission on many operations. For a tool that orchestrates
multi-repo work, constant permission prompts slow down the workflow significantly.

## Solution: Scoped Bypass

The tool provides ready-to-use permission configs that bypass prompts ONLY for:
1. The tool's working directory
2. Specific tool operations
3. Specific MCP operations

User explicitly opts in during `/dotnet-ai.configure`.

---

## Permission Levels

### Level 1: Minimal (Default)
Only allows build and test commands. Everything else requires confirmation.

### Level 2: Standard (Recommended)
Allows file operations in working directory, git operations, build/test, and `gh` CLI (PRs, repos, issues).

### Level 3: Full Bypass
Allows all operations in working directory (including all `gh` CLI commands). Use for trusted automation.

---

## Ready-to-Use Configs

### `/dotnet-ai.configure` generates:

#### `.claude/settings.local.json` (per-project)
```json
{
  "permissions": {
    "allow": [
      "Bash(dotnet build:*)",
      "Bash(dotnet test:*)",
      "Bash(dotnet restore:*)",
      "Bash(dotnet format:*)",
      "Bash(dotnet new:*)",
      "Bash(gh pr:*)",
      "Bash(gh repo:*)",
      "Bash(gh issue:*)",
      "Bash(git checkout:*)",
      "Bash(git branch:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git push:*)",
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git stash:*)",
      "Bash(ls:*)",
      "Bash(dir:*)",
      "Bash(tree:*)",
      "Bash(mkdir:*)",
      "Bash(cat:*)",
      "Bash(coderabbit:*)"
    ]
  }
}
```

#### For MCP tools (if using GitHub MCP)
```json
{
  "permissions": {
    "allow": [
      "mcp__github__get_file_contents",
      "mcp__github__search_code",
      "mcp__github__search_repositories",
      "mcp__github__create_pull_request",
      "mcp__github__list_branches",
      "mcp__github__create_branch",
      "mcp__github__get_pull_request",
      "mcp__github__list_pull_requests",
      "mcp__github__create_issue",
      "mcp__github__list_issues",
      "mcp__github__get_issue"
    ]
  }
}
```

---

## Configuration Flow

```
/dotnet-ai.configure

...other questions...

Permission Configuration:

  The tool needs permissions for file, git, and build operations.
  Choose a permission level:

  1. Minimal   - Only build/test (ask for everything else)
  2. Standard  - Build, test, git, gh CLI (recommended)
  3. Full      - All operations in working directory

  > 2

  Apply to:
  1. This project only (.claude/settings.local.json)
  2. User-wide (~/.claude/settings.json)

  > 1

  Generated: .claude/settings.local.json

  MCP Permissions:
  Do you use GitHub MCP server? [Y/n]
  > Y

  Added GitHub MCP permissions.

  Do you use CodeRabbit CLI? [Y/n]
  > Y

  Added coderabbit permissions.
```

---

## Safety Boundaries

Even in Full Bypass mode, the tool NEVER:
- Force-pushes to main/master/develop
- Deletes remote branches
- Modifies CI/CD pipelines without asking
- Accesses repos not in the configured list
- Pushes secrets to git
- Runs `rm -rf` or destructive commands

These are enforced by the tool's rules (`.claude/rules/`), not by Claude Code's permission system.

---

## Hook-Based Guards

The tool includes a pre-bash-guard hook (from dotnet-claude-kit pattern):

```json
// hooks/hooks.json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/pre-bash-guard.sh"
          }
        ]
      }
    ]
  }
}
```

```bash
# hooks/pre-bash-guard.sh
# Blocks dangerous operations even in bypass mode
BLOCKED_PATTERNS=(
  "git push.*--force"
  "git push.*-f "
  "git reset --hard"
  "rm -rf /"
  "git branch -D main"
  "git branch -D master"
  "git branch -D develop"
)
```

This ensures safety guardrails exist even when permissions are bypassed.
