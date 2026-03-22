---
description: "One-command feature builder that chains the full SDD lifecycle automatically"
---

# /dotnet-ai.do — One-Command Feature Builder

You are an AI coding assistant executing the `/dotnet-ai.do` command.
Your job is to take a natural-language feature description and execute the full lifecycle
from specification to pull request, pausing only when necessary.

## Input

```
/dotnet-ai.do "feature description"
```

Flags: `--dry-run` (specify + plan only), `--verbose` (diagnostic output),
       `--no-pr` (skip PR creation), `--no-review` (skip review and verify steps)

## Step 1: Initialize

1. Read `.dotnet-ai-kit/config.yml` — if missing, prompt: "Run /dotnet-ai.configure first."
2. Detect project mode: **generic** (single repo) or **microservice** (multi-repo).
3. Parse `$ARGUMENTS` as the feature description.
4. If no description provided: "Usage: /dotnet-ai.do \"Add order management\""
5. Print: "Starting: {description}"

## Step 2: Specify (Step 1/6)

Print: "Step 1/6: Generating specification..."

1. Generate feature directory: `.dotnet-ai-kit/features/{NNN}-{short-name}/`
2. Create `spec.md` from the description — same logic as `/dotnet-ai.specify`.
3. Auto-detect affected repos (microservice mode) or layers (generic mode).
4. Scan for ambiguities and `[NEEDS CLARIFICATION]` markers.

## Step 3: Quick Clarify (inline)

If ambiguities are found in the spec:

1. Print: "Found {N} ambiguities. Quick clarification needed:"
2. Ask a **maximum of 3** questions, presented inline one at a time.
3. After each answer, update `spec.md` immediately.
4. Remove resolved `[NEEDS CLARIFICATION]` markers.
5. If more than 3 ambiguities remain, note them in spec and continue.

If no ambiguities: skip silently.

## Step 4: Plan (Step 2/6)

Print: "Step 2/6: Planning implementation..."

1. Generate `plan.md` — same logic as `/dotnet-ai.plan`.
2. For microservice mode: generate `service-map.md` and `event-flow.md`.
3. Generate `tasks.md` — same logic as `/dotnet-ai.tasks`.
4. Count total tasks and affected repos.

### Complexity Check — Pause Decision

Evaluate complexity:
- **Simple**: 1 repo AND fewer than 10 tasks
- **Complex**: multi-repo OR 10+ tasks

If **simple**:
- Print plan summary (repos, task count, estimated files).
- Continue automatically — no pause.

If **complex**:
- Print detailed plan summary with per-repo breakdown.
- Ask: "This feature affects {N} repos with {M} tasks. Proceed? [Y/n]"
- On `n`: stop, preserve spec and plan. User can edit and re-run.
- On `Y` or Enter: continue.

If `--dry-run`: print the plan summary and stop here.
Print: "[DRY-RUN] Specification and plan generated. No implementation performed."

## Step 5: Implement (Step 3/6)

Print: "Step 3/6: Implementing... (T001/T{total})"

1. Execute all tasks — same logic as `/dotnet-ai.implement`.
2. Update progress display as each task completes:
   "Step 3/6: Implementing... (T{current}/T{total})"
3. Run `dotnet build` after each layer/repo group.
4. Run `dotnet test` after all tasks per repo.
5. On failure: stop, report error, preserve progress.
   User can fix and run `/dotnet-ai.implement --resume`.

## Step 6: Review + Verify (Step 4/6)

If `--no-review` is set, skip to Step 7.

Print: "Step 4/6: Reviewing and verifying..."

1. Run standards review — same logic as `/dotnet-ai.review`.
2. Run verification pipeline — same logic as `/dotnet-ai.verify`.
3. If CRITICAL review findings:
   - Print findings with suggested fixes.
   - Ask: "Critical issues found. Auto-fix safe issues? [Y/n]"
   - Apply safe auto-fixes if approved.
4. Report summary: review pass/fail, test results per repo.

## Step 7: PR (Step 5/6)

If `--no-pr` is set, skip to Step 8.

Print: "Step 5/6: Creating pull request(s)..."

1. Create PR(s) — same logic as `/dotnet-ai.pr`.
2. For multi-repo: create linked PRs in each affected repo.
3. Collect all PR URLs.

## Step 8: Report (Step 6/6)

Print the final summary:

```
Feature complete: {NNN}-{short-name}

  Specification:  Generated (spec.md)
  Clarifications: {N resolved, M remaining}
  Plan:           {task count} tasks across {repo count} repo(s)
  Implementation: {completed}/{total} tasks
  Build:          {PASS/FAIL}
  Tests:          {PASS/FAIL} ({passed}/{total})
  Review:         {PASS/WARN/SKIPPED}
  PR:             {PR URLs or SKIPPED}

  Files created:  {N}
  Files modified: {N}
  Duration:       {elapsed time}
```

## Smart Behavior Summary

| Condition | Behavior |
|-----------|----------|
| Simple feature (1 repo, <10 tasks) | Fully automatic, no pauses |
| Complex feature (multi-repo or 10+ tasks) | Pauses after plan for confirmation |
| Ambiguities in spec | Asks max 3 clarifying questions inline |
| `--dry-run` | Runs specify + plan only, shows preview |
| `--no-pr` | Everything except PR creation |
| `--no-review` | Skips review and verify steps |
| Build failure | Stops, reports error, preserves progress |
| No config | Prompts for `/dotnet-ai.configure` |

## Progress Display

Throughout execution, show a running status line:
```
Step {N}/6: {phase}... ({detail})
```

Phases: Specifying, Planning, Implementing, Reviewing, Creating PR, Done.

For implementation, show task progress: `(T005/T012)`
For multi-repo, show repo context: `(query: T005/T012)`

## Error Recovery

- **Spec failure**: report error, no files created.
- **Plan failure**: preserve spec, report error.
- **Implementation failure**: preserve completed tasks, report error and failing task.
  User can fix and run `/dotnet-ai.implement --resume`.
- **Review failure**: implementation is complete; report findings for manual fix.
- **PR failure**: implementation and review complete; user can run `/dotnet-ai.pr` manually.

Each phase is independent — failure in a later phase does not undo earlier work.

## Dry-Run Behavior

When `--dry-run` is active:
- Run specify and plan phases only.
- Print full plan summary with task list and file estimates.
- Do NOT implement, review, or create PRs.
- Prefix output with `[DRY-RUN]`.
