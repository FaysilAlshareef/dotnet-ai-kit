# Implementation Plan: Fix Permission System - Bypass Mode & Auto-Apply

**Branch**: `009-fix-permission-bypass` | **Date**: 2026-03-25 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-fix-permission-bypass/spec.md`

## Summary

The dotnet-ai-kit's permission system is broken: selecting a permission level (minimal/standard/full) saves a label to config.yml but never writes the actual permission rules to Claude Code's settings file. This plan implements four fixes: (1) a `copy_permissions()` function in copier.py that writes permission rules to `.claude/settings.json`, (2) integration into init/configure/upgrade CLI commands, (3) expanded `permissions-full.json` covering all common dev commands plus bypass mode, and (4) a `--global` flag for user-level cross-repo permissions.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: typer (CLI), pydantic v2 (models), pyyaml (config), rich (console output)
**Storage**: JSON files (`.claude/settings.json`, `~/.claude/settings.json`), YAML (`config.yml`)
**Testing**: pytest, pytest-cov
**Target Platform**: Windows, macOS, Linux (cross-platform)
**Project Type**: CLI tool / AI dev plugin
**Performance Goals**: Permission application < 2 seconds (SC-002)
**Constraints**: No `os.path.join` (use pathlib), no `shell=True`, always `encoding="utf-8"`
**Scale/Scope**: 3 permission templates (JSON), 1 new function in copier.py, modifications to 2-3 CLI commands, 1 new model field

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Detect-First, Respect-Existing | PASS | We're modifying the tool itself, not target project code. Existing copier.py patterns are followed. Merge strategy preserves user-defined rules. |
| II. Pattern Fidelity | PASS | New code follows existing codebase conventions: pathlib.Path, encoding="utf-8", pydantic v2 models, docstrings, type hints. |
| III. Architecture & Platform Agnostic | PASS | Uses `Path.home()` for global settings. All paths via pathlib. Works on Win/Mac/Linux. Claude Code-specific but scoped to its settings format. |
| IV. Best Practices & Quality | PASS | Tests written for copier.py changes. JSON merge handles edge cases. Error handling with actionable messages. |
| V. Safety & Token Discipline | PASS | One-time security warning for bypass mode. No deployment actions. Files are standard JSON/YAML operations. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/009-fix-permission-bypass/
├── plan.md              # This file
├── research.md          # Phase 0: Claude Code settings format research
├── data-model.md        # Phase 1: Data model for permission merge
├── quickstart.md        # Phase 1: Quick implementation guide
├── contracts/           # Phase 1: Settings JSON contract
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/dotnet_ai_kit/
├── copier.py            # MODIFY: Add copy_permissions(), merge_permissions()
├── cli.py               # MODIFY: Wire permission apply into init/configure/upgrade
├── models.py            # MODIFY: Add managed_permissions field to DotnetAiConfig
└── config.py            # No changes needed (save_config already handles new fields)

config/
├── permissions-minimal.json   # MODIFY: Add bare-command variants for zero-arg matching
├── permissions-standard.json  # MODIFY: Add missing common commands
├── permissions-full.json      # MODIFY: Major expansion + bypass mode config
└── mcp-permissions.json       # No changes (out of scope)

tests/
├── test_copier.py       # MODIFY: Add tests for copy_permissions/merge
└── test_cli.py          # MODIFY: Add tests for permission apply in init/configure
```

**Structure Decision**: Single project layout — all changes fit within existing `src/dotnet_ai_kit/` and `tests/` directories. No new modules needed; `copy_permissions()` belongs in `copier.py` alongside other file-copy functions.

## Complexity Tracking

> No constitution violations — table not needed.
