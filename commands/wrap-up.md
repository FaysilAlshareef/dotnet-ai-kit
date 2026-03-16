---
description: "End session with comprehensive commits, handoff document, and session summary"
---

# Wrap Up

Full session close -- commit all pending changes, write a comprehensive handoff with decisions and deviations, extract learnings, and report a session summary. Use when done for the day.

## Usage

```
/dotnet-ai.wrap-up $ARGUMENTS
```

**Examples:**
- (no args) -- End session, commit changes, write handoff
- `--no-commit` -- Write handoff without committing changes
- `--preview` -- Show what would be committed and written
- `--dry-run` -- Same as `--preview`
- `--verbose` -- Show detailed commit diffs and full handoff content

## Flags

| Flag | Description |
|------|-------------|
| `--no-commit` | Write handoff only, do not commit changes |
| `--preview` | Show what would be committed and written, no side effects |
| `--dry-run` | Same as `--preview` |
| `--verbose` | Show detailed diffs and full handoff content |

## Flow

### Step 1: Detect Active Feature

Read `.dotnet-ai-kit/features/` for the current active feature.
- Load `spec.md`, `plan.md`, `tasks.md` for context.
- Determine which tasks were completed this session vs previously.

### Step 2: Scan All Repos for Pending Changes

For each repo (or current directory for single-repo):
- Run `git status` to detect uncommitted changes.
- Run `git log` to identify commits made this session (since last handoff or branch creation).
- Categorize: new files, modified files, deleted files.

### Step 3: Commit All Pending Changes (per repo)

For each repo with uncommitted changes (unless `--no-commit`):
1. Stage relevant files (exclude build artifacts, `.vs/`, `bin/`, `obj/`).
2. Create descriptive commit:
   ```
   wrap-up: {feature-name} session complete

   Completed: T006-T010
   Remaining: T011-T015
   ```
3. Commit changes.

### Step 4: Write Comprehensive Handoff

Write `.dotnet-ai-kit/features/{NNN}-{short-name}/handoff.md`:

```markdown
# Handoff - Wrap Up

session_type: wrap-up
timestamp: {ISO 8601}
feature: {NNN}-{short-name}

## Session Summary
- Duration context: {start reference if available}
- Tasks completed this session: {count}
- Total progress: {X}/{Y} tasks ({percentage}%)

## Completed Tasks
- T006: Add GetOrders endpoint [gateway] -- new controller with list+get
- T007: Create Orders page [controlpanel] -- MudDataGrid with filters

## Remaining Tasks
- T011: Add OrderUpdated event handler [query]
- T012: Integration tests for gateway [gateway]

## Decisions Made
- Used cursor-based pagination for Orders list (matches existing Products pattern)
- Skipped soft-delete for Orders (spec says hard delete is acceptable)

## Deviations from Plan
- T008 split into T008a (controller) and T008b (models) due to complexity
- Added extra validation in Create handler not in original spec

## Blocked Items
- T013 blocked: waiting for proto changes in command repo to be merged

## Learnings
- Order aggregate needs CompletedAt timestamp (discovered during implementation)
- Gateway auth policy for orders should match products policy

## Repos Status
| Repo | Branch | Commits | Status |
|------|--------|---------|--------|
| command | feature/001-orders | 3 commits | complete |
| query | feature/001-orders | 2 commits | complete |
| gateway | feature/001-orders | 2 commits | in progress |
| controlpanel | feature/001-orders | 1 commit | in progress |

## Resume Instructions
1. Run /dotnet-ai.status 001 to see current state
2. Run /dotnet-ai.implement --resume to continue from T011
3. Review blocked items above before proceeding
```

### Step 5: Report Session Summary

```
Session wrapped up.

Commits:
  gateway      : "wrap-up: order-management session" (6 files)
  controlpanel : "wrap-up: order-management session" (4 files)

Progress: 10/15 tasks complete (67%)

Handoff: .dotnet-ai-kit/features/001-orders/handoff.md

To resume: /dotnet-ai.status 001
```

## When to Use

- End of day or end of work session
- Before a long break (overnight, weekend)
- When handing off to another developer or AI session
- When switching to a different feature for an extended period

For quick mid-session saves, use `/dotnet-ai.checkpoint` instead (lighter weight).

## Preview / Dry-Run Behavior

- `--preview` / `--dry-run`: Show per-repo changes, proposed commits, and full handoff content. No commits, no writes.
