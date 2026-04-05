# Tasks: Tool-Wide Quality Hardening

**Input**: Design documents from `/specs/016-tool-quality-hardening/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included — constitution principle IV (Best Practices) requires tests for all code changes.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core changes to build system and shared modules that user stories depend on

**CRITICAL**: US1 depends on pyproject.toml fix. US3/US6 depend on config.py and models.py fixes.

- [x] T001 [P] Add `profiles/` and `prompts/` to force-include in `pyproject.toml` (2 new entries mapping to `dotnet_ai_kit/bundled/profiles` and `dotnet_ai_kit/bundled/prompts`)
- [x] T002 [P] Add `KNOWN_PATH_KEYS` frozenset and `detected_paths` field_validator to `src/dotnet_ai_kit/models.py` — warn on unknown keys, do not reject (per data-model.md)
- [x] T003 [P] Wrap `yaml.safe_load()` in `src/dotnet_ai_kit/config.py:load_config()` with `yaml.YAMLError` catch, re-raise as `ValueError` with user-friendly message
- [x] T004 [P] Add `COMMAND_SHORT_ALIASES` dict to `src/dotnet_ai_kit/copier.py` (10 entries per data-model.md) and update short-prefix generation in `copy_commands()` to use alias when available
- [x] T005 [P] Remove `integrations:` section from `templates/config-template.yml` (lines 44-53), replace with comment about future support

### Tests for Foundational

- [x] T006 [P] Add test for `detected_paths` validator warning on unknown keys in `tests/test_models.py`
- [x] T007 [P] Add test for corrupted YAML producing `ValueError` (not `yaml.YAMLError`) in `tests/test_config.py`
- [x] T008 [P] Add test for `COMMAND_SHORT_ALIASES` producing correct short filenames (`dai.spec.md`, `dai.check.md`, `dai.go.md`) in `tests/test_copier.py`

**Checkpoint**: Foundation ready — all shared constants, validators, and build fixes in place. User story implementation can begin.

---

## Phase 2: User Story 1 - Production Install Works End-to-End (Priority: P1)

**Goal**: Wheel installs deploy architecture profiles and hooks via `init`. No silent failures.

**Independent Test**: Build wheel, install, run `init --type command --ai claude`, verify `architecture-profile.md` and PreToolUse hook exist.

### Implementation for User Story 1

- [x] T009 [US1] Add profile and hook deployment to `init()` in `src/dotnet_ai_kit/cli.py` — after existing skill/agent deployment (step 7b per contracts/cli-changes.md), gated on project type being known via `--type` or existing `project.yml`
- [x] T010 [US1] Add test verifying `init --type command --ai claude` deploys `architecture-profile.md` to `.claude/rules/` in `tests/test_cli.py`
- [x] T011 [US1] Add test verifying `init --type command --ai claude` deploys PreToolUse hook with `_source: "dotnet-ai-kit-arch"` to `.claude/settings.json` in `tests/test_cli.py`
- [x] T012 [US1] Add test verifying wheel contains `profiles/` and `prompts/` directories after `python -m build` in `tests/test_cli.py`

**Checkpoint**: Production installs now deploy profiles and hooks. US1 is fully functional and testable.

---

## Phase 3: User Story 2 - Secondary Repo Branch Safety (Priority: P1)

**Goal**: All 5 SDD commands that touch secondary repos enforce branch safety before committing.

**Independent Test**: Compare branch safety sections across specify.md, clarify.md, plan.md, tasks.md, implement.md — all must match.

### Implementation for User Story 2

- [x] T013 [P] [US2] Add "Secondary Repo Branch Safety" section to `commands/clarify.md` — insert before final section (exact text from contracts/command-changes.md), verify ≤200 lines after
- [x] T014 [P] [US2] Add "Secondary Repo Branch Safety" section to `commands/implement.md` — insert before Error Handling section (exact text from contracts/command-changes.md), verify ≤200 lines after

**Checkpoint**: All 5 secondary-repo commands have consistent branch safety. US2 complete.

---

## Phase 4: User Story 3 - CLI Lifecycle Completeness (Priority: P2)

**Goal**: `check` reports all deployed features. `upgrade` shows warning messages instead of silently swallowing errors.

**Independent Test**: Run `check` and verify profile/hook/skills/agents/linked-repos fields appear. Run `upgrade` with a failing profile and verify warning.

### Implementation for User Story 3

- [x] T015 [US3] Extend `check()` rich table in `src/dotnet_ai_kit/cli.py` — add Skills, Agents, Profile, Hook columns to AI Tools table (per contracts/cli-changes.md)
- [x] T016 [US3] Extend `check()` config panel in `src/dotnet_ai_kit/cli.py` — add Linked from, Detected paths, and Linked repos rows
- [x] T017 [US3] Extend `check()` JSON output in `src/dotnet_ai_kit/cli.py` — add skills, agents, profile, hook per tool + linked_from, detected_paths, linked_repos top-level fields
- [x] T018 [US3] Replace 4 `except Exception: pass` blocks in `upgrade()` in `src/dotnet_ai_kit/cli.py` with `except Exception as exc:` that prints yellow warning via `err_console.print()` (lines ~887, ~971, ~977, ~993)

### Tests for User Story 3

- [x] T019 [P] [US3] Add test for `check` reporting profile status (deployed/not deployed) in `tests/test_cli.py` — include timing assertion that check completes within 5 seconds (SC-003)
- [x] T020 [P] [US3] Add test for `check --json` including skills, agents, profile, hook, linked_from, detected_paths fields in `tests/test_cli.py`
- [x] T021 [P] [US3] Add test verifying `upgrade` prints warning (not silence) when profile deployment fails in `tests/test_cli.py`

**Checkpoint**: `check` provides complete health report. `upgrade` provides actionable error feedback. US3 complete.

---

## Phase 5: User Story 4 - Command File Quality and Consistency (Priority: P2)

**Goal**: Artifact ownership clear, step ordering correct, flags unambiguous, short aliases match docs.

**Independent Test**: Verify `plan.md` generates event-flow.md, all 9 code-gen commands have distinct --dry-run and --list flags, `dai.spec.md` filename deployed.

### Implementation for User Story 4

- [x] T022 [P] [US4] Add event-flow.md generation step to `commands/plan.md` — insert microservice-mode step per contracts/command-changes.md, verify ≤200 lines
- [x] T023 [P] [US4] Fix duplicate --dry-run flag in `commands/add-aggregate.md` — rename second --dry-run to --list, update examples and Preview section
- [x] T024 [P] [US4] Fix duplicate --dry-run flag in `commands/add-crud.md` — same pattern as T023
- [x] T025 [P] [US4] Fix duplicate --dry-run flag in `commands/add-endpoint.md` — same pattern as T023
- [x] T026 [P] [US4] Fix duplicate --dry-run flag in `commands/add-entity.md` — same pattern as T023
- [x] T027 [P] [US4] Fix duplicate --dry-run flag in `commands/add-event.md` — same pattern as T023
- [x] T028 [P] [US4] Fix duplicate --dry-run flag in `commands/add-page.md` — same pattern as T023
- [x] T029 [P] [US4] Fix duplicate --dry-run flag in `commands/add-tests.md` — same pattern as T023
- [x] T030 [P] [US4] Fix duplicate --dry-run flag in `commands/docs.md` — same pattern as T023
- [x] T031 [P] [US4] Fix duplicate --dry-run flag in `commands/explain.md` — same pattern as T023
- [x] T032 [US4] Reorder steps in `commands/specify.md` — move Step 4b (Project Feature Briefs, L152) before Step 5 (Quality Checklist, L130), renumber to Steps 4→5→6→7 per contracts/command-changes.md
- [x] T033 [US4] Clarify artifact ownership in `commands/do.md` — update L51-52 to assign service-map.md to specify step and event-flow.md to plan step per contracts/command-changes.md
- [x] T034 [US4] Update CLAUDE.md command alias table to match actual deployed short filenames (ensure dai.spec, dai.check, dai.go etc. are consistent with COMMAND_SHORT_ALIASES from T004)

**Checkpoint**: All command files have correct step ordering, unambiguous flags, clear artifact ownership, and matching aliases. US4 complete.

---

## Phase 6: User Story 5 - Full Deployment Pipeline (Priority: P3)

**Goal**: `configure` re-deploys all assets. Secondary repos get their own command style. `git add` stages all tool directories.

**Independent Test**: Run `configure` and verify skills/agents refreshed. Deploy to secondary with different style and verify.

### Implementation for User Story 5

- [x] T035 [US5] Add `copy_rules()`, `copy_skills()`, `copy_agents()` calls to `configure()` in `src/dotnet_ai_kit/cli.py` — after command re-copy, before profile deployment (per contracts/cli-changes.md)
- [x] T036 [US5] Update `deploy_to_linked_repos()` in `src/dotnet_ai_kit/copier.py` — load secondary repo's config.yml for `command_style`, create modified config copy for `copy_commands()` call (fallback to "both" if no secondary config)
- [x] T037 [US5] Update `deploy_to_linked_repos()` in `src/dotnet_ai_kit/copier.py` — replace hardcoded `git add .claude/ .dotnet-ai-kit/` with dynamic directory list built from `AGENT_CONFIG` per tool (per contracts/cli-changes.md)

### Tests for User Story 5

- [x] T038 [P] [US5] Add test verifying `configure` calls `copy_rules`, `copy_skills`, `copy_agents` in `tests/test_cli.py`
- [x] T039 [P] [US5] Add test verifying secondary repo uses its own `command_style` (not primary's) in `tests/test_multi_repo_deploy.py`
- [x] T040 [P] [US5] Add test verifying `git add` stages `.cursor/` when secondary has Cursor configured in `tests/test_multi_repo_deploy.py`

**Checkpoint**: Deployment pipeline is complete and tool-aware. US5 complete.

---

## Phase 7: User Story 6 - Config and Model Robustness (Priority: P3)

**Goal**: No silently dropped config fields. Unknown detected_paths keys warned. Configure blocked without init.

**Independent Test**: Run `configure` without prior `init` and verify exit code 1.

### Implementation for User Story 6

- [x] T041 [US6] Add `.dotnet-ai-kit/` existence check at start of `configure()` in `src/dotnet_ai_kit/cli.py` — print error and exit code 1 if directory missing (per contracts/cli-changes.md)

### Tests for User Story 6

- [x] T042 [US6] Add test verifying `configure` without prior `init` exits code 1 with message in `tests/test_cli.py`

**Checkpoint**: Config handling is robust and user-friendly. US6 complete. (Note: T002, T005, T006 in foundational phase already cover models.py validator and template fix.)

---

## Phase 8: User Story 7 - Skill Auto-Activation Coverage (Priority: P3)

**Goal**: At least 80/120 skills have `when-to-use` frontmatter. At least 9 skills have `paths` tokens.

**Independent Test**: `grep -rl "when-to-use" skills/ | wc -l` returns ≥80. `grep -rl "detected_paths" skills/ | wc -l` returns ≥9.

### Implementation for User Story 7

- [x] T043 [P] [US7] Add `when-to-use` frontmatter to remaining 26 microservice/ skills that lack it — use consistent phrasing "When creating or modifying ..." per skill context
- [x] T044 [P] [US7] Add `when-to-use` frontmatter to all 7 architecture/ skills
- [x] T045 [P] [US7] Add `when-to-use` frontmatter to remaining 2 testing/ skills, 7 data/ skills, and 3 non-alwaysApply core/ skills (12 files total)
- [x] T046 [P] [US7] Add `when-to-use` frontmatter to all 11 api/ skills and 6 cqrs/ skills (17 files total)
- [x] T047 [P] [US7] Add `when-to-use` frontmatter to high-value skills in devops/, docs/, quality/, security/, resilience/, observability/, infra/, workflow/ categories (7-10 files to reach 80+ total)
- [x] T048 [P] [US7] Add `paths` tokens to 6 skills: microservice/query/query-entity, microservice/query/event-handler, microservice/cosmos/cosmos-entity, microservice/gateway/gateway-endpoint, testing/unit-testing, testing/integration-testing (per data-model.md)
- [x] T049 [US7] Verify all modified skill files remain under 400 lines — spot-check largest files

**Checkpoint**: Skill activation coverage at 80+/120 when-to-use and 9+/120 paths. US7 complete.

---

## Phase 9: User Story 8 - Extension Cleanup and Init Friction (Priority: P4)

**Goal**: Extension after_remove hooks execute. Init auto-defaults to Claude.

**Independent Test**: Remove extension with hooks, verify they run. Run `init` without `--ai`, verify Claude default.

### Implementation for User Story 8

- [x] T050 [P] [US8] Add `after_remove` hook execution to `remove_extension()` in `src/dotnet_ai_kit/extensions.py` — after deleting extension directory but before updating registry, mirror `install_extension()` pattern (lines 308-319)
- [x] T051 [US8] Update `init()` in `src/dotnet_ai_kit/cli.py` — when no `--ai` flag and no AI tool directories detected, auto-default to `["claude"]` with info message instead of exit code 3 (NOTE: modifies same function as T009 — implement after T009 completes, not in parallel)

### Tests for User Story 8

- [x] T052 [P] [US8] Add test verifying `after_remove` hooks execute during extension removal in `tests/test_extensions.py`
- [x] T053 [P] [US8] Add test verifying `init` without `--ai` defaults to Claude in `tests/test_cli.py`

**Checkpoint**: Extension cleanup works. New user friction eliminated. US8 complete.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Validation across all user stories, lint compliance, final verification

- [x] T054 Run `ruff check src/ tests/` and fix any lint errors introduced by changes
- [x] T055 Run `ruff format --check src/ tests/` and fix any format issues
- [x] T056 Run full test suite `pytest --cov=dotnet_ai_kit` — all tests must pass (existing 263 + new ~20)
- [x] T057 Verify skill activation counts: `grep -rl "when-to-use" skills/` ≥80, `grep -rl "detected_paths" skills/` ≥9
- [x] T058 Verify command line budgets: all modified commands ≤200 lines, all skills ≤400 lines
- [x] T059 Run quickstart.md validation — build wheel and verify profiles/ and prompts/ are bundled

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — start immediately
- **US1 (Phase 2)**: Depends on T001 (pyproject.toml), T009 depends on init() changes only
- **US2 (Phase 3)**: No code dependencies — pure markdown changes, can start immediately
- **US3 (Phase 4)**: Depends on T003 (config.py YAML fix)
- **US4 (Phase 5)**: Depends on T004 (COMMAND_SHORT_ALIASES in copier.py)
- **US5 (Phase 6)**: Depends on T004 (copier.py changes). T036-T037 modify deploy_to_linked_repos
- **US6 (Phase 7)**: Depends on T002 (models.py), T005 (template)
- **US7 (Phase 8)**: No code dependencies — pure skill frontmatter changes, can start immediately
- **US8 (Phase 9)**: No dependencies — extensions.py and init() changes are independent
- **Polish (Phase 10)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational T001. Can start after T001.
- **US2 (P1)**: Independent — can start immediately (markdown only)
- **US3 (P2)**: Depends on Foundational T003. Independent of US1/US2.
- **US4 (P2)**: Depends on Foundational T004. Independent of US1-US3.
- **US5 (P3)**: Depends on T004 (copier.py). Can start after T004. Independent of US1-US4.
- **US6 (P3)**: Depends on T002, T005 (models/template). Independent of US1-US5.
- **US7 (P3)**: Fully independent — can start immediately alongside any other story.
- **US8 (P4)**: Fully independent — can start immediately alongside any other story.

### Within Each User Story

- Tests written alongside implementation (not strict TDD since many changes are small)
- Code changes before tests (test against actual behavior)
- Verify line budgets after each command file change

### Parallel Opportunities

**Immediate parallel starts** (no dependencies):
- T001-T005 (all foundational tasks)
- T013-T014 (US2 — branch safety)
- T043-T048 (US7 — skill activation)

**After foundational completes**:
- US1 (T009-T012) + US3 (T015-T021) + US4 (T022-T034) + US5 (T035-T040) + US6 (T041-T042) + US8 (T050-T053) can all proceed in parallel

**Shared file note**: US3 (T015-T018), US5 (T035), US6 (T041), US1 (T009), and US8 (T051) all modify `cli.py`. They target different functions so parallel execution is safe, but coordinate commits to avoid merge conflicts. T051 must follow T009 (same function).

---

## Parallel Example: Maximum Concurrency

```
# Wave 1: Start immediately (5 parallel streams)
Stream A: T001, T002, T003, T004, T005 (foundational — all [P])
Stream B: T013, T014 (US2 — branch safety, markdown only)
Stream C: T043, T044, T045, T046, T047, T048 (US7 — skill frontmatter)

# Wave 2: After foundational completes
Stream D: T009, T010, T011, T012 (US1 — init profile)
Stream E: T015, T016, T017, T018, T019, T020, T021 (US3 — check/upgrade)
Stream F: T022-T034 (US4 — command quality)
Stream G: T035, T036, T037, T038, T039, T040 (US5 — deploy pipeline)
Stream H: T041, T042 (US6 — configure guard)
Stream I: T050, T051, T052, T053 (US8 — extensions/init)

# Wave 3: Final
Stream J: T054-T059 (Polish — after all stories complete)
```

---

## Implementation Strategy

### MVP First (US1 + US2 Only)

1. Complete Phase 1: Foundational (T001-T008)
2. Complete Phase 2: US1 — Production install (T009-T012)
3. Complete Phase 3: US2 — Branch safety (T013-T014)
4. **STOP and VALIDATE**: Build wheel, verify profiles bundled. Verify branch safety sections in all 5 commands.
5. This delivers the 2 CRITICAL fixes.

### Incremental Delivery

1. Foundational → US1 + US2 → **CRITICAL fixes deployed**
2. Add US3 + US4 → **HIGH/MEDIUM CLI and command fixes**
3. Add US5 + US6 → **Deployment pipeline and config hardening**
4. Add US7 → **Skill activation expanded (largest task by file count)**
5. Add US8 → **Extension and UX friction fixes**
6. Polish → **Final validation**

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- US7 (skill activation) is the highest file-count change (~72 files) but lowest risk (frontmatter only)
- FR-028 (permissions-bypass.json) is resolved — file doesn't exist on disk (research R9)
- Total new tests: ~18 (T006-T008, T010-T012, T019-T021, T038-T040, T042, T052-T053)
- Commit after each task or logical group
