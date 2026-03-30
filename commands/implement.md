---
description: "Executes all planned implementation tasks. Use when ready to generate code from the task list."
---

# /dotnet-ai.implement — Execute Implementation

You are an AI coding assistant executing the `/dotnet-ai.implement` command.
Your job is to implement the tasks defined in tasks.md, writing real code.

## Input

Flags: `--dry-run` (preview without writing), `--verbose` (diagnostic output),
       `--resume` (continue from last incomplete/failed task)

## Step 1: Check Prerequisites

1. Find the active feature in `.dotnet-ai-kit/features/`.
2. Verify required artifacts exist:
   - `tasks.md` — required. If missing: "No tasks found. Run /dotnet-ai.tasks first."
   - `plan.md` — required for implementation guidance.
   - `spec.md` — required for acceptance criteria.
3. Check for `analysis.md` — if exists, warn about any CRITICAL findings.
   Do NOT block; inform the user and let them decide.
4. Detect mode: **generic** or **microservice**.
5. If no `.dotnet-ai-kit/config.yml`: prompt to run `/dotnet-ai.configure` first.

## Step 2: Load Skills on Demand

**Always load** (regardless of task type):
- `skills/core/configuration/SKILL.md` — Options pattern, DI registration, ValidateOnStart
- `skills/core/dependency-injection/SKILL.md` — Service lifetime, registration patterns

Load skills based on the tasks being implemented:
- Read `skills/workflow/sdd-lifecycle/SKILL.md` for lifecycle patterns
- Per task type, load the relevant skill:
  - Aggregate tasks: `skills/microservice/command/aggregate-design/SKILL.md`
  - Event tasks: `skills/microservice/command/event-design/SKILL.md`
  - Entity tasks: `skills/microservice/query/query-entity/SKILL.md`
  - Handler tasks: `skills/microservice/query/event-handler/SKILL.md`
  - Endpoint tasks: `skills/microservice/gateway/gateway-endpoint/SKILL.md`
  - Page tasks: `skills/microservice/controlpanel/blazor-component/SKILL.md`
  - Test tasks: `skills/testing/unit-testing/SKILL.md`
  - Generic API: `skills/api/minimal-api/SKILL.md`
  - Generic data: `skills/data/ef-core-basics/SKILL.md`
  - Generic CQRS: `skills/cqrs/mediatr-handlers/SKILL.md`

## Step 2b: Load Specialist Agent

Based on the project's detected `project_type`, read the specialist agent for architectural guidance:
- command → Read `agents/command-architect.md`
- query-sql → Read `agents/query-architect.md`
- query-cosmos → Read `agents/cosmos-architect.md`
- processor → Read `agents/processor-architect.md`
- gateway → Read `agents/gateway-architect.md`
- controlpanel → Read `agents/controlpanel-architect.md`
- hybrid → Read both `agents/command-architect.md` and `agents/query-architect.md`
- vsa, clean-arch, ddd, modular-monolith, generic → Read `agents/dotnet-architect.md`

## Step 2c: Load Task-Specific Secondary Agent

Based on the current task's domain, also load a secondary specialist agent:
- API/endpoint tasks → Read `agents/api-designer.md`
- Entity/data/EF tasks → Read `agents/ef-specialist.md`
- Test tasks → Read `agents/test-engineer.md`
- DevOps/Docker/CI tasks → Read `agents/devops-engineer.md`
- Documentation tasks → Read `agents/docs-engineer.md`
- Review tasks → Read `agents/reviewer.md`

Load all skills listed in the secondary agent's Skills Loaded section.

## Step 3: Resume Logic

If `--resume` flag is set:
1. Read `tasks.md` and find the first unchecked task `- [ ]`.
2. Check `undo-log.md` for the last failed task — show the error.
3. Skip all tasks marked `- [x]` (already complete).
4. Print: "Resuming from T{NNN}: {task description}"

If NOT resuming:
1. Verify no tasks are already checked (fresh start).
2. If tasks are partially complete without `--resume`: ask "Tasks partially complete. Use --resume to continue, or reset?"

## Step 4: Execute Tasks (Generic Mode)

1. Create feature branch: `feature/{NNN}-{short-name}`
   - If branch exists (resume), switch to it.
2. For each task in order (respecting dependencies):
   a. Print: "T{NNN}: {description}"
   b. Read the plan for implementation guidance.
   c. Scan existing code for patterns to follow (detect-first).
   d. Generate code following detected conventions.
   e. Write files to the specified paths.
   f. Log the action to `undo-log.md`:
      ```
      ## T{NNN} - {description}
      - created: {file path}
      - modified: {file path} (added {what})
      ```
   g. Mark task complete in tasks.md: `- [x] T{NNN} ...`
3. After each layer (Domain, Application, Infrastructure, API):
   - Run `dotnet build` — if it fails, stop and report the error.
4. After all tasks: run `dotnet test`.
5. If a task fails: stop, report error, suggest fix. User can fix and `--resume`.

## Step 5: Execute Tasks (Microservice Mode)

### 5a: Resolve Repos

1. Read repo paths from `config.yml` and per-feature overrides in `plan.md`.
2. For each repo in `service-map.md`:
   - If local path exists and is a git repo: use it directly.
   - If path is a GitHub URL (`github:org/repo`): clone via `gh repo clone {org/repo} repos/{local-name}`.
   - If path is null: prompt user for clone URL or local path.
3. Verify each resolved repo has a valid `.sln`, `.slnx`, or `.csproj`.
4. After cloning via `github:org/repo`, update `config.yml` with the resolved local path so future runs don't re-clone.
5. For each secondary repo, check for `.dotnet-ai-kit/briefs/{source-repo-name}/{NNN}-{name}/feature-brief.md`. If exists: load for context. If missing (just cloned): project the brief now from primary spec/plan/tasks.

### 5b: Branch and Execute in Dependency Order

Execution order: `command -> query/processor (parallel) -> gateway -> controlpanel`

For each repo in dependency order:

1. `cd` into the repo directory.
2. Create feature branch: `git checkout -b feature/{NNN}-{feature-name}`
   - If branch exists (resume): `git checkout feature/{NNN}-{feature-name}`
3. Execute tasks tagged for this repo (respecting `[depends:]` and `[P]` markers).
4. After each task group: run `dotnet build` in the repo root.
   - On build failure: stop this repo, mark remaining tasks as `- [B] T{NNN}` (blocked).
5. After all tasks for this repo: run `dotnet test`.
6. Mark tasks complete in the shared `tasks.md` with repo context.
7. Log actions to `undo-log.md` with `**Repo**: {repo-name}`.
8. Update the secondary repo's `feature-brief.md`: mark completed tasks as `- [x]`, update phase to "Implementing". When all tasks done: phase "Implemented". On failure: phase "Blocked — T{NNN} failed: {error}". Auto-commit with `chore: update feature brief {NNN}-{name} — {phase}`. Skip auto-commit if repo has uncommitted changes.

Query and Processor repos may execute in parallel after Command completes.
Gateway waits for Query (needs proto definitions). ControlPanel waits for Gateway.

### 5c: Cross-Repo Progress Tracking

Update `tasks.md` with per-repo status after each repo completes:

```
## Progress
- command:      6/6 tasks DONE
- query:        4/4 tasks DONE
- processor:    2/4 tasks (T009 FAILED)
- gateway:      0/3 tasks BLOCKED
- controlpanel: 0/1 tasks BLOCKED
```

### 5d: Partial Failure Handling

When a task or build fails in a repo:

1. **Stop** execution for that repo immediately.
2. **Mark** the failed task in tasks.md: `- [!] T{NNN} FAILED: {error summary}`
3. **Mark** all downstream tasks as blocked: `- [B] T{NNN} BLOCKED by T{failed}`
4. **Preserve** the feature branch in the failed repo (do not delete or reset).
5. **Continue?** If the failed repo is not a dependency for remaining repos, ask:
   "Repo {name} failed. Skip and continue with independent repos? [Y/n]"
   Otherwise, stop all execution.
6. **Record** the failure context in `undo-log.md` for debugging.
7. User can fix the issue and run `/dotnet-ai.implement --resume`.

Read `skills/workflow/multi-repo-workflow/SKILL.md` for orchestration patterns.

## Step 6: Undo Log

For every file created or modified, record in `undo-log.md` with task ID, repo name, timestamp, and action (created/modified) per file.

## Step 7: Completion Report

Report: tasks completed/total, files created/modified, build status, test results. For microservice mode, include per-repo summary. Suggest next: `/dotnet-ai.review` or `/dotnet-ai.verify`.

## Dry-Run Behavior

When `--dry-run`: print tasks and files that WOULD be created/modified, show file counts per repo. Do NOT write code, create branches, run builds, or modify tasks.md. Prefix with `[DRY-RUN]`.

## Error Handling

- Build failure: stop, show error, suggest fix, user can `--resume`
- Test failure: report failing tests, continue if `--verbose`
- Missing repo: prompt for clone URL or local path
- Task dependency not met: skip, report "Blocked by T{N}"
