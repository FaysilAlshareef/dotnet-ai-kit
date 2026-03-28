---
description: "Saves a progress checkpoint for session handoff. Use when pausing work to resume in a later session."
---

# Checkpoint

Quick save -- stage and commit progress in each repo with changes, then write a minimal handoff file. Use when pausing work but planning to return soon.

## Usage

```
/dotnet-ai.checkpoint $ARGUMENTS
```

**Examples:**
- (no args) -- Save progress in all repos with auto-generated message
- `"Completed query side"` -- Save with a custom message
- `--dry-run` -- Show what would be committed without doing it
- `--verbose` -- Show detailed file lists per repo

## Flags

| Flag | Description |
|------|-------------|
| `--dry-run` | Show what would be committed and written, without doing it |
| `--verbose` | Show detailed per-repo file lists and handoff content |
| `--no-commit` | Write handoff only, skip git commits |

## Flow

### Step 1: Detect Active Feature

Read `.dotnet-ai-kit/features/` for the current active feature.
- If no active feature: save changes without feature context (plain checkpoint).
- Load `tasks.md` to determine which tasks are complete/pending.

### Step 2: Scan Repos for Changes

For each repo (or current directory for single-repo projects):
- Run `git status` to detect staged and unstaged changes.
- Categorize files: new, modified, deleted.
- If no changes in any repo: report "No changes to save." and stop.

If `--dry-run`: show the file summary per repo and stop here.

### Step 3: Stage and Commit (per repo with changes)

For each repo with uncommitted changes:
1. Stage relevant files (exclude generated build artifacts, `.vs/`, `bin/`, `obj/`).
2. Create a descriptive commit message:
   ```
   checkpoint: {custom_message or auto_description}

   Feature: {NNN}-{short-name}
   Tasks completed: T001-T005
   Tasks pending: T006-T010
   ```
3. Commit changes.

If `--no-commit`: skip this step entirely.

### Step 4: Write Handoff File

Write `.dotnet-ai-kit/features/{NNN}-{short-name}/handoff.md` with:

```markdown
# Handoff - Checkpoint

session_type: checkpoint
timestamp: {ISO 8601}
feature: {NNN}-{short-name}
message: {custom message or "Mid-session checkpoint"}

## Completed Tasks
- T001: Create OrderAggregate [command]
- T002: Add OrderCreated event [command]
- T003: Create Order entity [query]

## Pending Tasks
- T006: Add GetOrders endpoint [gateway]
- T007: Create Orders page [controlpanel]

## Blocked Items
- (none, or list any blockers)

## Current Context
- Working on: {current task or area}
- Branch: feature/{NNN}-{short-name}
- Repos with changes: command, query
```

### Step 5: Report

```
Checkpoint saved.

Commits:
  command  : "checkpoint: Completed aggregate and events" (4 files)
  query    : "checkpoint: Added Order entity" (3 files)

Handoff written to .dotnet-ai-kit/features/001-orders/handoff.md

Resume with: /dotnet-ai.implement --resume
```

## When to Use

- Pausing work to switch context
- Before attempting a risky operation
- End of a work block when you plan to continue soon
- Before a meeting or break

For end-of-day or longer breaks, use `/dotnet-ai.wrap-up` instead (more comprehensive).

## Dry-Run Behavior

- `--dry-run`: Show per-repo file lists, proposed commit messages, and handoff content. No commits, no file writes.
