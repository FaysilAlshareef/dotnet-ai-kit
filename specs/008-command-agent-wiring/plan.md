# Implementation Plan: Wire All Commands to Appropriate Agents and Skills

**Branch**: `008-command-agent-wiring` | **Date**: 2026-03-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-command-agent-wiring/spec.md`

## Summary

Update all 26 command markdown files to properly load the correct specialist agents (13 total) and skills (106 total) based on project type and task type. Also fix agent skill path references to match actual file paths. This is a markdown-only change — no Python code modifications needed.

## Technical Context

**Language/Version**: Markdown (command templates read by AI tools)
**Primary Dependencies**: None (pure markdown editing)
**Storage**: Filesystem (markdown files in `commands/`, `agents/`, `skills/`)
**Testing**: Manual verification (file existence checks, line count checks)
**Target Platform**: Cross-platform (Windows, macOS, Linux)
**Project Type**: CLI tool plugin (AI-assisted development)
**Performance Goals**: N/A
**Constraints**: Commands <= 200 lines per file (token budget)
**Scale/Scope**: 26 commands, 13 agents, 106 skills

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Detect-First, Respect-Existing | PASS | Only modifying command templates; not changing existing code patterns |
| II. Pattern Fidelity | PASS | Following the agent-loading pattern already established in implement.md |
| III. Architecture & Platform Agnostic | PASS | No OS-specific changes; pure markdown |
| IV. Best Practices & Quality | PASS | Adding specialist guidance improves generated code quality |
| V. Safety & Token Discipline | PASS | Commands must stay under 200 lines; skills loaded on-demand |

No violations. Complexity Tracking not needed.

## Project Structure

### Documentation (this feature)

```text
specs/008-command-agent-wiring/
├── plan.md              # This file
├── research.md          # Agent-command routing matrix
├── data-model.md        # Agent/skill/command relationship model
├── quickstart.md        # Implementation guide
└── tasks.md             # Task breakdown (created by /speckit.tasks)
```

### Source Code (repository root)

```text
commands/                    # 17 commands modified (7 code-gen + 1 implement + 6 lifecycle + 3 skill fixes)
├── add-aggregate.md         # Modified: add agent loading
├── add-crud.md              # Modified: add agent loading
├── add-endpoint.md          # Modified: add agent loading
├── add-entity.md            # Modified: add agent loading
├── add-event.md             # Modified: add agent loading
├── add-page.md              # Modified: add agent loading
├── add-tests.md             # Modified: add agent loading
├── implement.md             # Modified: expand agent routing to all 13
├── review.md                # Modified: add agent loading
├── docs.md                  # Modified: add agent loading
├── verify.md                # Modified: add agent loading
├── analyze.md               # Modified: add agent loading
├── plan.md                  # Modified: add agent loading
├── tasks.md                 # Modified: add agent loading
├── specify.md               # Modified: add agent loading
└── clarify.md               # Modified: add agent loading

agents/                      # Up to 13 agents potentially modified (fix skill paths)
├── command-architect.md     # May fix: skill path shorthand → full paths
├── cosmos-architect.md      # May fix: skill path shorthand → full paths
├── docs-engineer.md         # Fix: skill path mismatches
├── ...                      # Other agents as needed

commands/ (unchanged)        # 9 utility commands NOT modified
├── checkpoint.md
├── configure.md
├── detect.md
├── explain.md
├── init.md
├── pr.md
├── status.md
├── undo.md
└── wrap-up.md
```

**Structure Decision**: All changes are within the existing `commands/` and `agents/` directories. No new directories or files created.
