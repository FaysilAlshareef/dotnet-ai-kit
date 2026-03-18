# Quickstart: Fix Tool Quality Issues

**Branch**: `004-fix-tool-issues` | **Date**: 2026-03-18

## Overview

This feature addresses 4 quality issues found during testing, plus CLI UX polish based on clig.dev guidelines and dotnet scaffold patterns. The changes span detection, permissions, configure UX, plan generation, and overall CLI UX quality.

## Implementation Order

### 1. Detection System Rewrite (P1) — Start here

**Files to modify**:
- `src/dotnet_ai_kit/detection.py` — Core rewrite
- `src/dotnet_ai_kit/models.py` — Add `hybrid` to project_type enum, add DetectionSignal/DetectionScoreCard models
- `src/dotnet_ai_kit/cli.py` — Update init command to show detection summary and handle override
- `tests/test_detection.py` — Rewrite tests for signal-based detection

**Key changes**:
1. Replace `_MICROSERVICE_PATTERNS` dict with a signal-based scoring system
2. Add `DetectionSignal` and `DetectionScoreCard` pydantic models
3. Refactor `_detect_microservice()` to collect signals, score candidates, and pick winner
4. Add `hybrid` as a valid project type when both command and query signals are strong
5. Add confidence scoring (high >0.8, medium >0.5, low <=0.5)
6. Add detection summary output via `rich` panel
7. Add interactive override prompt after detection
8. Add `rich.progress.Progress` spinner during file scanning

**Test approach**: Create fixture directories with minimal .cs files representing each project type. Verify signal detection and classification independently.

### 2. Permission Handling Fix (P2)

**Files to modify**:
- `config/permissions-standard.json` — Fix syntax: colon → space, add `$schema`
- `config/permissions-full.json` — Same fixes
- `config/permissions-minimal.json` — Same fixes
- `rules/` — Update rules that instruct AI on command construction
- `src/dotnet_ai_kit/cli.py` — Add pre-flight tool validation

**Key changes**:
1. **CRITICAL**: Fix permission pattern syntax from `Bash(dotnet build:*)` to `Bash(dotnet build *)` (space, not colon) per Claude Code official docs
2. Add `"$schema": "https://json.schemastore.org/claude-code-settings.json"` to all permission JSON files
3. Add rules instructing AI to use sequential commands instead of `&&` chains
4. Add `_validate_tools()` function that checks if referenced tools exist in PATH via `shutil.which()`
5. Show warnings during `init`/`configure` if tools are missing with install URLs

### 3. Interactive Configure (P3)

**Files to modify**:
- `src/dotnet_ai_kit/cli.py` — Rewrite configure command
- `pyproject.toml` — Add `questionary` dependency
- `tests/test_cli.py` — Update configure tests

**Key changes**:
1. Replace `typer.prompt()` calls with `rich.prompt.Prompt.ask()` for single-select (with choices)
2. Add `questionary.checkbox()` for multi-select (AI tools)
3. Add descriptions to each choice
4. Show current/default values
5. Keep `--minimal` flag for non-interactive mode
6. Add `--no-input` flag for fully non-interactive CI/CD mode (all values via flags)

### 4. Plan Generation Completeness (P3)

**Files to modify**:
- Plan-related command/skill templates in `commands/` and `skills/`
- `.specify/templates/plan-template.md` — Add complexity detection guidance

**Key changes**:
1. Update plan command instructions to analyze spec complexity
2. Add conditional artifact generation based on complexity indicators
3. Define complexity thresholds (3+ entities, external integrations, multi-repo)

### 5. CLI UX Polish and Quality Audit (P3)

**Files to modify**:
- `src/dotnet_ai_kit/cli.py` — All commands
- `.specify/scripts/powershell/create-new-feature.ps1` — Parameter binding fix
- `tests/test_cli.py` — New tests

**Key changes (per clig.dev guidelines)**:
1. Add progress spinner during detection scanning via `rich.progress`
2. Add next-command suggestions after `init`, `configure`, `upgrade` complete
3. Add `--json` flag to all CLI commands for machine-readable output
4. Add `NO_COLOR` env var support (verify rich handles this)
5. Add Ctrl-C (SIGINT) handling — clean exit with message, no traceback
6. Route error messages to stderr, data to stdout
7. Map exit codes: 0=success, 1=general error, 2=config error, 3=detection failed
8. Fix `$Number` positional parameter binding bug in create-new-feature.ps1
9. Add `--dry-run` flag to init, configure, upgrade commands
10. Improve error messages to include "what went wrong" and "how to fix it"

## Dev Setup

```bash
# Install in dev mode
pip install -e ".[dev]"

# Run tests
pytest

# Run specific test file
pytest tests/test_detection.py -v

# Lint
ruff check src/ tests/
```

## Dependency Changes

- Add `questionary>=2.0.0` to `pyproject.toml` dependencies
- No other new dependencies needed (`rich` already handles progress, NO_COLOR)
