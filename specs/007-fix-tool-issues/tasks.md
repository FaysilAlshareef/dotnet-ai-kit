# Tasks: Fix All 25 Identified Tool Issues

**Input**: Design documents from `/specs/007-fix-tool-issues/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: Tests are included as they are part of the existing pytest suite that must be maintained.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: Verify environment and branch readiness

- [x] T001 Verify branch `007-fix-tool-issues` is checked out and clean
- [x] T002 [P] Run `pytest` to confirm all existing tests pass before changes
- [x] T003 [P] Run `ruff check src/ tests/` to confirm no existing lint issues

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No blocking shared infrastructure needed. All user stories modify independent files and can proceed directly after setup.

**Checkpoint**: Setup verified — user story implementation can begin.

---

## Phase 3: User Story 1 - Tool Init Copies Skills and Agents (Priority: P1)

**Goal**: Add `copy_skills()` and `copy_agents()` functions to `copier.py` and call them from `init()` and `upgrade()` in `cli.py`. Skills and agents are git-tracked (committed).

**Independent Test**: Run init on a fresh `tmp_path` project, verify `.claude/skills/` and `.claude/agents/` directories exist with correct file structure.

### Implementation for User Story 1

- [x] T004 [US1] Add `copy_skills()` function to `src/dotnet_ai_kit/copier.py` — recursively copy all files in `skills/` preserving directory structure (each skill has only SKILL.md per subfolder), following `copy_rules()` pattern (lines 132-165)
- [x] T005 [US1] Add `copy_agents()` function to `src/dotnet_ai_kit/copier.py` — flat copy of `agents/*.md` files, following `copy_rules()` pattern
- [x] T006 [US1] Add `_find_skills_source()` helper to `src/dotnet_ai_kit/cli.py` — resolve skills directory path from package, following `_find_commands_source()` pattern
- [x] T007 [P] [US1] Add `_find_agents_source()` helper to `src/dotnet_ai_kit/cli.py` — resolve agents directory path from package, following `_find_commands_source()` pattern
- [x] T008 [US1] Update `init()` in `src/dotnet_ai_kit/cli.py` — call `copy_skills()` and `copy_agents()` after `copy_rules()` call (after line 379), for each configured AI tool
- [x] T009 [US1] Update `upgrade()` in `src/dotnet_ai_kit/cli.py` — call `copy_skills()` and `copy_agents()` in upgrade flow (after line 777), with backup of existing directories before overwrite
- [x] T010 [US1] Add tests for `copy_skills()` in `tests/test_copier.py` — verify recursive directory structure preservation, file count, content, and that re-running overwrites existing `.claude/skills/` directory with latest version
- [x] T011 [US1] Add tests for `copy_agents()` in `tests/test_copier.py` — verify flat copy of 13 agent files and that re-running overwrites existing `.claude/agents/` directory
- [x] T012 [US1] Add test for `init()` with skills/agents in `tests/test_cli.py` — verify init creates `.claude/skills/` and `.claude/agents/` directories, including overwrite of pre-existing directories

**Checkpoint**: After T012, run `pytest tests/test_copier.py tests/test_cli.py` — all new and existing tests green.

---

## Phase 4: User Story 2 - Commands Enforce Correct Architectural Patterns (Priority: P1)

**Goal**: Update command markdown files to always load configuration/DI skills, load specialist agents per repo type, prevent entity generation on command side, and fix related command issues.

**Independent Test**: Read updated `implement.md` and verify always-loaded skills list includes `configuration` and `dependency-injection`. Read `tasks.md` and verify Phase 2 constraint text. Read `implement.md` and verify agent loading directives.

### Implementation for User Story 2

- [x] T013 [US2] Update `commands/implement.md` Step 2 — add always-loaded skills: `skills/core/configuration/SKILL.md` and `skills/core/dependency-injection/SKILL.md` to the list before per-task-type skills (around line 30)
- [x] T014 [US2] Update `commands/implement.md` Step 2 — add agent loading section: "For each repo type, also read the specialist agent: command → `agents/command-architect.md`, query → `agents/query-architect.md`, processor → `agents/processor-architect.md`, gateway → `agents/gateway-architect.md`, controlpanel → `agents/controlpanel-architect.md`"
- [x] T015 [P] [US2] Update `commands/tasks.md` Phase 2 (Command Side) — add constraint: "CONSTRAINT: Command side is event-sourced. Generate ONLY aggregates, events, value objects, enums, and domain exceptions. NEVER create entities, projections, read models, or lookup tables. If the command side needs to query external state, add a gRPC client call task in Infrastructure tasks."
- [x] T016 [P] [US2] Update `commands/tasks.md` — add `[P]` marker documentation: "`[P]` means this task can execute in parallel with other `[P]` tasks in the same phase — it modifies different files and has no dependencies on incomplete tasks within the phase."
- [x] T017 [P] [US2] Update `commands/plan.md` Step 3 (Constitution Check Gate) — make the gate optional: "If `.specify/memory/constitution.md` does not exist, skip this gate with a warning: 'Constitution file not found — skipping compliance check.' Continue to Phase 0."
- [x] T018 [P] [US2] Update `commands/analyze.md` — remove Pass 8 (Event Catalogue) section entirely (lines 91-95). Event information is derived from code at analysis runtime.

**Checkpoint**: After T018, verify each modified command file is under 200 lines. Read them to confirm changes are correct.

---

## Phase 5: User Story 3 - Config Template and Hooks Work Correctly (Priority: P2)

**Goal**: Fix the YAML structure bug in config template, fix the find command in pre-commit hook, and correct the AI tools comment.

**Independent Test**: Load the fixed config template through `DotnetAiConfig` pydantic model — it should validate without errors. Run the hook's find command on a directory with both `.sln` and `.csproj` files.

### Implementation for User Story 3

- [x] T019 [P] [US3] Fix `templates/config-template.yml` line 54 — change `permissions:\n  level: "standard"` to `permissions_level: "standard"` (flat key matching `DotnetAiConfig.permissions_level` field)
- [x] T020 [P] [US3] Fix `templates/config-template.yml` line 62 — change comment from `# Supported: claude, cursor, copilot, codex, antigravity` to `# Supported: claude`
- [x] T021 [P] [US3] Fix `hooks/pre-commit-lint.sh` line 34 — change `find . -maxdepth 3 -name "*.sln" -o -name "*.csproj"` to `find . -maxdepth 3 \( -name "*.sln" -o -name "*.csproj" \)`
- [x] T022 [US3] Add test in `tests/test_config.py` — load the config template through `DotnetAiConfig` model and verify it validates successfully (may need to fill required fields)

**Checkpoint**: After T022, config template passes pydantic validation. Hook find command returns both file types.

---

## Phase 6: User Story 4 - Feature Numbering and Cross-Repo Tracking (Priority: P2)

**Goal**: Enforce per-repo feature numbering starting at 001 and add spec-link generation for cross-repo features.

**Independent Test**: Read `specify.md` and verify numbering logic is explicit about per-repo scope. Read `tasks.md` and verify spec-link generation step exists.

### Implementation for User Story 4

- [x] T023 [US4] Update `commands/specify.md` Step 3 — add explicit text: "Feature numbers are per-repo. Scan ONLY the current repo's `.dotnet-ai-kit/features/` directory. Do not inherit or reference numbers from other repos. If no features exist in this repo, start at 001."
- [x] T024 [US4] Update `commands/tasks.md` — add a "Cross-Repo Feature Tracking" step after task generation: "For microservice mode, if tasks span multiple repos: create `spec-link.md` in each affected secondary repo's `.dotnet-ai-kit/features/{feature-name}/` directory containing: feature name, source repo, primary spec path, creation date."

**Checkpoint**: After T024, verify numbering and cross-repo instructions are clear and unambiguous.

---

## Phase 7: User Story 5 - Robust Extension and Template System (Priority: P3)

**Goal**: Fix Jinja2 silent failures, add extension install cleanup, add file locking for registry, support hybrid project type, validate repo paths, and standardize exit codes.

**Independent Test**: Render a Jinja2 template with a missing variable — should raise error. Simulate extension install failure — no partial files should remain.

### Implementation for User Story 5

- [x] T025 [P] [US5] Fix `src/dotnet_ai_kit/copier.py` line 30 — change `jinja2.Undefined` to `jinja2.StrictUndefined` in `render_template()` function
- [x] T026 [P] [US5] Update `src/dotnet_ai_kit/models.py` — ensure `"hybrid"` is included in the valid `project_type` allowed values (line 312 in models.py)
- [x] T027 [US5] Update `src/dotnet_ai_kit/cli.py` — add `"hybrid"` to the `MICROSERVICE_TYPES` set (around line 277-285)
- [x] T028 [US5] Add repo path validation in `src/dotnet_ai_kit/models.py` `ReposConfig` — add `@field_validator` for command, query, processor, gateway, controlpanel fields: value must be None, start with `github:`, or be a non-empty string (local path)
- [x] T029 [US5] Update `src/dotnet_ai_kit/extensions.py` install function — wrap `shutil.copytree()` in try/except; on failure after copy, call `shutil.rmtree()` on destination to clean up partial state
- [x] T030 [US5] Add file locking to `src/dotnet_ai_kit/extensions.py` — add `filelock` import; wrap `_load_extensions_registry()` → modify → `_save_extensions_registry()` in `filelock.FileLock(registry_path.with_suffix(".lock"))`
- [x] T031 [US5] Add `filelock` to `pyproject.toml` dependencies
- [x] T032 [US5] Standardize exit codes in `src/dotnet_ai_kit/cli.py` — audit all `raise typer.Exit()` calls (~15-20 instances across init, check, configure, upgrade, extension-* functions): normalize to code=1 for user input errors, code=2 for config/file errors, code=3 for missing dependencies. Only fix parameter values, do not refactor surrounding code.
- [x] T033 [US5] Add test for Jinja2 StrictUndefined in `tests/test_copier.py` — verify missing variable raises `jinja2.UndefinedError`
- [x] T034 [P] [US5] Add test for extension cleanup in `tests/test_extensions.py` — simulate copytree failure, verify destination directory is cleaned up
- [x] T035 [P] [US5] Add test for repo path validation in `tests/test_models.py` — verify valid paths pass, invalid paths raise ValidationError

**Checkpoint**: After T035, run `pytest` — all tests green. Extension install is transactional. Template rendering is strict.

---

## Phase 8: User Story 6 - Missing Skills, Rules, and Documentation (Priority: P3)

**Goal**: Create new rules (configuration, testing), new skills (error-handling, event-versioning), update query-architect agent for Cosmos routing, and fix SaveChangesAsync consistency.

**Independent Test**: Verify each new file exists, is under the token budget, and contains the expected patterns.

### Implementation for User Story 6

- [x] T036 [P] [US6] Create `rules/configuration.md` — enforce Options pattern (`IOptions<T>`, `IOptionsSnapshot<T>`, `IOptionsMonitor<T>`), require `ValidateDataAnnotations()` + `ValidateOnStart()`, forbid raw `IConfiguration` injection in services. Under 100 lines.
- [x] T037 [P] [US6] Create `rules/testing.md` — enforce test naming `{Method}_{Scenario}_{ExpectedResult}`, arrange-act-assert structure, aggregate testing patterns (create via factory, apply events, verify state), event handler testing patterns (create entity, apply event, verify projection). Under 100 lines.
- [x] T038 [P] [US6] Create `skills/core/error-handling/SKILL.md` — cover: domain exceptions inheriting `IProblemDetailsProvider`, gRPC `RpcException` mapping via interceptors, structured error responses with problem details, exception hierarchy for CQRS services. Under 400 lines.
- [x] T039 [P] [US6] Create `skills/microservice/command/event-versioning/SKILL.md` — cover: upcasting patterns for event schema evolution, versioned event data classes with backward-compatible field additions (default values), event store migration strategies, Event<TData> schema evolution. Under 400 lines.
- [x] T040 [US6] Update `agents/query-architect.md` — add Cosmos routing guidance in Boundaries section: "For Cosmos DB query services, delegate to `agents/cosmos-architect.md` which specializes in partition strategies, transactional batches, and Cosmos-specific repository patterns."
- [x] T041 [US6] Fix SaveChangesAsync consistency — grep all 104+ existing skill files in `skills/` for `SaveChangesAsync` and ensure every instance passes `cancellationToken` as parameter. Only fix parameter passing; do not refactor surrounding skill content or structure.
- [x] T042 [US6] Verify all new rules are under 100 lines: `wc -l rules/configuration.md rules/testing.md`
- [x] T043 [US6] Verify all new skills are under 400 lines: `wc -l skills/core/error-handling/SKILL.md skills/microservice/command/event-versioning/SKILL.md`

**Checkpoint**: After T043, all new files exist and comply with token budgets. SaveChangesAsync is consistent across all skills.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup across all changes

- [x] T044 Run full test suite: `pytest --cov=dotnet_ai_kit` — all tests pass with coverage report
- [x] T045 [P] Run linter: `ruff check src/ tests/` — no errors
- [x] T046 [P] Run formatter: `ruff format --check src/ tests/` — no formatting issues
- [x] T047 Verify all 25 issues from spec FR-001 through FR-025 are addressed — cross-reference each FR with its implementing task
- [x] T048 Update `.claude-plugin/plugin.json` if skill or agent counts changed — update description counts
- [x] T049 Update `.specify/memory/constitution.md` Technology Constraints — change "6 rules" to "9 rules", "104 skills" to "106 skills". Increment patch version in Sync Impact Report header.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: No blocking prerequisites
- **User Story 1 (Phase 3)**: Can start immediately — modifies `copier.py` and `cli.py`
- **User Story 2 (Phase 4)**: Can start immediately — modifies only `commands/*.md` files (no overlap with US1)
- **User Story 3 (Phase 5)**: Can start immediately — modifies `templates/` and `hooks/` (no overlap)
- **User Story 4 (Phase 6)**: Depends on US2 (T015, T016 modify `commands/tasks.md` — T024 also modifies it)
- **User Story 5 (Phase 7)**: Can start immediately — modifies `copier.py` (T025 modifies different function than US1), `models.py`, `extensions.py`
- **User Story 6 (Phase 8)**: Can start immediately — creates new files only (no overlap)
- **Polish (Phase 9)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Independent — no dependencies on other stories
- **US2 (P1)**: Independent — no dependencies on other stories
- **US3 (P2)**: Independent
- **US4 (P2)**: Soft dependency on US2 (both modify `commands/tasks.md` — coordinate edits)
- **US5 (P3)**: Independent (T025 modifies `copier.py` `render_template()` while US1 adds new functions — no conflict)
- **US6 (P3)**: Independent — only creates new files and modifies `agents/query-architect.md`

### Parallel Opportunities

**Maximum parallelism**: US1 + US2 + US3 + US5 + US6 can all start simultaneously (5 streams).

```
Phase 1 (Setup): T001 → T002 ∥ T003
                            ↓
Phase 3 (US1): T004 → T005∥T006∥T007 → T008 → T009 → T010∥T011 → T012
Phase 4 (US2): T013 → T014 ∥ T015∥T016∥T017∥T018
Phase 5 (US3): T019 ∥ T020 ∥ T021 → T022
Phase 7 (US5): T025∥T026 → T027∥T028 → T029 → T030 → T031 → T032 → T033∥T034∥T035
Phase 8 (US6): T036 ∥ T037 ∥ T038 ∥ T039 → T040 → T041 → T042∥T043
                            ↓
Phase 6 (US4): T023 → T024 (after US2 tasks on tasks.md complete)
                            ↓
Phase 9 (Polish): T044 → T045∥T046 → T047 → T048 → T049
```

---

## Parallel Example: User Story 1

```
# Launch in parallel (different files):
Task T005: "Add copy_agents() to copier.py"
Task T006: "Add _find_skills_source() to cli.py"
Task T007: "Add _find_agents_source() to cli.py"

# Then sequential (same files, dependencies):
Task T008: "Update init() in cli.py" (depends on T006, T007)
Task T009: "Update upgrade() in cli.py" (depends on T008)

# Tests in parallel:
Task T010: "Test copy_skills()"
Task T011: "Test copy_agents()"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 3: User Story 1 (init copies skills/agents) — root cause fix
3. Complete Phase 4: User Story 2 (commands enforce patterns) — prevention fix
4. **STOP and VALIDATE**: Run tests, verify init works, verify command files are correct
5. This alone fixes the most impactful issues (#3, #4, #5, #6, #7, #8)

### Incremental Delivery

1. Setup → US1 + US2 → Validate (MVP: 9 issues fixed)
2. Add US3 → Validate (12 issues fixed: bugs)
3. Add US4 → Validate (14 issues: numbering + cross-repo)
4. Add US5 → Validate (20 issues: robustness)
5. Add US6 → Validate (25 issues: all fixed)
6. Polish → Final validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US1 and US2 are both P1 priority — implement both before moving to P2
- US4 has a soft dependency on US2 because both modify `commands/tasks.md` — do US2 first
- All new rules must be under 100 lines, all new skills under 400 lines
- Commit after each user story checkpoint for safe rollback points
