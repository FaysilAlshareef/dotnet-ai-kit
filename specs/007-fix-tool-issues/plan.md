# Implementation Plan: Fix All 25 Identified Tool Issues

**Branch**: `007-fix-tool-issues` | **Date**: 2026-03-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-fix-tool-issues/spec.md`

## Summary

Fix 25 identified issues across the dotnet-ai-kit tool: critical bugs in config template and hooks, missing skill/agent copying during init, missing architectural enforcement in commands (Options pattern, command-side entity prevention, agent loading), feature numbering fixes, extension system robustness, and new rules/skills for configuration and testing patterns.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: typer, pydantic v2, jinja2, rich, pyyaml, hatchling
**Storage**: YAML config files, Markdown templates (filesystem only)
**Testing**: pytest, pytest-cov
**Target Platform**: Windows, macOS, Linux (cross-platform CLI)
**Project Type**: CLI tool + AI plugin (commands, skills, agents, rules as Markdown)
**Performance Goals**: N/A (CLI tool, file operations)
**Constraints**: Rules <= 100 lines, Commands <= 200 lines, Skills <= 400 lines; pathlib only (no os.path)
**Scale/Scope**: 26 commands, 104+ skills, 13 agents, 7+ rules, ~1136 lines in cli.py

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Detect-First, Respect-Existing | PASS | All changes extend existing patterns; no refactoring of working code |
| II. Pattern Fidelity | PASS | New `copy_skills()`/`copy_agents()` follow exact pattern of existing `copy_commands()`/`copy_rules()` |
| III. Architecture & Platform Agnostic | PASS | All changes use pathlib; cross-platform tested; no OS-specific code |
| IV. Best Practices & Quality | PASS | Adding rules/skills that enforce best practices (Options pattern, testing) |
| V. Safety & Token Discipline | PASS | New rules <= 100 lines, new skills <= 400 lines; no deployment changes |

No violations. Complexity Tracking not needed.

## Project Structure

### Documentation (this feature)

```text
specs/007-fix-tool-issues/
├── plan.md              # This file
├── research.md          # Phase 0 research findings
├── data-model.md        # Phase 1 data model
├── quickstart.md        # Phase 1 implementation quickstart
└── tasks.md             # Phase 2 task breakdown (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/dotnet_ai_kit/
├── cli.py                  # Modified: init() and upgrade() add skill/agent copying
├── copier.py               # Modified: add copy_skills(), copy_agents(); fix Jinja2 StrictUndefined
├── models.py               # Modified: add hybrid to microservice types; add repo path validation
├── extensions.py           # Modified: add cleanup on failure; add file locking

pyproject.toml              # Modified: add filelock dependency

templates/
└── config-template.yml     # Modified: fix permissions_level key; fix AI tools comment

hooks/
└── pre-commit-lint.sh      # Modified: fix find command parentheses

commands/
├── implement.md            # Modified: add always-loaded skills; add agent loading per repo type
├── tasks.md                # Modified: add command-side entity constraint; document [P] marker
├── specify.md              # Modified: enforce per-repo feature numbering starting at 001
├── plan.md                 # Modified: make constitution check optional
└── analyze.md              # Modified: remove event-catalogue reference

rules/
├── configuration.md        # NEW: Options pattern enforcement rule
└── testing.md              # NEW: CQRS testing patterns rule

skills/
├── core/
│   └── error-handling/
│       └── SKILL.md        # NEW: Domain exceptions, gRPC error mapping
└── microservice/
    └── command/
        └── event-versioning/
            └── SKILL.md    # NEW: Event schema evolution patterns

agents/
└── query-architect.md      # Modified: add Cosmos DB routing guidance

tests/
├── test_copier.py          # Modified: add tests for copy_skills(), copy_agents()
├── test_cli.py             # Modified: add tests for init with skills/agents
└── test_extensions.py      # Modified: add tests for cleanup and locking
```

**Structure Decision**: Single project structure (existing). All changes modify or add files within the existing directory layout. No new projects or directories outside the established pattern.

## Complexity Tracking

> No constitution violations. Table not needed.
