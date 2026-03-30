---
description: "Generates an implementation plan from the spec. Use when ready to design the technical approach."
---

# /dotnet-ai.plan — Implementation Planning

You are an AI coding assistant executing the `/dotnet-ai.plan` command.
Your job is to create a detailed implementation plan from an existing feature spec.

## Input

Flags: `--dry-run` (preview without writing), `--verbose` (diagnostic output)

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

## Step 1: Load Prerequisites

1. Find the active feature in `.dotnet-ai-kit/features/` (most recent or in-progress).
2. Load `spec.md` — required. If missing: "No spec found. Run /dotnet-ai.specify first."
3. Load `.dotnet-ai-kit/config.yml` if it exists.
4. Note any remaining `[NEEDS CLARIFICATION]` markers — warn but do not block.
5. If `--verbose`, print loaded artifacts and detected mode.

## Step 2: Detect Project Mode

1. From config or spec content, determine: **generic** or **microservice**.
2. Load skills on demand based on mode:
   - Always: `skills/workflow/sdd-lifecycle/SKILL.md`
   - Generic: `skills/architecture/clean-architecture/SKILL.md` or VSA skill
   - Microservice: `skills/workflow/multi-repo-workflow/SKILL.md`

## Step 3: Constitution Check Gate

If `.dotnet-ai-kit/memory/constitution.md` does not exist, skip this gate with a warning: "Project constitution not found — run /dai.learn to generate." Continue to Phase 0.

Read `.dotnet-ai-kit/memory/constitution.md` and verify compliance:
- Detect-First: plan must research existing code before proposing changes
- Pattern Fidelity: plan must follow detected conventions
- Architecture Agnostic: plan must match the project's architecture

Document result in `## Constitution Check`. Violations go to `## Complexity Tracking`.

## Step 4: Complexity Analysis

Analyze spec for feature complexity:

| Indicator | Threshold | Weight |
|-----------|-----------|--------|
| Entities / data models | >= 3 | High |
| External service integrations | >= 1 | High |
| Multi-repo (spans services) | Yes | High |
| Functional requirements | >= 5 | Medium |
| Data migrations / state transitions | Yes | Medium |

- **Complex** (any HIGH met): generate full artifacts (research.md, data-model.md, contracts/, quickstart.md)
- **Simple** (no HIGH met): generate plan.md only

## Step 5: Research Phase

Scan existing codebase for: folder structure, naming conventions, entities, handlers,
NuGet packages, DI patterns, test frameworks. If `--verbose`, print discoveries.

## Step 6: Generate Plan

Load `skills/workflow/plan-templates/SKILL.md` for mode-specific plan structure.

## Step 7: Generate Supporting Artifacts (Complex Only)

Load `skills/workflow/plan-artifacts/SKILL.md` for research.md, data-model.md,
contracts/, and quickstart.md generation guidance.

## Step 7b: Update Projected Briefs (microservice mode)

For each secondary repo with an existing brief in `.dotnet-ai-kit/briefs/{source-repo-name}/{NNN}-{name}/`:
1. Append or update "Implementation Approach" section with architecture decisions relevant to that repo.
2. Update "Required Changes" with technical approach from plan.md.
3. If `data-model.md` was generated, include relevant entity details for that repo.
4. Update phase to "Planned". If brief doesn't exist yet (repo cloned after specify), create it now with all available info.

Auto-commit with `chore: update feature brief {NNN}-{name} — planned`. Skip auto-commit if repo has uncommitted changes.

## Step 8: Report

```
Plan generated for {NNN}-{short-name}.
Mode: {generic|microservice} | Complexity: {simple|complex}
Constitution: {PASS|FAIL with count}

Artifacts created:
- plan.md
{if complex:} research.md, data-model.md, quickstart.md, contracts/
{if microservice:} service-map.md, event-flow.md

Next: /dotnet-ai.tasks or /dotnet-ai.analyze
```

## Dry-Run Behavior

When `--dry-run`: print plan content, show file paths, do NOT write files, prefix `[DRY-RUN]`.

## Error Handling

- Missing spec: direct to `/dotnet-ai.specify`
- Missing config: proceed with auto-detection, warn user
- Constitution violations: document but do not block
