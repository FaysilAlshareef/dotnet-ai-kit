---
description: "Revert the last code generation action or specific task with preview and confirmation"
---

# Undo

Safely revert the last implementation step or a specific task. Shows a preview of what will be reverted and asks for confirmation before making changes.

## Usage

```
/dotnet-ai.undo $ARGUMENTS
```

**Examples:**
- (no args) -- Undo the last action
- `T005` -- Undo specific task T005
- `--list` -- Show undo history without reverting
- `--preview` -- Show what would be reverted without doing it
- `--verbose` -- Show detailed file diffs before reverting

## Flags

| Flag | Description |
|------|-------------|
| `--list` | Show undo history (all recorded actions) without reverting |
| `--preview` | Show what would be reverted, do not revert |
| `--dry-run` | Same as `--preview` |
| `--verbose` | Show full file diffs for each file that would be reverted |
| `--force` | Skip confirmation prompt (use with caution) |

## Flow

### Step 1: Locate Undo Log

Read `.dotnet-ai-kit/features/{current}/undo-log.md` for the active feature.
- If no active feature: check for most recent feature with undo log.
- If no undo log found: report "No undo history found. Nothing to revert." and stop.

### Step 2: Select Action to Undo

- **No args**: select the most recent (last) entry in the undo log.
- **Task ID** (e.g., `T005`): find matching entry.
  - If not found: report "Task T005 not found in undo history. Available: T003, T004, T005" and stop.
- **`--list`**: display all entries and stop.

### Step 3: Check Revertibility

For each file in the selected action, check:
- **Created files**: verify they still exist and are unmodified since generation.
- **Modified files**: verify the modifications are still present (not further changed).
- **Committed files**: if changes have been committed, report:
  ```
  Changes for T005 have been committed. Cannot undo committed work.
  Use `git revert <commit>` or `git reset` to revert committed changes.
  ```
  Stop here -- only uncommitted changes can be reverted.

### Step 4: Preview Changes

Display what will be reverted:
```
Undo T005: Create OrderController

Files to revert:
  DELETE  Controllers/OrderController.cs         (created by T005)
  DELETE  Models/CreateOrderRequest.cs            (created by T005)
  REVERT  Program.cs                              (restore previous version)

Confirm? [Y/n]
```

If `--preview` or `--dry-run`: show the preview and stop without reverting.
If `--verbose`: also show file diffs for modified files.

### Step 5: Execute Revert (after confirmation)

- **Created files**: delete them (`rm {file}`)
- **Modified files**: restore previous version (`git checkout -- {file}`)
- **Update tasks.md**: mark the task as pending again (change `[x]` to `[ ]`)
- **Update undo-log.md**: mark the entry as reverted

### Step 6: Report

```
T005 reverted. 3 files restored.
Task T005 marked as pending in tasks.md.
```

## Undo Log Format

Each task records its file changes when executed:
```
## T005 - Create OrderController
timestamp: 2024-01-15T14:30:00Z
repo: gateway
- created: Controllers/OrderController.cs
- created: Models/CreateOrderRequest.cs
- modified: Program.cs (added service registration)
```

## Safety Rules

- Only reverts files touched by the targeted task, not the entire branch.
- Cannot undo across repos in a single operation -- one repo at a time.
- Cannot undo committed changes -- suggests `git revert` for committed work.
- Shows diff preview before any destructive operation.
- Requires confirmation unless `--force` is used.
- If a file was further modified after the task: warn and ask whether to proceed.

## Preview / Dry-Run Behavior

- `--preview` / `--dry-run`: Show exactly what would be reverted. No file changes, no task updates.
