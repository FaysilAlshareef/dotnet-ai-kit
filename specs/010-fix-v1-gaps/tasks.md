# Tasks: Fix v1.0 Gap Report Issues

**Input**: Design documents from `/specs/010-fix-v1-gaps/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: Tests included for Python code changes (FR-004, FR-005, FR-006) as the project uses pytest. No tests for Markdown-only changes.

**Organization**: Tasks grouped by user story. US1 = Project Knowledge (P1), US2 = Tool Consistency (P1), US3 = Knowledge Base & Discoverability (P2), US4 = Template Variables & Explicit Outputs (P2).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No project initialization needed — all changes fit existing structure. This phase handles quick, blocking fixes.

- [x] T001 [P] Rename skill `name` field from `dotnet-ai-controller-patterns` to `dotnet-ai-restful-controllers` in `skills/api/controller-patterns/SKILL.md` (FR-003)
- [x] T002 [P] Replace all `--preview` with `--dry-run` in `commands/add-aggregate.md` (FR-009)
- [x] T003 [P] Replace all `--preview` with `--dry-run` in `commands/add-entity.md` (FR-009)
- [x] T004 [P] Replace all `--preview` with `--dry-run` in `commands/add-event.md` (FR-009)
- [x] T005 [P] Replace all `--preview` with `--dry-run` in `commands/add-endpoint.md` (FR-009)
- [x] T006 [P] Replace all `--preview` with `--dry-run` in `commands/add-page.md` (FR-009)
- [x] T007 [P] Replace all `--preview` with `--dry-run` in `commands/add-crud.md` (FR-009)
- [x] T008 [P] Replace all `--preview` with `--dry-run` in `commands/add-tests.md` (FR-009)
- [x] T009 [P] Replace all `--preview` with `--dry-run` in `commands/docs.md` (FR-009)
- [x] T010 [P] Replace all `--preview` with `--dry-run` in `commands/explain.md` (FR-009)
- [x] T011 [P] Standardize `commands/checkpoint.md` to `--dry-run` only — remove `--preview` alias and all dual references (FR-009)
- [x] T012 [P] Standardize `commands/undo.md` to `--dry-run` only — remove `--preview` alias and all dual references (FR-009)
- [x] T013 [P] Standardize `commands/wrap-up.md` to `--dry-run` only — remove `--preview` alias and all dual references (FR-009)

**Checkpoint**: All 27 commands now use consistent `--dry-run` flag. Zero `--preview` references remain. Duplicate skill name resolved.

---

## Phase 2: Foundational (Python Code Changes)

**Purpose**: Core Python changes that must complete before new content depends on them.

**CRITICAL**: Run `pytest` after each task to ensure no regressions.

- [x] T014 Remove `CodeRabbitConfig` class (lines 156-178) and `IntegrationsConfig` class (lines 181-188) from `src/dotnet_ai_kit/models.py` (FR-004)
- [x] T015 Remove `integrations` field (lines 212-215) from `DotnetAiConfig` in `src/dotnet_ai_kit/models.py` and add `model_config = ConfigDict(extra="ignore")` to silently handle existing config files with `integrations:` section (FR-004)
- [x] T016 Add `domain: str = Field(default="Domain", description="Domain name for template rendering.")` to `NamingConfig` class in `src/dotnet_ai_kit/models.py` (FR-004/FR-006)
- [x] T017 Update `tests/test_cli.py` to remove any references to `CodeRabbitConfig` or `IntegrationsConfig` and verify config loading still works with `extra="ignore"` (FR-004)
- [x] T018 Wire `NamingConfig.domain` to template context in `src/dotnet_ai_kit/copier.py` — replace hardcoded `"Domain": "Domain"` (line 367) with `"Domain": config.naming.domain` and `"domain": "domain"` (line 368) with `"domain": config.naming.domain.lower()` (FR-006)
- [x] T019 Add tests in `tests/test_copier.py` verifying: (a) default domain="Domain" produces same output as before, (b) custom domain="Draw" produces `Draw`/`draw` in template context (FR-006)
- [x] T020 Add `min_cli_version` validation to `install_extension()` in `src/dotnet_ai_kit/extensions.py` — compare `manifest.min_cli_version` against `dotnet_ai_kit.__version__` using tuple version comparison, raise `ExtensionError` if CLI version is too old (FR-005)
- [x] T021 Add hook validation in `_validate_manifest_data()` in `src/dotnet_ai_kit/extensions.py` — ensure hooks dict keys are valid lifecycle events (`after_install`, `after_remove`) and values are lists of strings (shell commands) (FR-005)
- [x] T022 Add hook execution in `install_extension()` in `src/dotnet_ai_kit/extensions.py` — after successful install, execute `after_install` hooks via `subprocess.run()` with list args parsed by `shlex.split()` (no `shell=True`). On Windows, use the command string directly with `shell=False` and proper quoting (FR-005)
- [x] T023 Add tests in `tests/test_extensions.py` for: (a) `min_cli_version` validation rejects too-new version, (b) `min_cli_version` accepts matching or older version, (c) hook validation rejects invalid hook keys, (d) `after_install` hooks execute on successful install (FR-005)
- [x] T024 Run full test suite: `pytest --cov=dotnet_ai_kit` — verify all existing + new tests pass with no regressions

**Checkpoint**: All Python changes complete. Models cleaned up, NamingConfig wired to templates, extension hooks functional. Test suite green.

---

## Phase 3: User Story 1 — Project Knowledge Persists Across Sessions (Priority: P1)

**Goal**: Developers can run `/dai.learn` to generate a persistent project constitution that is loaded in subsequent sessions.

**Independent Test**: Run `/dai.learn` on a .NET project, verify `.dotnet-ai-kit/memory/constitution.md` is generated with accurate project details.

### Implementation for User Story 1

- [x] T025 [US1] Create `commands/learn.md` — the `/dai.learn` slash command (27th command). Must: (a) chain `/dai.detect` for project scan, (b) read project files (csproj, domain classes, DI registration, existing patterns), (c) generate `.dotnet-ai-kit/memory/constitution.md` with architecture, domain model, conventions, packages, and patterns sections, (d) support `--update` flag to refresh existing constitution, (e) support `--dry-run` flag, (f) stay under 200 lines, (g) document that `.dotnet-ai-kit/memory/constitution.md` should be loaded by AI sessions at startup — add a note in the command output suggesting the user add it as a rule or always-loaded file in their AI tool configuration (FR-001)
- [x] T026 [US1] Update `commands/plan.md` — wire Constitution Check gate (Step 3) to read `.dotnet-ai-kit/memory/constitution.md` instead of dead `.specify/memory/constitution.md` reference. If file doesn't exist, skip with warning "Project constitution not found — run /dai.learn to generate" (FR-002)
- [x] T027 [US1] Update `skills/workflow/plan-templates/SKILL.md` — update Constitution Check sections (Generic mode ~line 21, Microservice mode ~line 67) to reference `.dotnet-ai-kit/memory/constitution.md` (FR-002)

**Checkpoint**: `/dai.learn` command exists and can generate project constitution. `/dai.plan` constitution check gate wired to correct file.

---

## Phase 4: User Story 2 — Tool Consistency and Correctness (Priority: P1)

**Goal**: No duplicate skill names, no dead references, extension hooks work, standardized flags.

**Independent Test**: Parse all skill YAML frontmatter and verify unique names. Run extension with hooks and verify execution.

### Implementation for User Story 2

> All consistency fixes for this story were completed in Phase 1 (T001-T013) and Phase 2 (T014-T024). This phase runs quick spot-checks; T041 in Phase 7 repeats these as part of comprehensive final verification.

- [x] T028 [US2] Verify SC-002: Run `grep -r "^name:" skills/ | sort` and confirm zero duplicate names across all 106 skills
- [x] T029 [US2] Verify SC-003: Run `grep -r "\-\-preview" commands/` and confirm zero results
- [x] T030 [US2] Verify FR-004: Run `grep -r "CodeRabbitConfig\|IntegrationsConfig" src/` and confirm zero results
- [x] T030b [US2] Verify FR-011: Confirm `skills/microservice/controlpanel/response-result/SKILL.md` is listed in `agents/controlpanel-architect.md` Skills Loaded section

**Checkpoint**: All consistency and correctness issues verified as resolved.

---

## Phase 5: User Story 3 — Complete Knowledge Base and Discoverability (Priority: P2)

**Goal**: Knowledge docs exist for all core architectures. Plugin manifest enumerates all tool components.

**Independent Test**: Verify knowledge docs exist for CQRS, DDD, Clean Arch, VSA. Verify plugin.json lists all 27 commands, 13 agents, 106 skills, 4 hooks.

### Implementation for User Story 3

- [x] T031 [P] [US3] Create `knowledge/cqrs-patterns.md` — CQRS reference doc (~200 lines). Cover: command/query separation, MediatR handlers, pipeline behaviors, event sourcing integration. Follow format of existing `knowledge/event-sourcing-flow.md` (FR-007)
- [x] T032 [P] [US3] Create `knowledge/ddd-patterns.md` — DDD reference doc (~200 lines). Cover: aggregates, entities, value objects, domain events, bounded contexts, repositories. Follow existing knowledge doc format (FR-007)
- [x] T033 [P] [US3] Create `knowledge/clean-architecture-patterns.md` — Clean Architecture reference doc (~200 lines). Cover: layer separation (Domain, Application, Infrastructure, API), dependency rule, use cases, ports/adapters. Follow existing knowledge doc format (FR-007)
- [x] T034 [P] [US3] Create `knowledge/vsa-patterns.md` — VSA reference doc (~200 lines). Cover: feature folders, handler-per-endpoint, minimal abstraction, slice independence. Follow existing knowledge doc format (FR-007)
- [x] T034b [P] [US3] Create `knowledge/modular-monolith-patterns.md` — Modular Monolith reference doc (~200 lines). Cover: module boundaries, inter-module communication, shared kernel, independent deployment. Follow existing knowledge doc format (FR-007)
- [x] T035 [US3] Expand `.claude-plugin/plugin.json` with full catalog — add `commands` array (27 entries with name, alias, description, category), `agents` array (13 entries with name, role), `skills` object (grouped by category, 106 total), `hooks` array (4 entries with name, type, behavior) (FR-008)

**Checkpoint**: Knowledge directory has 15+ docs covering all supported architectures. Plugin manifest is a complete catalog.

---

## Phase 6: User Story 4 — Template Variables and Explicit Outputs (Priority: P2)

**Goal**: Template rendering uses configurable domain names. `/dai.specify` explicitly outputs service-map.md for microservice features.

**Independent Test**: Scaffold a project with `naming.domain: Draw` in config and verify namespaces. Run `/dai.specify` in microservice mode and verify service-map.md is documented as output.

### Implementation for User Story 4

> NamingConfig wiring (FR-006) was completed in Phase 2 (T016, T018, T019). This phase handles command updates.

- [x] T036 [US4] Update `commands/specify.md` — add explicit step after microservice mode section (~line 115) to create `service-map.md` in the feature directory. Document the expected content: Mermaid diagram of service dependencies, per-service change summary, affected repos list (FR-010)

**Checkpoint**: `/dai.specify` explicitly generates service-map.md for microservice features. Template variables use config values.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates, constitution sync, final verification.

- [x] T037 [P] Update `CLAUDE.md` — change command count from 26 to 27, add `/dotnet-ai.learn` row to commands table with alias `/dai.learn` and category "Project", update knowledge doc count from 11 to 15
- [x] T038 [P] Update `planning/12-version-roadmap.md` — reflect 27 commands (was 26), 15 knowledge docs (was 11), add `/dai.learn` to v1.0 deliverables list
- [x] T039 [P] Update `.specify/memory/constitution.md` — change Technology Constraints section: commands 26→27, knowledge documents 11→15. Increment version to 1.0.3 with amendment note
- [x] T040 Update `templates/config-template.yml` (if exists) — add `naming.domain` field with documentation comment explaining its purpose
- [x] T041 Run full verification from quickstart.md: (a) `grep -r "^name:" skills/` for duplicates, (b) `grep -r "\-\-preview" commands/` for stale flags, (c) `grep -r "CodeRabbitConfig\|IntegrationsConfig" src/` for dead models, (d) `pytest --cov=dotnet_ai_kit` for full test suite
- [x] T042 Run quickstart.md validation — walk through all verification steps and confirm all pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — all tasks are parallel, independent file edits
- **Phase 2 (Foundational)**: T014→T015→T016 sequential (same file), T018 depends on T016, T020→T021→T022 sequential (same file, extensions.py) but parallel with T014-T019 group
- **Phase 3 (US1)**: Depends on Phase 1 completion (T001 for skill name, T002-T013 for `--dry-run`)
- **Phase 4 (US2)**: Depends on Phase 1 + Phase 2 completion (verification of earlier work)
- **Phase 5 (US3)**: T031-T034 independent (parallel), T035 independent of knowledge docs
- **Phase 6 (US4)**: Depends on Phase 2 (T016, T018 for NamingConfig wiring)
- **Phase 7 (Polish)**: Depends on all prior phases

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 1 — no dependency on Python changes
- **US2 (P1)**: Verification only — depends on Phase 1 + Phase 2
- **US3 (P2)**: Fully independent — can start after Phase 1
- **US4 (P2)**: T036 independent of Python changes

### Within Each User Story

- US1: T025 (learn command) → T026 (plan.md) → T027 (plan-templates) — sequential, references must align
- US3: T031-T034 parallel (independent files), then T035 (manifest needs final command list)
- US4: T036 standalone

### Parallel Opportunities

- **Phase 1**: All 13 tasks (T001-T013) can run in parallel — each touches a different file
- **Phase 2**: T020→T021→T022 group (extensions.py, sequential) can run in parallel with T014→T018→T019 group (models/copier)
- **Phase 3 + Phase 5**: Can run in parallel — US1 (commands) and US3 (knowledge docs) touch different files
- **Phase 5**: T031-T034 all parallel (4 independent knowledge docs)
- **Phase 7**: T037-T039 all parallel (different files)

---

## Parallel Example: Phase 1 (All 13 tasks)

```text
# Launch all Phase 1 tasks together (all different files):
Task T001: Rename skill name in skills/api/controller-patterns/SKILL.md
Task T002: --preview → --dry-run in commands/add-aggregate.md
Task T003: --preview → --dry-run in commands/add-entity.md
Task T004: --preview → --dry-run in commands/add-event.md
Task T005: --preview → --dry-run in commands/add-endpoint.md
Task T006: --preview → --dry-run in commands/add-page.md
Task T007: --preview → --dry-run in commands/add-crud.md
Task T008: --preview → --dry-run in commands/add-tests.md
Task T009: --preview → --dry-run in commands/docs.md
Task T010: --preview → --dry-run in commands/explain.md
Task T011: --dry-run standardization in commands/checkpoint.md
Task T012: --dry-run standardization in commands/undo.md
Task T013: --dry-run standardization in commands/wrap-up.md
```

## Parallel Example: Phase 5 (Knowledge Docs)

```text
# Launch all 4 knowledge docs together:
Task T031: Create knowledge/cqrs-patterns.md
Task T032: Create knowledge/ddd-patterns.md
Task T033: Create knowledge/clean-architecture-patterns.md
Task T034: Create knowledge/vsa-patterns.md
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only)

1. Complete Phase 1: Quick fixes (T001-T013) — ~15 min
2. Complete Phase 2: Python changes (T014-T024) — ~45 min
3. Complete Phase 3: `/dai.learn` command (T025-T027) — ~30 min
4. Complete Phase 4: Verification (T028-T030) — ~5 min
5. **STOP and VALIDATE**: Tool consistency fixed, project memory working

### Incremental Delivery

1. Phase 1 + 2 → Foundation ready (consistency + Python fixes)
2. Phase 3 (US1) → Project constitution system working (MVP!)
3. Phase 4 (US2) → All correctness verified
4. Phase 5 (US3) → Knowledge base complete, plugin discoverable
5. Phase 6 (US4) → Template variables configurable, service-map explicit
6. Phase 7 → Documentation updated, constitution synced

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- FR-011 confirmed already resolved — no task needed
- Run `pytest` after Phase 2 to catch regressions early
- Constitution path is `.dotnet-ai-kit/memory/constitution.md` (mirrors speckit pattern)
- Commit after each phase completion
