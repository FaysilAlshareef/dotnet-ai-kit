# Tasks: Fix Tool Quality Issues

**Input**: Design documents from `/specs/004-fix-tool-issues/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included per constitution (TDD: Red-Green-Refactor).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new dependency and prepare project for changes

- [x] T001 Add `questionary>=2.0.0` to dev dependencies in `pyproject.toml`
- [x] T002 [P] Verify dev install works with `pip install -e ".[dev]"` and import questionary

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add shared pydantic models that multiple user stories depend on

- [x] T003 Add `DetectionSignal` pydantic model to `src/dotnet_ai_kit/models.py` with fields: pattern_name, signal_type (naming/code-pattern/structural/build-config), target_project_type, confidence (high/medium/low), weight, evidence, is_negative
- [x] T004 Add `DetectionScoreCard` pydantic model to `src/dotnet_ai_kit/models.py` with fields: project_type, positive_score, negative_score, net_score, signal_count
- [x] T005 [P] Add `hybrid` to valid project_type values in `DetectedProject.validate_project_type()` in `src/dotnet_ai_kit/models.py`
- [x] T006 [P] Add `confidence`, `confidence_score`, `user_override`, `top_signals` fields to `DetectedProject` model in `src/dotnet_ai_kit/models.py`
**Checkpoint**: Foundation ready — all new models available for user story implementation

---

## Phase 3: User Story 1 — Smart Project Detection (Priority: P1) MVP

**Goal**: Rewrite detection to use signal-based scoring of actual code patterns instead of name-first classification. Support `hybrid` type. Show detection summary with confidence. Allow user override.

**Independent Test**: Run detection against fixture projects representing each type (command, query, processor, gateway, hybrid) without naming hints and verify correct classification.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T008 [P] [US1] Write test for command-side detection by code patterns (Aggregate base class, Event publishing, no query handlers) in `tests/test_detection.py`
- [x] T009 [P] [US1] Write test for query-sql detection by code patterns (IRequestHandler for queries, hosted service event handlers, no command handlers) in `tests/test_detection.py`
- [x] T010 [P] [US1] Write test for query-cosmos detection by code patterns (IContainerDocument interface) in `tests/test_detection.py`
- [x] T011 [P] [US1] Write test for processor detection by code patterns (IHostedService + ServiceBusProcessor, event routing) in `tests/test_detection.py`
- [x] T012 [P] [US1] Write test for gateway detection by code patterns (ApiController + gRPC/HTTP clients, no direct DB) in `tests/test_detection.py`
- [x] T013 [P] [US1] Write test for hybrid detection when both command and query signals are strong in `tests/test_detection.py`
- [x] T014 [P] [US1] Write test for detection without naming hints (project named generically but code patterns are clear) in `tests/test_detection.py`
- [x] T015 [P] [US1] Write test for confidence scoring (high >0.8, medium >0.5, low <=0.5) in `tests/test_detection.py`
- [x] T016 [P] [US1] Write test for detection summary output format (classification + top signals + confidence) in `tests/test_detection.py`
- [x] T017 [P] [US1] Write test for architecture pattern detection (clean-arch, vsa, ddd, modular-monolith) by structure in `tests/test_detection.py`
- [x] T017b [P] [US1] Write test for controlpanel detection by code patterns (Blazor `.razor` files + `ResponseResult<T>`) in `tests/test_detection.py`
- [x] T017c [P] [US1] Write test for multi-project solution detection (each project classified independently) in `tests/test_detection.py`
- [x] T017d [P] [US1] Write test for non-standard framework fallback (no known patterns match → `generic` type with `low` confidence) in `tests/test_detection.py`

### Implementation for User Story 1

- [x] T018 [US1] Define signal pattern registry `_SIGNAL_PATTERNS` in `src/dotnet_ai_kit/detection.py` — list of (pattern_name, regex, target_project_type, signal_type, confidence, is_negative) tuples covering command, query-sql, query-cosmos, processor, gateway, controlpanel, hybrid signals per research.md R2
- [x] T019 [US1] Implement `_collect_signals()` function in `src/dotnet_ai_kit/detection.py` that scans all .cs files and returns list of `DetectionSignal` objects
- [x] T020 [US1] Implement `_score_candidates()` function in `src/dotnet_ai_kit/detection.py` that aggregates signals into `DetectionScoreCard` per project type, applying positive/negative weights
- [x] T021 [US1] Implement `_classify_project()` function in `src/dotnet_ai_kit/detection.py` that picks highest-scoring type (or `hybrid` if command+query both above threshold), computes confidence score, selects top 3 signals
- [x] T022 [US1] Refactor `_detect_microservice()` in `src/dotnet_ai_kit/detection.py` to use `_collect_signals()` → `_score_candidates()` → `_classify_project()` pipeline instead of name-first + pattern match
- [x] T023 [US1] Update `_detect_microservice_by_name()` in `src/dotnet_ai_kit/detection.py` to return naming signals (signal_type="naming") instead of directly returning project type — these feed into the scoring system as supplementary signals
- [x] T024 [US1] Refactor `_detect_generic()` in `src/dotnet_ai_kit/detection.py` to return structural signals for clean-arch, vsa, ddd, modular-monolith based on project references and actual layer structure (not just directory names)
- [x] T024b [US1] Add `rich.progress.Progress` spinner in `_collect_signals()` in `src/dotnet_ai_kit/detection.py` that shows "Scanning {n} files..." during file analysis
- [x] T025 [US1] Implement `_display_detection_summary()` function in `src/dotnet_ai_kit/detection.py` using `rich.panel.Panel` to render detection result per contracts/cli-detection-output.md format
- [x] T026 [US1] Implement `_prompt_override()` function in `src/dotnet_ai_kit/detection.py` that asks user "Is this correct? [Y/n/change]" and presents numbered type selection if user wants to override
- [x] T027 [US1] Update `detect_project()` public function in `src/dotnet_ai_kit/detection.py` to return enriched `DetectedProject` with signals, confidence, confidence_score, top_signals, and user_override fields
- [x] T028 [US1] Update `init` command in `src/dotnet_ai_kit/cli.py` to call `_display_detection_summary()` and `_prompt_override()` after detection, and save enriched project.yml with confidence and top_signals
- [x] T029 [US1] Update `_save_project()` in `src/dotnet_ai_kit/config.py` to serialize new DetectedProject fields (confidence, confidence_score, user_override, top_signals) to project.yml

**Checkpoint**: Detection correctly classifies command/query/processor/gateway/controlpanel/hybrid by code patterns. Multi-project solutions handled. Non-standard projects fall back gracefully. Summary displayed. User can override. All T008-T017d tests pass.

---

## Phase 4: User Story 2 — Permission Handling for Compound Commands (Priority: P2)

**Goal**: Fix permission configs so compound commands work, add pre-flight tool validation, guide AI to avoid `&&` chains.

**Independent Test**: Configure standard permissions, verify `gh pr create` works when gh is in PATH, verify clear error when gh is missing.

### Tests for User Story 2

- [x] T030 [P] [US2] Write test for `_validate_tools()` function — returns found/missing status for each referenced tool in `tests/test_cli.py`
- [x] T031 [P] [US2] Write test for pre-flight validation output format (tool name, status, install guidance) in `tests/test_cli.py`
- [x] T031b [P] [US2] Write test that AI guidance rule file exists in `rules/` and instructs sequential tool calls instead of `&&` chains
- [x] T031c [P] [US2] Write test that permission JSON patterns match expected space syntax format (`Bash(command *)`) and include `$schema` reference in `tests/test_cli.py`

### Implementation for User Story 2

- [x] T032 [US2] Implement `_validate_tools()` function in `src/dotnet_ai_kit/cli.py` that checks PATH for tools referenced in permission config (dotnet, git, gh, docker) using `shutil.which()`
- [x] T033 [US2] Call `_validate_tools()` during `init` and `configure` commands in `src/dotnet_ai_kit/cli.py` — show warnings for missing tools with install URLs
- [x] T034 [P] [US2] Fix `config/permissions-standard.json`: change all patterns from colon syntax `Bash(dotnet build:*)` to space syntax `Bash(dotnet build *)` per Claude Code official docs, add `"$schema": "https://json.schemastore.org/claude-code-settings.json"`, add `Bash(cd *)` pattern
- [x] T035 [P] [US2] Fix `config/permissions-full.json` with same colon→space syntax fix and `$schema` addition as permissions-standard.json
- [x] T035b [P] [US2] Fix `config/permissions-minimal.json` with same colon→space syntax fix and `$schema` addition
- [x] T036 [US2] Add or update a rule in `rules/` that instructs AI assistants to use sequential tool calls instead of `&&` chains, and to check tool availability before constructing commands

**Checkpoint**: Pre-flight tool validation works. Permission patterns are correct. AI guidance rule prevents compound command issues.

---

## Phase 5: User Story 3 — Interactive Configure with Selectable Choices (Priority: P3)

**Goal**: Replace plain-text prompts in configure command with interactive menus and multi-select checkboxes.

**Independent Test**: Run `dotnet-ai configure` and verify each option presents selectable choices instead of free-text input.

### Tests for User Story 3

- [x] T037 [P] [US3] Write test for configure with single-select permission level (mocking questionary/rich prompt) in `tests/test_cli.py`
- [x] T038 [P] [US3] Write test for configure with multi-select AI tools (mocking questionary checkbox) in `tests/test_cli.py`
- [x] T039 [P] [US3] Write test for configure `--minimal` flag bypasses interactive prompts in `tests/test_cli.py`
- [x] T039b [P] [US3] Write test for configure summary output table after save in `tests/test_cli.py`

### Implementation for User Story 3

- [x] T040 [US3] Replace permission level prompt in `configure` command in `src/dotnet_ai_kit/cli.py` with `rich.prompt.Prompt.ask()` using choices=["1", "2", "3"] with descriptions, showing current/default value per contracts/cli-configure-prompts.md
- [x] T041 [US3] Add AI tools multi-select using `questionary.checkbox()` in `configure` command in `src/dotnet_ai_kit/cli.py` with options for claude, cursor, copilot, codex, antigravity — pre-select currently configured tools
- [x] T042 [US3] Add command style single-select in `configure` command in `src/dotnet_ai_kit/cli.py` with choices full/short/both, examples, and current value highlighted
- [x] T043 [US3] Add default branch prompt with default value display in `configure` command in `src/dotnet_ai_kit/cli.py`
- [x] T044 [US3] Keep `--minimal` flag logic: skip interactive prompts, use defaults, only ask company name in `src/dotnet_ai_kit/cli.py`
- [x] T044b [US3] Add `--no-input` flag to `configure` command in `src/dotnet_ai_kit/cli.py` that requires all values via flags (`--company`, `--org`, `--branch`, `--permissions`, `--tools`, `--style`) and fails if required values are missing — for CI/CD pipelines
- [x] T045 [US3] Add configuration summary output after save (company, org, branch, permissions, tools, style) in `src/dotnet_ai_kit/cli.py` using `rich.table.Table`

**Checkpoint**: Configure command uses interactive menus. All options show descriptions and defaults. `--minimal` still works for CI.

---

## Phase 6: User Story 4 — Complete Plan Generation (Priority: P3)

**Goal**: Update plan generation templates to produce data models, contracts, and quickstart for complex features; lightweight plan for simple features.

**Independent Test**: Trigger plan generation for a feature with 3+ entities and verify data-model.md and contracts/ are produced.

### Implementation for User Story 4

- [x] T046 [US4] Update plan command template in `commands/` to add complexity analysis step that counts entities, integrations, and functional requirements from the spec
- [x] T047 [US4] Add complexity threshold logic to plan command template: if 3+ entities OR external integrations OR multi-repo → generate full artifacts; otherwise → lightweight plan only
- [x] T048 [US4] Update plan skill in `skills/` to include instructions for generating data-model.md from spec entities and contracts/ from interface requirements
- [x] T049 [US4] Add quickstart.md generation guidance to plan command template with implementation order, files to modify, and dev setup sections

**Checkpoint**: Plan generation produces appropriate artifacts based on feature complexity.

---

## Phase 7: User Story 5 — CLI UX Polish and Quality Audit (Priority: P3)

**Goal**: Follow clig.dev CLI UX best practices: progress indicators, next-command suggestions, `--json` output, `NO_COLOR` support, Ctrl-C handling, stderr for errors, exit code mapping. Plus fix known quality issues.

**Independent Test**: Run each CLI command and verify: spinner shown during detection, next-step suggested after completion, `--json` produces valid JSON, `NO_COLOR=1` disables colors, Ctrl-C exits cleanly, errors go to stderr, exit codes are mapped.

### Tests for User Story 5

- [x] T050 [P] [US5] Write test that `--json` flag produces valid JSON output for `init` and `check` commands in `tests/test_cli.py`
- [x] T050b [P] [US5] Write test that next-command suggestion appears after `init` completes in `tests/test_cli.py`
- [x] T050c [P] [US5] Write test that exit codes are non-zero for error cases (config error, detection failure) in `tests/test_cli.py`

### Implementation for User Story 5

- [x] T051 [US5] Add `--json` flag to `init`, `check`, `configure`, and `upgrade` commands in `src/dotnet_ai_kit/cli.py` — output valid JSON to stdout, suppress decorative text when flag is set
- [x] T052 [US5] Add next-command suggestions after CLI operations complete in `src/dotnet_ai_kit/cli.py`: after `init` → "Run `dotnet-ai configure` to customize settings", after `configure` → "Run `dotnet-ai check` to verify setup"
- [x] T053 [US5] Add `NO_COLOR` env var support in `src/dotnet_ai_kit/cli.py` — check `os.environ.get("NO_COLOR")` and configure `rich.console.Console(no_color=True)` when set
- [x] T054 [US5] Add Ctrl-C (SIGINT) handler in `src/dotnet_ai_kit/cli.py` — catch `KeyboardInterrupt` at top level, print clean exit message, suppress Python traceback
- [x] T055 [P] [US5] Route error messages to stderr in `src/dotnet_ai_kit/cli.py` — use `rich.console.Console(stderr=True)` for error output, keep stdout for data
- [x] T056 [P] [US5] Map exit codes in `src/dotnet_ai_kit/cli.py`: 0=success, 1=general error, 2=config error, 3=detection failed — use `raise typer.Exit(code=N)` or `sys.exit(N)`
- [x] T057 [US5] Review and improve error messages across all CLI commands in `src/dotnet_ai_kit/cli.py` — ensure each error includes what went wrong and how to fix it (per clig.dev: "Rewrite caught errors for humans")
- [x] T058 [P] [US5] Add `--dry-run` flag to `init`, `configure`, and `upgrade` commands in `src/dotnet_ai_kit/cli.py` that shows what would be done without making changes (per constitution V.Safety — `check` and `extension-list` are read-only and don't need it)
- [x] T059 [US5] Fix `$Number` positional parameter binding bug in `.specify/scripts/powershell/create-new-feature.ps1` — add `[Parameter(Position=0)]` to `$Number` or reorder parameters so `$FeatureDescription` binds first
- [x] T060 [US5] Run full test suite and fix any failures: `pytest tests/ -v`

**Checkpoint**: CLI follows clig.dev best practices. Progress indicators, next-step suggestions, `--json`, `NO_COLOR`, clean Ctrl-C, stderr errors, mapped exit codes all working. Script parameter binding fixed.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Validation across all user stories

- [x] T061 [P] Run `ruff check src/ tests/` and fix any linting issues
- [x] T062 [P] Run `ruff format --check src/ tests/` and fix any formatting issues
- [x] T063 Run `pytest --cov=dotnet_ai_kit` and verify test coverage for modified files
- [x] T064 Run quickstart.md validation — walk through implementation order and verify all described changes are implemented

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 (Detection) can proceed independently
  - US2 (Permissions) can proceed independently (no dependency on US1)
  - US3 (Configure) can proceed independently (no dependency on US1/US2)
  - US4 (Plan Generation) can proceed independently (template changes only)
  - US5 (Quality Audit) should run last (validates all other changes)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **US2 (P2)**: Can start after Phase 2 — No dependencies on other stories
- **US3 (P3)**: Can start after Phase 2 — No dependencies on other stories
- **US4 (P3)**: Can start after Phase 2 — No dependencies on other stories
- **US5 (P3)**: Should start after US1-US3 (applies cross-cutting UX to commands modified by other stories)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services/functions
- Core logic before CLI integration
- Story complete before moving to next priority

### Parallel Opportunities

- T001, T002: Setup tasks can run in parallel
- T003-T006: Foundational model tasks — T005/T006 are [P] (different fields/models)
- T008-T017d: All US1 test tasks can run in parallel (all in same file but independent test functions)
- T030-T031c: US2 test tasks can run in parallel
- T034-T035b: Permission JSON updates can run in parallel (3 files)
- T037-T039b: US3 test tasks can run in parallel
- T050-T050c: US5 test tasks can run in parallel
- T055-T056: US5 stderr/exit-code tasks can run in parallel
- US1, US2, US3, US4 can all be worked on in parallel after Phase 2

---

## Parallel Example: User Story 1

```
# Launch all tests for US1 together:
Task T008: "Command-side detection test in tests/test_detection.py"
Task T009: "Query-sql detection test in tests/test_detection.py"
Task T010: "Query-cosmos detection test in tests/test_detection.py"
Task T011: "Processor detection test in tests/test_detection.py"
Task T012: "Gateway detection test in tests/test_detection.py"
Task T013: "Hybrid detection test in tests/test_detection.py"
Task T014: "No-naming-hint detection test in tests/test_detection.py"
Task T015: "Confidence scoring test in tests/test_detection.py"
Task T016: "Summary output test in tests/test_detection.py"
Task T017: "Architecture pattern test in tests/test_detection.py"

# After tests written, implement in order:
Task T018: Signal pattern registry (foundation for all detection)
Task T019: Signal collection (reads files)
Task T020: Candidate scoring (aggregates signals)
Task T021: Classification (picks winner)
Task T022: Refactor _detect_microservice to use pipeline
Task T023-T24: Update naming/generic detection to return signals
Task T025-T26: Display summary + override prompt
Task T027-T29: Wire up public API + CLI integration
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational models (T003-T006)
3. Complete Phase 3: User Story 1 — Smart Detection (T008-T029)
4. **STOP and VALIDATE**: Run `pytest tests/test_detection.py -v` — all tests pass
5. Detection now works by code patterns with confidence scoring

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. User Story 1 (Detection) → Test → MVP!
3. User Story 2 (Permissions) → Test → Permissions fixed (critical format fix)
4. User Story 3 (Configure) → Test → UX improved
5. User Story 4 (Plan Generation) → Test → Plans complete
6. User Story 5 (CLI UX Polish) → Test → Professional CLI experience
7. Polish → Final validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- TDD: Write tests first, verify they fail, then implement
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
