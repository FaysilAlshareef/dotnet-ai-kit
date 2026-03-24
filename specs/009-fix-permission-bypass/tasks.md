# Tasks: Fix Permission System - Bypass Mode & Auto-Apply

**Input**: Design documents from `/specs/009-fix-permission-bypass/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Add the foundational model field needed by all user stories

- [x] T001 Add `managed_permissions: list[str]` field with default `[]` to `DotnetAiConfig` in `src/dotnet_ai_kit/models.py`

**Checkpoint**: Model field exists, existing tests still pass (`pytest tests/test_config.py`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core merge logic and expanded templates that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 Implement `merge_permissions()` pure function in `src/dotnet_ai_kit/copier.py` — takes existing settings dict, template entries list, managed entries list, and permission level; returns merged settings dict following the algorithm in research.md R2 (preserve user entries, replace managed entries, set/remove defaultMode based on level)
- [x] T003 Implement `copy_permissions()` I/O function in `src/dotnet_ai_kit/copier.py` — reads permission template JSON from `config/` dir, loads existing `.claude/settings.json` (or creates empty), calls `merge_permissions()`, writes result, updates `managed_permissions` in config; accepts `target_dir`, `config`, `package_dir`, `global_install=False` parameters
- [x] T004 [P] Write tests for `merge_permissions()` in `tests/test_copier.py` — cover: empty settings (fresh project), existing user entries preserved, level change (old entries removed/new added), deny/ask rules preserved, full level sets bypassPermissions, standard level does NOT set bypassPermissions, deduplication
- [x] T005 [P] Write tests for `copy_permissions()` in `tests/test_copier.py` — cover: creates `.claude/settings.json` if missing, reads existing settings, invalid JSON handling (error reported, file not overwritten), missing template file error

**Checkpoint**: `merge_permissions()` and `copy_permissions()` work correctly — `pytest tests/test_copier.py -v`

---

## Phase 3: User Story 1 + User Story 2 — Bypass Mode & Auto-Apply on Init/Configure (Priority: P1) MVP

**Goal**: When a developer selects any permission level during init or configure, the tool actually writes the permission rules to `.claude/settings.json`. Full level enables bypassPermissions mode. This fixes the core bug.

**Independent Test**: Run `dotnet-ai init` with full permissions in a tmp project, verify `.claude/settings.json` contains `bypassPermissions` mode and allow-list entries. Run `dotnet-ai configure --permissions standard`, verify bypass mode is removed and standard allow-list is present.

### Implementation for US1 + US2

- [x] T006 [US1] [US2] Wire `copy_permissions()` call into `init` command in `src/dotnet_ai_kit/cli.py` — call after copying commands/rules/skills/agents, pass target dir, config, and package dir
- [x] T007 [US1] [US2] Wire `copy_permissions()` call into `configure` command in `src/dotnet_ai_kit/cli.py` — call after saving config to config.yml
- [x] T008 [US1] Add one-time bypass security warning in `src/dotnet_ai_kit/cli.py` — when `permissions_level == "full"`, display a rich Panel warning before applying permissions (FR-011)
- [x] T009 [US1] [US2] Add console feedback output in `src/dotnet_ai_kit/cli.py` — after `copy_permissions()` returns, print: number of permissions applied, target settings file path, active permission mode (FR-009)
- [x] T010 [US1] [US2] Write CLI integration tests in `tests/test_cli.py` — cover: init with full level creates settings.json with bypassPermissions, init with standard level creates settings.json without bypassPermissions, configure level change from standard to full adds bypass mode, configure level change from full to standard removes bypass mode

**Checkpoint**: `dotnet-ai init` and `dotnet-ai configure` now actually apply permissions. Full mode = zero prompts. Run full test suite: `pytest tests/ -v`

---

## Phase 4: User Story 3 — Comprehensive Command Coverage (Priority: P2)

**Goal**: The full permission template covers all common dev commands so no unexpected prompts appear for standard operations.

**Independent Test**: Inspect `config/permissions-full.json` for coverage of file system, .NET, git, npm/node, docker, search, and utility commands. Verify both bare and wildcard variants are present (e.g., `Bash(ls)` AND `Bash(ls *)`).

### Implementation for US3

- [x] T011 [P] [US3] Expand `config/permissions-full.json` to ~80+ entries covering: file system (ls, dir, find, grep, cat, head, tail, wc, cp, mv, rm, mkdir, echo, pwd, touch, chmod, stat, file, tree), .NET (all dotnet subcommands), git (all subcommands), gh (all subcommands), web dev (npm, node, ng, yarn, pnpm, npx, tsc, webpack, vite), containers (docker, docker-compose, podman), search (rg, ag, ack), utilities (curl, wget, which, where, sed, awk, sort, uniq, xargs, tee, tr, cut, diff, jq, yq), Python (python, pip, pytest, ruff), PowerShell (powershell, pwsh). Add `defaultMode: bypassPermissions`. Use both bare and wildcard patterns per research.md R3.
- [x] T012 [P] [US3] Expand `config/permissions-standard.json` to ~40 entries — add missing common commands: grep, find, head, tail, wc, echo, pwd, rg, python, pip, powershell, pwsh. Add bare-command variants (e.g., `Bash(ls)` alongside existing `Bash(ls *)`).
- [x] T013 [P] [US3] Update `config/permissions-minimal.json` to add bare-command variants — add `Bash(cd)`, `Bash(dotnet)` alongside existing wildcard entries to fix zero-arg matching.
- [x] T014 [US3] Write a validation test in `tests/test_copier.py` that loads each permission template JSON and verifies: valid JSON structure, no duplicate entries, `permissions-full.json` has `defaultMode: bypassPermissions`, `permissions-standard.json` does NOT have `defaultMode`, all entries match the `Bash(*)` or tool permission format.

**Checkpoint**: All three permission templates are comprehensive and valid. `pytest tests/test_copier.py -v`

---

## Phase 5: User Story 4 — Global Permission Installation (Priority: P2)

**Goal**: Developers can apply permissions globally to `~/.claude/settings.json` so they work across all repos.

**Independent Test**: Run `dotnet-ai configure --global --permissions full`, verify `~/.claude/settings.json` contains bypass mode and full allow-list.

### Implementation for US4

- [x] T015 [US4] Add `--global` flag to `configure` command in `src/dotnet_ai_kit/cli.py` — `typer.Option(False, "--global", help="Apply permissions to global user settings (~/.claude/settings.json)")`. When set, pass `global_install=True` to `copy_permissions()`.
- [x] T016 [US4] Update `copy_permissions()` in `src/dotnet_ai_kit/copier.py` to handle `global_install=True` — target `Path.home() / ".claude" / "settings.json"` instead of project-level `.claude/settings.json`. Create `~/.claude/` directory if it doesn't exist.
- [x] T017 [US4] Write tests for global install in `tests/test_cli.py` — cover: global flag targets home dir settings, global flag creates ~/.claude/ if missing, error when home dir not writable (mock `Path.home()` in tests using `tmp_path`)

**Checkpoint**: `--global` flag works. `pytest tests/test_cli.py -v`

---

## Phase 6: User Story 5 — Upgrade Existing Projects (Priority: P3)

**Goal**: Existing projects with `permissions_level` set but no applied permissions get auto-fixed on upgrade.

**Independent Test**: Create a project with old-style config (permissions_level: full, no `.claude/settings.json`), run `dotnet-ai upgrade`, verify permissions are applied.

### Implementation for US5

- [x] T018 [US5] Add permission gap detection to `upgrade` command in `src/dotnet_ai_kit/cli.py` — after loading config, check if `permissions_level` is set but `.claude/settings.json` either doesn't exist or has no `permissions.allow` entries. If gap detected, call `copy_permissions()` and report what was applied.
- [x] T019 [US5] Write tests for upgrade permission detection in `tests/test_cli.py` — cover: old config with permissions_level but no settings.json triggers apply, already-applied permissions skip apply (idempotent), upgrade reports what was applied in output

**Checkpoint**: Upgrade auto-fixes permission gap. `pytest tests/test_cli.py -v`

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge case handling, error messages, and final validation

- [x] T020 Add edge case handling in `copy_permissions()` in `src/dotnet_ai_kit/copier.py` — invalid JSON error (report clearly, don't overwrite), missing template file error (report and suggest reinstall), no write access error (actionable message), idempotent check (skip if permissions already up to date)
- [x] T021 [P] Run `ruff check src/dotnet_ai_kit/copier.py src/dotnet_ai_kit/cli.py src/dotnet_ai_kit/models.py` and `ruff format --check` to ensure code passes linting
- [x] T022 [P] Run full test suite `pytest tests/ -v --tb=short` and verify all tests pass (existing + new). Manually verify SC-002: time the `dotnet-ai configure --permissions full` command and confirm it completes in under 2 seconds.
- [x] T023 Run quickstart.md validation — manually verify the implementation matches the quickstart guide steps
- [x] T024 Add `dry_run` parameter to `copy_permissions()` in `src/dotnet_ai_kit/copier.py` — when True, compute and return the merged result without writing to disk. Print a preview of what would change (entries added/removed, mode change). Wire the existing `--dry-run` flag from init/configure commands to pass through to `copy_permissions()`.
- [x] T025 Add pre-write backup in `copy_permissions()` in `src/dotnet_ai_kit/copier.py` — before overwriting `.claude/settings.json`, save the current file to `.dotnet-ai-kit/backups/settings.json.bak` (with timestamp if multiple backups needed). This enables `/dotnet-ai.undo` to restore the previous state.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (model field needed by merge function)
- **US1+US2 (Phase 3)**: Depends on Phase 2 (needs merge_permissions and copy_permissions)
- **US3 (Phase 4)**: Can run in PARALLEL with Phase 3 (template files are independent of Python code)
- **US4 (Phase 5)**: Depends on Phase 3 (needs copy_permissions wired into CLI)
- **US5 (Phase 6)**: Depends on Phase 3 (needs copy_permissions wired into CLI)
- **Polish (Phase 7)**: Depends on all previous phases

### User Story Dependencies

- **US1+US2 (P1)**: Depends on Foundational (Phase 2) — core bug fix
- **US3 (P2)**: Independent of US1/US2 — template expansion is file-only work
- **US4 (P2)**: Depends on US1/US2 — needs copy_permissions in CLI before adding --global flag
- **US5 (P3)**: Depends on US1/US2 — needs copy_permissions in CLI before adding upgrade detection

### Within Each User Story

- Pure functions before I/O wrappers
- I/O functions before CLI wiring
- CLI wiring before tests
- Tests validate the full chain

### Parallel Opportunities

- T002 + T004 can start together (write function + tests simultaneously)
- T003 depends on T002; T005 can start after T003
- T011 + T012 + T013 are all parallel (different JSON files)
- T011/T012/T013 (Phase 4) can run in parallel with Phase 3 tasks
- T021 + T022 are parallel (lint + tests)

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Launch merge function + tests together:
Task: "Implement merge_permissions() in src/dotnet_ai_kit/copier.py"
Task: "Write tests for merge_permissions() in tests/test_copier.py"

# Launch I/O function + tests together:
Task: "Implement copy_permissions() in src/dotnet_ai_kit/copier.py"
Task: "Write tests for copy_permissions() in tests/test_copier.py"
```

## Parallel Example: Phase 4 (US3 - Templates)

```bash
# All three template files can be expanded simultaneously:
Task: "Expand config/permissions-full.json"
Task: "Expand config/permissions-standard.json"
Task: "Update config/permissions-minimal.json"
```

---

## Implementation Strategy

### MVP First (US1 + US2 Only)

1. Complete Phase 1: Add model field (T001)
2. Complete Phase 2: merge + copy functions (T002-T005)
3. Complete Phase 3: Wire into init/configure (T006-T010)
4. **STOP and VALIDATE**: Test with `dotnet-ai init --permissions full` in a tmp project
5. The core bug is fixed — permissions are now applied

### Incremental Delivery

1. Phase 1 + 2 → Foundation ready
2. Phase 3 (US1+US2) → Core bug fix (MVP!)
3. Phase 4 (US3) → Comprehensive command coverage
4. Phase 5 (US4) → Global install support
5. Phase 6 (US5) → Upgrade auto-fix
6. Phase 7 → Polish and validate

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US1 and US2 are merged into one phase because they share the same core implementation (copy_permissions)
- Tests are included per constitution TDD principle
- Template expansion (Phase 4) is independent and can run in parallel with Phase 3
