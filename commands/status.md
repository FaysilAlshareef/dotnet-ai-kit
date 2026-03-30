---
description: "Shows current feature progress and phase. Use when checking where you are in the SDD lifecycle."
---

# Status

Display a progress dashboard for active features showing lifecycle stage, task completion per repo, and suggested next command.

## Usage

```
/dotnet-ai.status $ARGUMENTS
```

**Examples:**
- (no args) -- Show current/most recent active feature
- `001` -- Show status for feature 001 specifically
- `--all` -- Show all features (active and completed)
- `--verbose` -- Show detailed task-level breakdown

## Flags

| Flag | Description |
|------|-------------|
| `--all` | Show all features, not just the current one |
| `--dry-run` | Preview what status information would be gathered (no side effects) |
| `--verbose` | Show per-task details with file paths and timestamps |
| `--json` | Output status as JSON for tooling integration |

## Flow

### Step 1: Locate Features

Read `.dotnet-ai-kit/features/` directory for feature directories.
- Each feature directory follows the pattern: `{NNN}-{short-name}/`
- If `$ARGUMENTS` contains a feature ID: load that specific feature
- If `--all`: load all features
- If no args: find the most recently modified feature (active first)
- If no features found: report "No features found. Start with /dotnet-ai.specify" and stop.

### Step 2: Read Feature Artifacts

For each feature, check existence and content of:
- `spec.md` -- specification (exists = specified)
- `plan.md` -- implementation plan (exists = planned)
- `service-map.md` -- multi-repo service map (microservice mode)
- `tasks.md` -- task list with completion status
- `analysis.md` -- analysis findings
- `handoff.md` -- session handoff (checkpoint or wrap-up)
- `undo-log.md` -- undo history

### Step 2b: Detect Linked Features

Scan `.dotnet-ai-kit/briefs/` for all source repo subdirectories and their feature briefs. Display them separately from local features:

```
Linked Features (from other repos):
  [company-domain-command] 001-order-management   Phase: Tasks Generated | Tasks: 0/4
  [company-domain-command] 002-invoice-export      Phase: Planned
  [company-domain-gateway] 002-user-sync           Phase: Specified
```

If `--verbose`: show the full brief content. The `--all` flag should include both local and linked features.

### Step 3: Calculate Lifecycle Progress

Determine which lifecycle stages are complete, in-progress, or pending:

```
[x] Specified   -- spec.md exists and has no [NEEDS CLARIFICATION] markers
[x] Planned     -- plan.md exists
[x] Tasks       -- tasks.md exists with task count
[>] Implement   -- tasks.md has some completed tasks (show X/Y)
[ ] Review      -- no review report found
[ ] Verify      -- no verification report found
[ ] PR          -- no PR URLs recorded
```

Display format: `specify> plan> implement> review> verify> pr`
- Checkmark for completed stages
- Arrow `>` for current stage
- Circle `o` for pending stages

### Step 4: Calculate Per-Repo Status (microservice mode)

If `service-map.md` exists, show per-repo breakdown:
```
command      : 6/6 tasks done   branch: feature/001-orders
query        : 4/4 tasks done   branch: feature/001-orders
processor    : 2/4 tasks done   branch: feature/001-orders  <-- current
gateway      : 0/3 tasks done   not started
controlpanel : 0/1 tasks done   not started
```

For single-repo projects, show task completion by layer instead.

### Step 5: Suggest Next Command

Based on current state, suggest the most logical next action:

| State | Suggestion |
|-------|-----------|
| No spec | `/dotnet-ai.specify "description"` |
| Spec has clarification markers | `/dotnet-ai.clarify` |
| Spec complete, no plan | `/dotnet-ai.plan` |
| Plan exists, no tasks | `/dotnet-ai.tasks` |
| Tasks exist, none started | `/dotnet-ai.implement` |
| Tasks partially complete | `/dotnet-ai.implement --resume` |
| All tasks complete, no review | `/dotnet-ai.review` |
| Review done, not verified | `/dotnet-ai.verify` |
| Verified, no PR | `/dotnet-ai.pr` |
| PR created | `/dotnet-ai.wrap-up` |
| Handoff exists (checkpoint) | `/dotnet-ai.implement --resume` |

### Step 6: Show Handoff Context (if exists)

If `handoff.md` exists, show a brief summary:
- Session type (checkpoint or wrap-up)
- Last session date
- Blocked items or pending decisions
- Key context for resuming work

## Output Format

```
Feature: 001-order-management
Status:  IN PROGRESS (implementing)
Mode:    Microservice

Progress:
  [x] Specified  (spec.md)
  [x] Planned    (plan.md, service-map.md)
  [x] Tasks      (18 tasks generated)
  [>] Implement  (12/18 tasks complete)
  [ ] Review
  [ ] Verify
  [ ] PR

Next: /dotnet-ai.implement --resume    (continue from T013)
```

## Dry-Run / Preview Behavior

- `--dry-run`: Show which feature directories and files would be read. No side effects (status is already read-only, but this confirms the data sources).
