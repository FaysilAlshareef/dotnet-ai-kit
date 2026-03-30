# Tasks: Fix Command Style Lifecycle

**Input**: Design documents from `/specs/014-command-style-lifecycle/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Foundational (Cleanup Helper)

**Purpose**: Shared cleanup function used by US1 (style change cleanup) and US3 (plugin mode cleanup)

- [x] T001 Add `_clean_managed_commands(commands_dir: Path) -> int` helper function to `src/dotnet_ai_kit/copier.py` that deletes all files matching `dotnet-ai.*.md` and `dai.*.md` patterns from the given directory using `Path.glob()`. Return count of deleted files. No-op if directory does not exist.

**Checkpoint**: Helper function exists and can be unit tested in isolation.

---

## Phase 2: User Story 1 — Style Change Cleans Up Stale Files (Priority: P1)

**Goal**: Changing `command_style` removes files from the previous style so no stale duplicates remain.

**Independent Test**: Init with `both` (creates 54 files), change to `short`, run copy_commands again, verify only 27 `dai.*.md` files exist and zero `dotnet-ai.*.md` files.

- [x] T002 [US1] Update `copy_commands()` in `src/dotnet_ai_kit/copier.py`: call `_clean_managed_commands(commands_dir)` at the start of the function, after `commands_dir.mkdir()` and before the file-writing loop (line ~87)
- [x] T003 [P] [US1] Add test `test_cleanup_on_style_change_both_to_short` in `tests/test_copier.py`: call `copy_commands` with `both` style, then call again with `short` style, assert zero `dotnet-ai.*.md` files remain and only `dai.*.md` files exist
- [x] T004 [P] [US1] Add test `test_cleanup_on_style_change_full_to_short` in `tests/test_copier.py`: call `copy_commands` with `full` style, then call with `short` style, assert zero `dotnet-ai.*.md` files and only `dai.*.md` exist
- [x] T005 [P] [US1] Add test `test_cleanup_on_style_change_short_to_full` in `tests/test_copier.py`: call `copy_commands` with `short` style, then call with `full` style, assert zero `dai.*.md` files and only `dotnet-ai.*.md` exist
- [x] T006 [P] [US1] Add test `test_cleanup_preserves_user_files` in `tests/test_copier.py`: create a custom user file (`my-custom.md`) in commands dir, run `copy_commands`, assert user file still exists

**Checkpoint**: Style changes clean up stale files. All existing `copy_commands` tests still pass.

---

## Phase 3: User Story 2 — Short Aliases Always Have Full Content (Priority: P1)

**Goal**: `dai.*.md` files always contain the complete command content, never redirect stubs.

**Independent Test**: Init with `both` style, read any `dai.*.md` file, verify it contains the actual command instructions (not "See /dotnet-ai.specify").

- [x] T007 [US2] Remove the redirect stub branch (the `elif config.command_style == "both":` block that writes alias content) in `copy_commands()` in `src/dotnet_ai_kit/copier.py`: replace the `if config.command_style == "short": ... elif config.command_style == "both": ...` block with a single unconditional write of full `content` to the short alias file for both `short` and `both` styles
- [x] T008 [P] [US2] Add test `test_short_aliases_have_full_content_in_both_mode` in `tests/test_copier.py`: call `copy_commands` with `both` style, read both `dotnet-ai.specify.md` and `dai.specify.md`, assert `dai.specify.md` contains the actual command content (e.g., "Run the specify command") not a redirect stub, and assert its content equals `dotnet-ai.specify.md` content (FR-005 equivalence)

**Checkpoint**: All `dai.*.md` files contain full content regardless of style mode.

---

## Phase 4: User Story 3 — Plugin Mode Prevents Command Duplication (Priority: P2)

**Goal**: In plugin mode, `dotnet-ai.*.md` files are never written; only `dai.*.md` short aliases are written when style includes "short".

**Independent Test**: Call `copy_commands` with `is_plugin=True` and `both` style, verify zero `dotnet-ai.*.md` files and only `dai.*.md` files with full content.

- [x] T009 [US3] Add `is_plugin: bool = False` keyword argument to `copy_commands()` signature in `src/dotnet_ai_kit/copier.py`. Add early return `return 0` after cleanup if `is_plugin` and `config.command_style == "full"`. Skip the `dotnet-ai.*.md` write block when `is_plugin` is True.
- [x] T010 [US3] Add `_detect_plugin_mode() -> bool` helper function to `src/dotnet_ai_kit/cli.py` that checks if `_get_package_dir() / ".claude-plugin" / "plugin.json"` exists. Return True if found, False otherwise.
- [x] T011 [US3] Update the `copy_commands()` call site in the `init()` function in `src/dotnet_ai_kit/cli.py`: compute `is_plugin = _detect_plugin_mode()` before the tool loop and pass `is_plugin=is_plugin` to `copy_commands()`
- [x] T012 [US3] Update the `copy_commands()` call site in the `upgrade()` function in `src/dotnet_ai_kit/cli.py`: compute `is_plugin = _detect_plugin_mode()` before the tool loop and pass `is_plugin=is_plugin` to `copy_commands()`
- [x] T013 [P] [US3] Add test `test_plugin_mode_skips_full_commands` in `tests/test_copier.py`: call `copy_commands` with `is_plugin=True` and `both` style, assert zero `dotnet-ai.*.md` files and `dai.*.md` files with full content
- [x] T014 [P] [US3] Add test `test_plugin_mode_full_style_writes_nothing` in `tests/test_copier.py`: call `copy_commands` with `is_plugin=True` and `full` style, assert count returned is 0 and no managed files exist
- [x] T015 [P] [US3] Add test `test_plugin_mode_short_style_writes_dai_only` in `tests/test_copier.py`: call `copy_commands` with `is_plugin=True` and `short` style, assert only `dai.*.md` files with full content exist

**Checkpoint**: Plugin mode works correctly for all 3 style settings. Standalone mode backward compatible.

---

## Phase 4b: Configure Command Re-Copy (Post-Review Fix)

**Goal**: The `configure()` CLI function must re-copy command files after saving config so style changes take effect immediately (FR-014, FR-017).

- [x] T019 [US1] Add command re-copy logic to the `configure()` function in `src/dotnet_ai_kit/cli.py`: after applying permissions and saving config, call `copy_commands()` for each configured AI tool (same pattern as `init()`). Compute `is_plugin = _detect_plugin_mode()` and pass it. Report the number of commands re-copied.
- [x] T020 [P] [US1] Add test `test_configure_recopy_on_style_change` in `tests/test_cli.py`: invoke configure with `--no-input --company Test --style short`, verify that command files in `.claude/commands/` match the new style (only `dai.*.md` files, no `dotnet-ai.*.md`)

**Checkpoint**: Style changes via `dotnet-ai configure` take effect immediately.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates and final validation

- [x] T016 [P] Add plugin mode behavior note to Step 5 (Command Style section) in `commands/configure.md`: document that in plugin mode `dotnet-ai-kit:*` commands are always available, `full` writes nothing, `short`/`both` write only `dai.*.md`, style changes always clean up stale files first. Note that the configure quick-update mode (`style=short`, etc.) triggers re-copy with cleanup via the CLI subprocess call (FR-003, FR-014)
- [x] T017 [P] Add plugin vs standalone note to `commands/init.md`: document that when running as a plugin, `dotnet-ai.*.md` files are NOT copied because the plugin system serves them, only `dai.*.md` short aliases are copied when style includes "short"
- [x] T018 Run `pytest tests/test_copier.py -v` to verify all existing tests pass alongside the 7 new tests

**Checkpoint**: All tests pass, documentation updated.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundational)**: No dependencies — start immediately
- **Phase 2 (US1)**: Depends on T001 (cleanup helper)
- **Phase 3 (US2)**: No dependency on Phase 2 — can run in parallel (different code block in same file)
- **Phase 4 (US3)**: Depends on T001 (cleanup helper) and T007 (full content logic) since US3 adds `is_plugin` to the already-modified `copy_commands()`
- **Phase 5 (Polish)**: Depends on all previous phases

### User Story Dependencies

- **US1 (Cleanup)**: Independent after Phase 1 foundational helper
- **US2 (Full Content)**: Independent — modifies a different code block in `copy_commands()`
- **US3 (Plugin Mode)**: Depends on US1 + US2 being in place (adds `is_plugin` to the already-updated function)

### Parallel Opportunities

- T003, T004, T005, T006 can run in parallel (independent test functions in same file)
- T008 can run in parallel with US1 tests (different test function)
- T013, T014, T015 can run in parallel (independent test functions)
- T016, T017 can run in parallel (different command files)

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Complete Phase 1: Cleanup helper (T001)
2. Complete Phase 2: Style change cleanup (T002-T006)
3. Complete Phase 3: Full content aliases (T007-T008)
4. **STOP and VALIDATE**: Run pytest, verify cleanup works, verify aliases have full content
5. This alone fixes the 2 most impactful issues (P1 priorities)

### Full Delivery

6. Complete Phase 4: Plugin mode (T009-T015)
7. Complete Phase 5: Documentation (T016-T018)
8. Final validation: all 18 tasks complete, all tests pass

---

## Notes

- [P] tasks = different files or independent test functions, no dependencies
- [Story] label maps task to specific user story for traceability
- All file paths are relative to repository root
- Existing 4 `copy_commands` tests in `test_copier.py` must continue to pass (backward compatibility)
- copier.py has a 200-line soft budget per the constitution token discipline
