# Implementation Plan: Fix v1.0 Gap Report Issues

**Branch**: `010-fix-v1-gaps` | **Date**: 2026-03-25 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-fix-v1-gaps/spec.md`

## Summary

Fix 11 identified gaps in dotnet-ai-kit v1.0: add a `/dai.learn` command for project knowledge persistence, fix dead constitution references, resolve duplicate skill names, clean up unused models, implement extension hook execution and version validation, wire NamingConfig to template rendering, add missing knowledge docs (CQRS, DDD, Clean Arch, VSA), expand plugin manifest, standardize `--dry-run` flags, make service-map.md an explicit output, and add missing agent skill reference.

## Technical Context

**Language/Version**: Python 3.10+ (CLI tool), Markdown (commands/skills/agents/rules/knowledge)
**Primary Dependencies**: typer, pydantic v2, jinja2, rich, pyyaml, hatchling
**Storage**: YAML config files, Markdown knowledge files, JSON plugin manifest
**Testing**: pytest, pytest-cov
**Target Platform**: Windows, macOS, Linux (cross-platform)
**Project Type**: CLI tool + AI plugin (Claude Code)
**Performance Goals**: Constitution generation < 60 seconds (SC-001)
**Constraints**: Commands <= 200 lines, Skills <= 400 lines, Rules <= 100 lines
**Scale/Scope**: 27 commands, 106 skills, 13 agents, 9 rules, 15+ knowledge docs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Detect-First, Respect-Existing | PASS | `/dai.learn` chains `/dai.detect` — reuses detection, does not duplicate |
| II. Pattern Fidelity | PASS | No code generation changes — only knowledge capture and tool fixes |
| III. Architecture & Platform Agnostic | PASS | All changes are cross-platform (Python pathlib, Markdown files) |
| IV. Best Practices & Quality | PASS | Removes dead code, fixes bugs, adds documentation |
| V. Safety & Token Discipline | PASS | New command <= 200 lines, knowledge docs are reference material loaded on-demand |

**Result**: PASS — No violations. No entries needed in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/010-fix-v1-gaps/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
# Files CREATED (new)
commands/learn.md                              # FR-001: New /dai.learn command (27th)
knowledge/cqrs-patterns.md                     # FR-007: CQRS reference doc
knowledge/ddd-patterns.md                      # FR-007: DDD reference doc
knowledge/clean-architecture-patterns.md       # FR-007: Clean Architecture reference doc
knowledge/vsa-patterns.md                      # FR-007: VSA reference doc
knowledge/modular-monolith-patterns.md         # FR-007: Modular Monolith reference doc

# Files MODIFIED
commands/plan.md                               # FR-002: Wire constitution check to .dotnet-ai-kit/memory/constitution.md
commands/specify.md                            # FR-010: Add service-map.md as explicit microservice output
commands/add-aggregate.md                      # FR-009: --preview → --dry-run
commands/add-entity.md                         # FR-009: --preview → --dry-run
commands/add-event.md                          # FR-009: --preview → --dry-run
commands/add-endpoint.md                       # FR-009: --preview → --dry-run
commands/add-page.md                           # FR-009: --preview → --dry-run
commands/add-crud.md                           # FR-009: --preview → --dry-run
commands/add-tests.md                          # FR-009: --preview → --dry-run
commands/docs.md                               # FR-009: --preview → --dry-run
commands/checkpoint.md                         # FR-009: --preview → --dry-run (keep as primary)
commands/undo.md                               # FR-009: --preview → --dry-run (keep as primary)
commands/wrap-up.md                            # FR-009: --preview → --dry-run (keep as primary)
commands/explain.md                            # FR-009: --preview → --dry-run
skills/api/controller-patterns/SKILL.md        # FR-003: Rename to unique name
skills/workflow/plan-templates/SKILL.md        # FR-002: Update Constitution Check section
src/dotnet_ai_kit/models.py                    # FR-004: Remove CodeRabbitConfig/IntegrationsConfig
src/dotnet_ai_kit/copier.py                    # FR-006: Wire NamingConfig to template context
src/dotnet_ai_kit/extensions.py                # FR-005: Add hook execution + version check
agents/controlpanel-architect.md               # FR-011: Verified — response-result already listed
.claude-plugin/plugin.json                     # FR-008: Expand with full command/skill/agent catalog
planning/12-version-roadmap.md                 # Update: reflect new command count (27), knowledge docs (15+)
CLAUDE.md                                      # Update: command count 26→27, add /dai.learn row

# Files MODIFIED (tests)
tests/test_extensions.py                       # FR-005: Add hook execution + version check tests
tests/test_copier.py                           # FR-006: Add NamingConfig wiring tests
tests/test_cli.py                              # FR-004: Update for removed models
```

**Structure Decision**: No new directories needed. All changes fit existing project structure. Knowledge docs go in `knowledge/`, new command goes in `commands/`, Python changes in `src/dotnet_ai_kit/`.

## Complexity Tracking

> No constitution violations — table not needed.
