---
description: "Analyzes plan consistency before coding. Use when validating spec-plan-task alignment."
---

# /dotnet-ai.analyze — Consistency Check

You are an AI coding assistant executing the `/dotnet-ai.analyze` command.
This command is **READ-ONLY** except for writing `analysis.md` (the report). You MUST NOT modify any other files.

## Usage

```
/dotnet-ai.analyze $ARGUMENTS
```

**Examples:**
- (no args) — Analyze current feature against spec/plan/tasks
- `--verbose` — Show detailed check output per pass

## Input

Flags: `--dry-run` (preview analysis scope), `--verbose` (diagnostic output),
       `--severity {level}` (filter output: critical, high, medium, low)

## Load Specialist Agent

Based on the detected project type, read the specialist agent for architectural guidance:
- **Microservice mode**:
  - command → Read `agents/command-architect.md`
  - query-sql → Read `agents/query-architect.md`
  - query-cosmos → Read `agents/cosmos-architect.md`
  - processor → Read `agents/processor-architect.md`
  - gateway → Read `agents/gateway-architect.md`
  - controlpanel → Read `agents/controlpanel-architect.md`
  - hybrid → Read both `agents/command-architect.md` and `agents/query-architect.md`
- **Generic mode** (VSA, Clean Arch, DDD, Modular Monolith):
  - Read `agents/dotnet-architect.md`

Load all skills listed in the agent's Skills Loaded section.

## Step 1: Load All Artifacts

1. Find the active feature in `.dotnet-ai-kit/features/`.
2. Load all available artifacts from the feature directory:
   - `spec.md` — user stories, requirements, entities
   - `plan.md` — implementation design, layer/service breakdown
   - `tasks.md` — task list with file paths and dependencies
   - `service-map.md` — service dependencies (microservice mode)
   - `event-flow.md` — event definitions and flow (microservice mode)
   - `contracts/` — proto and API contracts (microservice mode)
3. Detect mode: **generic** or **microservice**.
4. If microservice mode: resolve repo paths from `config.yml` / `service-map.md`.
   For each repo, verify the directory exists and is accessible (read-only).
5. If `--verbose`, print: "Loaded {N} artifacts. Mode: {mode}. Repos: {list}"

## Step 2: Load Skills

- Read `skills/quality/architectural-fitness/SKILL.md` for architecture analysis
- Read `skills/quality/code-analysis/SKILL.md` for code analysis patterns
- Microservice: Read `skills/microservice/command/event-design/SKILL.md`
- Microservice: Read `skills/workflow/multi-repo-workflow/SKILL.md` for cross-repo patterns

## Step 3: Run Analysis Passes

### Generic .NET Passes (always run)

**Pass 1: Architecture Consistency**
- Layer boundaries respected: no Domain → Infrastructure references
- Dependencies flow inward: API → Application → Domain (not reversed)
- No circular dependencies between layers
- Severity: CRITICAL if boundary violated, HIGH if questionable

**Pass 2: Naming Consistency**
- Same entity/concept name used in spec, plan, and tasks
- Naming follows detected project conventions (PascalCase, suffixes)
- No conflicting names for the same concept
- Severity: MEDIUM for inconsistencies, LOW for style deviations

**Pass 3: Coverage Gaps**
- Every requirement has a task; every task traces to a requirement (no orphans either direction)
- Severity: HIGH for missing tasks, MEDIUM for missing traceability

**Pass 4: Concurrency**
- Entities updated concurrently have row version/concurrency tokens; aggregate roots have concurrency handling.
- Severity: HIGH if missing for shared entities, MEDIUM otherwise

### Microservice Passes (in addition to above)

These passes inspect both feature artifacts AND actual code across repos listed in
`config.yml` / `service-map.md`. Read each repo directory as needed (read-only).

**Pass 5: Event Consistency**
- Scan command repo for published events, query repo for handlers, processor repo for routing.
- CRITICAL if event has zero handlers; HIGH if event schema mismatches handler expected fields.

**Pass 6: Proto Consistency**
- Collect `.proto` files from command and query repos (server definitions).
- Collect `.proto` files from gateway repo (client definitions).
- Compare message names, field names, field numbers, and types.
- Verify each gateway gRPC client has a matching server service definition.
- Severity: CRITICAL for missing or mismatched request/response contracts.

**Pass 7: Cross-Repo Dependencies**
- Read `appsettings.json` / K8s manifests in each repo for service URLs and topic names.
- Verify service bus topic names in command publisher match processor listener config.
- Verify gRPC service addresses in gateway match query/command service addresses.
- Check dependency order in tasks.md matches `service-map.md`.
- Severity: HIGH for URL/topic mismatches, MEDIUM for missing config entries.

**Pass 8: Event Version Compatibility**
- If events use version suffixes (e.g., `OrderCreatedV2`), verify handlers exist
  for each version still in circulation.
- Check that new event versions do not remove required fields (breaking change).
- Verify processor routing handles both old and new event versions during migration.
- Severity: HIGH for breaking changes, MEDIUM for missing version handlers.

**Pass 9: Sequence Gaps**
- Trace the full event flow: command publishes -> query/processor handles -> any
  downstream publish -> next handler. Verify no dead ends or missing links.
- Severity: HIGH for broken chains.

**Pass 10: Idempotency**
- Commands that create resources use client-provided IDs.
- Event handlers are idempotent (sequence-based dedup in query, client-sent ID in command).
- Severity: MEDIUM for missing idempotency.

**Pass 11: Brief Consistency** (microservice mode)
- For each secondary repo reachable via `config.yml`, scan `.dotnet-ai-kit/briefs/{source-repo-name}/{NNN}-{name}/feature-brief.md`.
- Verify brief matches current spec/plan/tasks: events, required changes, task list.
- Severity: HIGH for stale briefs (spec changed after projection), MEDIUM for minor drift.

## Step 4: Compile Report

Maximum 50 findings. If more found, keep the highest severity and note "N additional findings suppressed."

Apply `--severity` filter if provided (show only findings at or above that level).

Save report to `analysis.md` in the feature directory:

```markdown
# Analysis Report: {Feature Name}

**Feature**: {NNN}-{short-name} | **Mode**: {mode}
**Date**: {DATE} | **Findings**: {total}

## Summary
- CRITICAL: {count}
- HIGH: {count}
- MEDIUM: {count}
- LOW: {count}

## Findings

### [{severity}] {pass-name}: {brief description}
**Location**: {file or artifact reference}
**Details**: {explanation}
**Suggested Fix**: {what to do}

...
```

## Step 5: Report to User

```
Analysis complete for {NNN}-{short-name}.
  CRITICAL: {N}  HIGH: {N}  MEDIUM: {N}  LOW: {N}

{If CRITICAL > 0}:
  CRITICAL issues found. Review analysis.md before implementing.
  Consider: /dotnet-ai.plan (revise approach) or fix manually.

{If CRITICAL == 0}:
  No blocking issues. Ready to implement.

Next: /dotnet-ai.implement
```

## IMPORTANT: Read-Only Constraint

This command MUST NOT:
- Modify spec.md, plan.md, tasks.md, or any other file
- Create files other than analysis.md (the report)
- Execute any build, test, or git commands
- Suggest auto-fixes that change files (only suggest, never apply)

## Dry-Run Behavior

When `--dry-run` is active:
- Print which passes WOULD run based on detected mode
- Print artifact paths that WOULD be analyzed
- Do NOT run any analysis passes
- Prefix output with `[DRY-RUN]`

## Error Handling

- Missing artifacts: skip related passes, note in report as "SKIPPED: {reason}"
- Missing spec: "Cannot analyze. Run /dotnet-ai.specify first."
- Missing plan: "Cannot analyze fully. Run /dotnet-ai.plan first."
