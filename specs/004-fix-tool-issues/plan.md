# Implementation Plan: Fix Tool Quality Issues

**Branch**: `004-fix-tool-issues` | **Date**: 2026-03-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-fix-tool-issues/spec.md`

## Summary

Fix 4 quality issues found during testing plus CLI UX polish: (1) rewrite detection to use signal-based scoring of actual code patterns instead of name-first classification, (2) fix permission handling — colon→space syntax fix, pre-flight tool validation, AI guidance rules, (3) convert configure command to interactive selection menus with `--no-input` for CI/CD, (4) enhance plan generation to produce data models and contracts for complex features, (5) CLI UX polish per clig.dev guidelines — progress spinners, next-command suggestions, `--json`, `NO_COLOR`, Ctrl-C handling, stderr routing, exit code mapping.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: typer, pydantic v2, jinja2, rich, pyyaml, questionary (new)
**Storage**: YAML files (`.dotnet-ai-kit/config.yml`, `.dotnet-ai-kit/project.yml`)
**Testing**: pytest, pytest-cov
**Target Platform**: Windows, macOS, Linux (cross-platform)
**Project Type**: CLI tool (Python package)
**Performance Goals**: Detection should complete within 5 seconds for typical .NET solutions (<50 .cs files)
**Constraints**: Token budgets (rules ≤100 lines, commands ≤200 lines, skills ≤400 lines), cross-platform paths via pathlib, follow clig.dev CLI UX guidelines
**Scale/Scope**: Single developer tool, typical solution has 1-10 projects

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Detect-First, Respect-Existing | PASS | This feature improves detection itself — aligns perfectly |
| II. Pattern Fidelity | PASS | Not generating .NET code; improving the tool's own code |
| III. Architecture & Platform Agnostic | PASS | Detection must work for all architecture types; cross-platform enforced |
| IV. Best Practices & Quality | PASS | Adding tests, improving error handling, TDD approach, clig.dev UX patterns |
| V. Safety & Token Discipline | PASS | No deployment actions; token budgets respected; --dry-run for init/configure/upgrade |

**Gate result**: ALL PASS — no violations to justify.

**Post-Phase 1 re-check**: All principles still satisfied. The signal-based detection strengthens Principle I. The `hybrid` type addition and architecture-agnostic scoring align with Principle III. Interactive configure and pre-flight tool validation improve Principle IV compliance.

## Project Structure

### Documentation (this feature)

```text
specs/004-fix-tool-issues/
├── plan.md              # This file
├── research.md          # Phase 0 output — 6 research decisions
├── data-model.md        # Phase 1 output — entity definitions
├── quickstart.md        # Phase 1 output — implementation guide
├── contracts/           # Phase 1 output
│   ├── cli-detection-output.md    # Detection summary format
│   ├── cli-configure-prompts.md   # Interactive configure UX
│   └── permission-json-format.md  # Permission JSON structure
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/dotnet_ai_kit/
├── detection.py          # MODIFY: Rewrite to signal-based scoring
├── models.py             # MODIFY: Add DetectionSignal, DetectionScoreCard, hybrid type
├── cli.py                # MODIFY: Detection summary, override, interactive configure
├── config.py             # MINOR: No changes expected
├── copier.py             # MINOR: No changes expected
├── extensions.py         # MINOR: No changes expected
└── agents.py             # MINOR: No changes expected

config/
├── permissions-standard.json  # MODIFY: Update patterns
├── permissions-full.json      # MODIFY: Update patterns
└── permissions-minimal.json   # MODIFY: Fix colon→space syntax, add $schema

tests/
├── test_detection.py     # MODIFY: Rewrite for signal-based detection
├── test_cli.py           # MODIFY: Add configure interactive tests
├── test_config.py        # MINOR: No changes expected
├── test_copier.py        # MINOR: No changes expected
└── test_extensions.py    # MINOR: No changes expected
```

**Structure Decision**: Single project layout. All changes are within the existing `src/dotnet_ai_kit/` package and `tests/` directory. No new directories needed in source. The `contracts/` directory is spec-only (not shipped).

## Complexity Tracking

> No constitution violations to justify. All changes fit within existing project structure.
