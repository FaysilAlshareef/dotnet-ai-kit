# Implementation Plan: Fix Command Style Lifecycle

**Branch**: `014-command-style-lifecycle` | **Date**: 2026-03-30 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/014-command-style-lifecycle/spec.md`

## Summary

Fix three command copy system issues: (1) add cleanup of managed files before writing to prevent stale files on style changes, (2) detect plugin mode and skip full-prefix files when plugin already serves them, (3) always write full content to short alias files instead of redirect stubs. Changes affect `copier.py`, `cli.py`, two command docs, and new tests.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: typer, pydantic v2, rich, pathlib
**Storage**: Filesystem (`.claude/commands/*.md` files)
**Testing**: pytest, pytest-cov
**Target Platform**: Windows, macOS, Linux (cross-platform)
**Project Type**: CLI tool / Claude Code plugin
**Performance Goals**: N/A (simple file I/O)
**Constraints**: Commands ≤ 200 lines, cross-platform paths via pathlib
**Scale/Scope**: 27 commands × 2 prefixes = max 54 files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Detect-First, Respect-Existing | PASS | Plugin detection respects existing install mode; cleanup only targets managed patterns |
| II. Pattern Fidelity | PASS | Changes follow existing copier.py code patterns (Path, encoding="utf-8") |
| III. Architecture & Platform Agnostic | PASS | Cross-platform via pathlib, no OS-specific code |
| IV. Best Practices & Quality | PASS | Tests written for all new behavior |
| V. Safety & Token Discipline | PASS | No token budget impact; cleanup is safe (pattern-scoped) |

No violations. No complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/014-command-style-lifecycle/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
└── tasks.md             # Phase 2 output (from /speckit.tasks)
```

### Source Code (repository root)

```text
src/dotnet_ai_kit/
├── copier.py            # MODIFY: add _clean_managed_commands(), update copy_commands()
├── cli.py               # MODIFY: add _detect_plugin_mode(), pass is_plugin to copy_commands()

tests/
├── test_copier.py       # MODIFY: add 7 new tests for cleanup, plugin mode, full-content aliases

commands/
├── configure.md         # MODIFY: add plugin mode note to Step 5
├── init.md              # MODIFY: add plugin vs standalone note
```

**Structure Decision**: Single project layout — all changes are modifications to existing files. No new files needed in `src/` or `tests/`.

## Implementation Layers

### Layer 1: copier.py — _clean_managed_commands() helper

Add a private function that deletes all `dotnet-ai.*.md` and `dai.*.md` files from a given directory. Uses `Path.glob()` with two patterns. Returns the count of deleted files.

**Key behavior**:
- Safe on non-existent directory (no-op)
- Only matches `dotnet-ai.*.md` and `dai.*.md` — user files untouched
- Called at the start of `copy_commands()` before any writes

### Layer 2: copier.py — copy_commands() signature update

Add `is_plugin: bool = False` parameter. Update logic:

1. Call `_clean_managed_commands()` at the start (always, regardless of mode)
2. If `is_plugin` and style is `full`: return 0 immediately after cleanup
3. If `is_plugin`: skip the `full` name write block entirely
4. Remove the stub alias branch (the `elif config.command_style == "both":` block that writes redirect content). The `both` style now writes full content to `dai.*.md` — same as `short` style does.

**Simplified post-change logic**:
```
# Cleanup managed files first
_clean_managed_commands(commands_dir)

for each command file:
    if not is_plugin and style in (full, both):
        write dotnet-ai.{name}.md with full content
    if style in (short, both):
        write dai.{name}.md with full content
```

### Layer 3: cli.py — _detect_plugin_mode() helper

Add a private function that checks `_get_package_dir() / ".claude-plugin" / "plugin.json"` exists.

In dev mode, `_get_package_dir()` returns the repo root where `.claude-plugin/plugin.json` lives. In wheel installs, it returns the bundled directory — the `.claude-plugin/` directory would need to be included in the wheel (already handled by plugin packaging). Returns `bool`.

### Layer 4: cli.py — Pass is_plugin to copy_commands()

Update all 3 call sites — `init()`, `upgrade()`, and `configure()` — to compute `is_plugin = _detect_plugin_mode()` and pass it to `copy_commands()`. The `configure()` function must also re-copy commands after saving config so style changes take effect immediately (same pattern as init/upgrade).

### Layer 5: commands/configure.md — Plugin mode documentation

Add a note under Step 5 (Command Style) explaining that in plugin mode:
- `dotnet-ai-kit:*` commands are always available via the plugin system
- `style=full` in plugin mode writes nothing (plugin handles full commands)
- `style=short` or `both` writes only `dai.*.md` short aliases
- Style changes always clean up stale files first

### Layer 6: commands/init.md — Plugin vs standalone note

Add a brief note explaining that when running as a plugin, full-prefix commands are not copied because the plugin system serves them. Only short aliases are copied when the style includes "short".

### Layer 7: tests/test_copier.py — New tests

7 new tests covering:
1. Cleanup on style change (`both` → `short`)
2. Plugin mode skips full commands
3. Plugin mode + `full` style = zero files
4. Plugin mode + `short` style = only `dai.*.md`
5. Short aliases always have full content in `both` mode
6. Style change `full` → `short` (cleanup + create)
7. Style change `short` → `full` (cleanup + create)

All existing 4 `copy_commands` tests must continue to pass (backward compat).

## Constitution Re-Check (Post-Design)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Detect-First | PASS | Plugin detection checks existing `.claude-plugin/plugin.json` |
| II. Pattern Fidelity | PASS | Follows existing copier.py patterns exactly |
| III. Platform Agnostic | PASS | pathlib.Path throughout, no shell commands |
| IV. Best Practices | PASS | Tests cover all new behavior, backward compat verified |
| V. Safety & Token Discipline | PASS | No new files, minimal code additions, command docs stay under 200 lines |

All gates pass. Ready for `/speckit.tasks`.
