# Tasks: dotnet-ai-kit v1.0 — Foundation Release

**Input**: Design documents from `/specs/001-v1-foundation-release/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Tests are included for the Python CLI modules (pytest). Knowledge base content (rules, skills, commands) is validated by token budget checks in the Polish phase.

**Organization**: Tasks are grouped by user story. The Foundational phase builds the shared knowledge base (rules, agents, skills, knowledge docs) that ALL user stories depend on.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **CLI source**: `src/dotnet_ai_kit/`
- **Knowledge base**: `rules/`, `agents/`, `skills/`, `commands/`, `knowledge/`
- **Templates**: `templates/`
- **Config**: `config/`
- **Tests**: `tests/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Python package structure and project initialization

- [x] T001 Create pyproject.toml with package metadata (name: dotnet-ai-kit, entry: dotnet-ai, deps: typer, pydantic, jinja2, rich, pyyaml, pytest-dev) in pyproject.toml
- [x] T002 Create Python package init with version string in src/dotnet_ai_kit/__init__.py
- [x] T003 [P] Create directory structure: rules/, agents/, skills/ (22 subdirs), commands/, knowledge/, templates/, config/, tests/ at repository root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared knowledge base that ALL user stories depend on. Rules, agents, skills, and knowledge docs form the content backbone of the tool.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Rules (6 files, source: planning/05-rules-design.md)

- [x] T004 [P] Create naming conventions rule (company-agnostic, mode-aware, ~80 lines) in rules/naming.md
- [x] T005 [P] Create C# coding style rule (version-aware, no force-upgrade, ~60 lines) in rules/coding-style.md
- [x] T006 [P] Create localization rule (resource files, conditional on project usage, ~40 lines) in rules/localization.md
- [x] T007 [P] Create error handling rule (mode-aware: ProblemDetails/gRPC/Result pattern, ~55 lines) in rules/error-handling.md
- [x] T008 [P] Create architecture rule (multi-architecture layer boundaries, ~80 lines) in rules/architecture.md
- [x] T009 [P] Create existing projects rule (detect-respect-extend, never refactor, ~65 lines) in rules/existing-projects.md

### Agents (13 files, source: planning/03-agents-design.md)

- [x] T010 [P] Create dotnet-architect agent (generic .NET architecture, 10 skills, boundaries) in agents/dotnet-architect.md
- [x] T011 [P] Create api-designer agent (REST API design, 14 skills, boundaries) in agents/api-designer.md
- [x] T012 [P] Create ef-specialist agent (EF Core & data access, 9 skills, boundaries) in agents/ef-specialist.md
- [x] T013 [P] Create devops-engineer agent (CI/CD, Docker, K8s, observability, 10 skills) in agents/devops-engineer.md
- [x] T014 [P] Create command-architect agent (event-sourced commands, 13 skills) in agents/command-architect.md
- [x] T015 [P] Create query-architect agent (SQL query side, 11 skills) in agents/query-architect.md
- [x] T016 [P] Create cosmos-architect agent (Cosmos DB query side, 11 skills) in agents/cosmos-architect.md
- [x] T017 [P] Create processor-architect agent (background processing, 9 skills) in agents/processor-architect.md
- [x] T018 [P] Create gateway-architect agent (REST gateway, 10 skills) in agents/gateway-architect.md
- [x] T019 [P] Create controlpanel-architect agent (Blazor WASM, 5 skills) in agents/controlpanel-architect.md
- [x] T020 [P] Create test-engineer agent (testing across all types, 6 skills) in agents/test-engineer.md
- [x] T021 [P] Create reviewer agent (code review, 4 skills) in agents/reviewer.md
- [x] T022 [P] Create docs-engineer agent (documentation, 10 skills) in agents/docs-engineer.md

### Skills — Core & Architecture (source: planning/14-generic-skills-spec.md)

- [x] T023 [P] Create 4 core skills (csharp-idioms, async-patterns, dependency-injection, configuration) in skills/core/
- [x] T024 [P] Create 5 architecture skills (clean-architecture, vertical-slice, ddd-patterns, modular-monolith, cqrs-basics) in skills/architecture/

### Skills — API & Data (source: planning/14-generic-skills-spec.md)

- [x] T025 [P] Create 5 API skills (minimal-api, controller-patterns, openapi-scalar, versioning, content-negotiation) in skills/api/
- [x] T026 [P] Create 5 data skills (ef-core-basics, ef-migrations, ef-queries, repository-patterns, db-transactions) in skills/data/

### Skills — CQRS, Resilience, Security, Observability (source: planning/14-generic-skills-spec.md)

- [x] T027 [P] Create 4 CQRS skills (mediatr-handlers, pipeline-behaviors, request-response, notification-handlers) in skills/cqrs/
- [x] T028 [P] Create 3 resilience skills (polly-resilience, circuit-breaker, retry-patterns) in skills/resilience/
- [x] T029 [P] Create 3 security skills (auth-jwt, auth-policies, data-protection) in skills/security/
- [x] T030 [P] Create 3 observability skills (serilog-structured, health-checks, opentelemetry) in skills/observability/

### Skills — Microservice Command & Query (source: planning/18-microservice-skills-spec.md)

- [x] T031 [P] Create 6 microservice/command skills (aggregate-design, event-design, event-store, outbox, command-handler, aggregate-testing) in skills/microservice/command/
- [x] T032 [P] Create 5 microservice/query skills (query-entity, event-handler, query-handler, sequence-checking, listener-pattern) in skills/microservice/query/

### Skills — Microservice Cosmos, Processor, gRPC (source: planning/18-microservice-skills-spec.md)

- [x] T033 [P] Create 4 microservice/cosmos skills (cosmos-entity, cosmos-repository, partition-strategy, transactional-batch) in skills/microservice/cosmos/
- [x] T034 [P] Create 4 microservice/processor skills (hosted-service, event-routing, batch-processing, grpc-client) in skills/microservice/processor/
- [x] T035 [P] Create 3 microservice/grpc skills (service-definition, interceptors, validation) in skills/microservice/grpc/

### Skills — Microservice Gateway & Control Panel (source: planning/18-microservice-skills-spec.md)

- [x] T036 [P] Create 4 microservice/gateway skills (gateway-endpoint, endpoint-registration, gateway-security, scalar-docs) in skills/microservice/gateway/
- [x] T037 [P] Create 5 microservice/controlpanel skills (blazor-component, gateway-facade, response-result, query-string-bindable, mudblazor-patterns) in skills/microservice/controlpanel/

### Skills — Testing, DevOps, Workflow (source: planning/14-generic-skills-spec.md, planning/18-microservice-skills-spec.md)

- [x] T038 [P] Create 4 testing skills (unit-testing, integration-testing, test-fixtures, performance-testing) in skills/testing/
- [x] T039 [P] Create 5 devops skills (dockerfile, kubernetes, github-actions, azure-resources, aspire-orchestration) in skills/devops/
- [x] T040 [P] Create 5 workflow skills (sdd-lifecycle, feature-tracking, multi-repo-workflow, code-review-workflow, session-management) in skills/workflow/

### Skills — Infra, Quality, Docs (source: planning/14-generic-skills-spec.md)

- [x] T041 [P] Create 3 infra skills (background-jobs, email-notifications, file-storage) in skills/infra/
- [x] T042 [P] Create 3 quality skills (code-analysis, architectural-fitness, review-checklist) in skills/quality/
- [x] T043 [P] Create 8 docs skills (api-docs, architecture-docs, runbook, adr, onboarding, changelog-gen, diagram-gen, readme-gen) in skills/docs/

### Knowledge Documents (source: planning/18-microservice-skills-spec.md, planning/14-generic-skills-spec.md)

- [x] T044 [P] Create event-sourcing-flow knowledge doc in knowledge/event-sourcing-flow.md
- [x] T045 [P] Create outbox-pattern knowledge doc in knowledge/outbox-pattern.md
- [x] T046 [P] Create service-bus-patterns knowledge doc in knowledge/service-bus-patterns.md
- [x] T047 [P] Create grpc-patterns knowledge doc in knowledge/grpc-patterns.md
- [x] T048 [P] Create cosmos-patterns knowledge doc in knowledge/cosmos-patterns.md
- [x] T049 [P] Create testing-patterns knowledge doc in knowledge/testing-patterns.md
- [x] T050 [P] Create deployment-patterns knowledge doc in knowledge/deployment-patterns.md
- [x] T051 [P] Create dead-letter-reprocessing knowledge doc in knowledge/dead-letter-reprocessing.md
- [x] T052 [P] Create event-versioning knowledge doc in knowledge/event-versioning.md
- [x] T053 [P] Create concurrency-patterns knowledge doc in knowledge/concurrency-patterns.md
- [x] T054 [P] Create documentation-standards knowledge doc in knowledge/documentation-standards.md

### CLI Foundation Models (source: planning/16-cli-implementation.md)

- [x] T055 Create Pydantic config and project models in src/dotnet_ai_kit/models.py
- [x] T056 Create config schema with validation rules in src/dotnet_ai_kit/config.py
- [x] T057 [P] Create AGENT_CONFIG dict for Claude/Cursor/Copilot/Codex in src/dotnet_ai_kit/agents.py

**Checkpoint**: Knowledge base complete (6 rules, 13 agents, 101 skills, 11 knowledge docs). CLI foundation models ready. User story implementation can now begin.

---

## Phase 3: User Story 1 - Install Tool and Initialize in Existing Project (Priority: P1) 🎯 MVP

**Goal**: Developer installs CLI, runs `dotnet-ai init`, and the tool auto-detects project properties and copies rules/commands to the AI tool's directories.

**Independent Test**: Run `dotnet-ai init . --ai claude` in a .NET project and verify config.yml, 25 commands, and 6 rules are created.

### Implementation for User Story 1

- [x] T058 [US1] Implement project detection algorithm (architecture, .NET version, company name, packages) in src/dotnet_ai_kit/detection.py
- [x] T059 [US1] Implement file copy + Jinja2 template rendering (commands, rules, config) in src/dotnet_ai_kit/copier.py
- [x] T060 [US1] Implement CLI commands (init, check, upgrade, configure, --verbose) with typer in src/dotnet_ai_kit/cli.py
- [x] T061 [US1] Implement extension manager (add, remove, list, manifest validation) in src/dotnet_ai_kit/extensions.py
- [x] T062 [P] [US1] Create default config template with all fields in templates/config-template.yml
- [x] T063 [P] [US1] Create permissions-minimal.json (Level 1: build/test only) in config/permissions-minimal.json
- [x] T064 [P] [US1] Create permissions-standard.json (Level 2: + git/gh CLI) in config/permissions-standard.json
- [x] T065 [P] [US1] Create permissions-full.json (Level 3: all operations) in config/permissions-full.json
- [x] T066 [P] [US1] Create mcp-permissions.json (GitHub MCP permissions) in config/mcp-permissions.json
- [x] T067 [US1] Create CLAUDE.md project context file at repository root in CLAUDE.md
- [x] T067a [US1] Create init slash command (detect existing/new project, copy rules+commands, report detection results, --force flag) in commands/init.md
- [x] T067b [US1] Create configure slash command (interactive questionnaire, JIT prompting, permission level, CodeRabbit integration, --minimal/--reset flags) in commands/configure.md
- [x] T068 [P] [US1] Write CLI unit tests for init, check, upgrade (including just-in-time config prompting when company name is missing) in tests/test_cli.py
- [x] T069 [P] [US1] Write detection algorithm tests (microservice + generic patterns) in tests/test_detection.py
- [x] T070 [P] [US1] Write config validation tests in tests/test_config.py
- [x] T071 [P] [US1] Write file copier tests (cross-platform paths, Jinja2 rendering) in tests/test_copier.py
- [x] T072 [P] [US1] Write extension manager tests in tests/test_extensions.py

**Checkpoint**: CLI tool is installable and functional. `dotnet-ai init`, `check`, `upgrade`, `configure`, and `extension` commands work. Rules and commands are copied to user projects.

---

## Phase 4: User Story 3 - Step-by-Step Feature Lifecycle (Priority: P2)

**Goal**: Developer uses individual SDD commands (specify → clarify → plan → tasks → analyze → implement → review → verify → pr) to build features with full control.

**Independent Test**: Run each command in sequence and verify each produces its expected output artifact.

### Implementation for User Story 3

- [x] T073 [US3] Create specify command (feature spec from description, service map, quality checklist) in commands/specify.md
- [x] T074 [US3] Create clarify command (ambiguity scan, sequential questions, spec update) in commands/clarify.md
- [x] T075 [US3] Create plan command (research, layer/service mapping, event design, contracts) in commands/plan.md
- [x] T076 [US3] Create tasks command (task generation by phase/repo, dependency notation, file paths) in commands/tasks.md
- [x] T077 [US3] Create analyze command (read-only consistency check, severity ratings, max 50 findings) in commands/analyze.md
- [x] T078 [US3] Create implement command (feature branch, dependency-order execution, build after each group, task tracking) in commands/implement.md
- [x] T079 [US3] Create review command (standards review, CodeRabbit integration, auto-fix option) in commands/review.md
- [x] T080 [US3] Create verify command (build + test + format + mode-specific checks, PASS/FAIL/WARN) in commands/verify.md
- [x] T081 [US3] Create pr command (push branch, gh pr create, feature summary, cross-links) in commands/pr.md

**Checkpoint**: All 9 SDD lifecycle commands work. Developer can run specify through pr in sequence.

---

## Phase 5: User Story 2 - One-Command Feature Building (Priority: P1)

**Goal**: Developer runs `/dotnet-ai.do "description"` and the tool chains the full lifecycle automatically.

**Independent Test**: Run `/dotnet-ai.do "Add product catalog"` and verify spec, plan, implementation, review, and PR are produced.

### Implementation for User Story 2

- [x] T082 [US2] Create do command (chains specify→plan→implement→review→verify→pr, smart pausing, max 3 clarifying questions, --dry-run, --no-pr, --no-review flags) in commands/do.md

**Checkpoint**: One-command feature building works. Simple features complete without pausing; complex features pause after plan.

---

## Phase 6: User Story 4 - Quick Code Generation (Priority: P2)

**Goal**: Developer uses code gen commands (add-crud, add-aggregate, etc.) to scaffold code matching existing project patterns.

**Independent Test**: Run `/dotnet-ai.add-crud Order` and verify entity, handlers, endpoint, and tests are generated.

### Implementation for User Story 4

- [x] T083 [P] [US4] Create add-aggregate command (aggregate + initial event + handler + gRPC service) in commands/add-aggregate.md
- [x] T084 [P] [US4] Create add-entity command (entity + event handlers, auto-detect SQL/Cosmos) in commands/add-entity.md
- [x] T085 [P] [US4] Create add-event command (event to existing aggregate + handler suggestions) in commands/add-event.md
- [x] T086 [P] [US4] Create add-endpoint command (REST endpoint + gRPC client registration) in commands/add-endpoint.md
- [x] T087 [P] [US4] Create add-page command (Blazor page + MudBlazor + gateway facade) in commands/add-page.md
- [x] T088 [US4] Create add-crud command (full CRUD: entity + handlers + endpoint + tests, mode-aware: VSA/Clean Arch/DDD/Microservice) in commands/add-crud.md
- [x] T089 [US4] Create add-tests command (scan untested code, detect framework/mocking lib, generate tests) in commands/add-tests.md

**Checkpoint**: All 7 code generation commands work. Generated code matches existing project patterns.

---

## Phase 7: User Story 5 - Multi-Repository Microservice Features (Priority: P3)

**Goal**: Developer orchestrates features across 3-6 repos with dependency-ordered implementation and linked PRs.

**Independent Test**: Specify a multi-repo feature and verify repos are cloned, branches created, tasks organized by service dependency order.

### Implementation for User Story 5

- [x] T090 [US5] Enhance implement command with multi-repo orchestration logic (clone/open repos, dependency-order execution, per-repo build/test, cross-repo progress tracking) in commands/implement.md
- [x] T091 [US5] Enhance analyze command with cross-service consistency checks (event consistency, proto consistency, cross-repo dependencies, event catalogue validation) in commands/analyze.md

**Checkpoint**: Multi-repo features implement in correct dependency order (Command → Query/Processor → Gateway → ControlPanel). Linked PRs created.

---

## Phase 8: User Story 6 - Session Management and Progress Tracking (Priority: P3)

**Goal**: Developer can check progress, save checkpoints, undo mistakes, and resume work across sessions.

**Independent Test**: Start a feature, checkpoint, close session, reopen, run status and verify accurate progress with "Next:" suggestion.

### Implementation for User Story 6

- [x] T092 [P] [US6] Create status command (lifecycle progress, task progress, per-repo status, next suggestion) in commands/status.md
- [x] T093 [P] [US6] Create undo command (show revert preview, confirm, restore files, update tasks.md) in commands/undo.md
- [x] T094 [US6] Create checkpoint command (commit changes, write handoff.md with completed/pending/blocked) in commands/checkpoint.md
- [x] T095 [US6] Create wrap-up command (commit all, comprehensive handoff, extract learnings, session summary) in commands/wrap-up.md

**Checkpoint**: Session management works. Progress saved and restored across sessions.

---

## Phase 9: User Story 7 - Learning and Pattern Explanation (Priority: P4)

**Goal**: Developer uses explain command to learn patterns, get code examples from the tool's knowledge base, and complete an interactive tutorial.

**Independent Test**: Run `/dotnet-ai.explain aggregate` and verify description, usage, code example, and common mistakes.

### Implementation for User Story 7

- [x] T096 [US7] Create explain command (topic matching to knowledge/skills/commands, code examples, Mermaid diagrams, --tutorial 5-step walkthrough, --mistakes flag) in commands/explain.md

**Checkpoint**: Explain command covers all architecture patterns, microservice patterns, and tool commands.

---

## Phase 10: User Story 8 - Documentation Generation (Priority: P4)

**Goal**: Developer generates and maintains project documentation via `/dotnet-ai.docs` with 9 subcommands.

**Independent Test**: Run `/dotnet-ai.docs readme` and verify README.md is generated from project analysis.

### Implementation for User Story 8

- [x] T097 [US8] Create docs command (9 subcommands: readme, api, adr, deploy, release, service, code, feature, all; gap scanning; multi-repo support) in commands/docs.md

**Checkpoint**: Documentation generation works for all 9 subcommands.

---

## Phase 11: User Story 1 (continued) - Project Templates (Priority: P1)

**Goal**: Complete the init flow with scaffolding templates for new projects.

**Independent Test**: Run `dotnet-ai init my-project --type command` and verify a complete command project is scaffolded.

### Implementation for User Story 1 (Templates)

- [x] T098 [P] [US1] Create command microservice template (event-sourced write side scaffold) in templates/command/
- [x] T099 [P] [US1] Create query microservice template (SQL Server read side scaffold) in templates/query/
- [x] T100 [P] [US1] Create cosmos-query microservice template (Cosmos DB read side scaffold) in templates/cosmos-query/
- [x] T101 [P] [US1] Create processor microservice template (background event processor scaffold) in templates/processor/
- [x] T102 [P] [US1] Create gateway-management microservice template (REST gateway with Scalar scaffold) in templates/gateway-management/
- [x] T103 [P] [US1] Create gateway-consumer microservice template (consumer-facing gateway scaffold) in templates/gateway-consumer/
- [x] T104 [P] [US1] Create controlpanel-module microservice template (Blazor WASM module scaffold) in templates/controlpanel-module/
- [x] T105 [P] [US1] Create generic-vsa template (Vertical Slice Architecture scaffold) in templates/generic-vsa/
- [x] T106 [P] [US1] Create generic-clean-arch template (Clean Architecture scaffold) in templates/generic-clean-arch/
- [x] T107 [P] [US1] Create generic-ddd template (Domain-Driven Design scaffold) in templates/generic-ddd/
- [x] T108 [P] [US1] Create generic-modular-monolith template (Modular Monolith scaffold) in templates/generic-modular-monolith/
- [x] T109 [US1] Create command file templates with $ARGUMENTS placeholder for Claude Code in templates/commands/

**Checkpoint**: All 11 project templates + command file templates work. `dotnet-ai init --type` scaffolds any supported project type.

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Validation, documentation, and quality assurance

- [x] T110 Validate token budgets (all rules ≤100 lines, commands ≤200 lines, skills ≤400 lines) and verify all 25 commands include --dry-run or --preview flag support per Constitution Principle V
- [x] T111 [P] Validate all 25 command alias mappings (full + short names) documented in commands/ and CLAUDE.md
- [x] T112 [P] Update README.md with final file counts, verified command list, and installation instructions
- [x] T113 [P] Update CONTRIBUTING.md with final project structure and build phases
- [x] T114 Run quickstart.md validation: verify all commands and workflows described work end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (directory structure must exist) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 (CLI needs models, agents.py)
- **US3 (Phase 4)**: Depends on Phase 2 (commands reference skills)
- **US2 (Phase 5)**: Depends on Phase 4 (do.md chains SDD commands)
- **US4 (Phase 6)**: Depends on Phase 2 (code gen commands reference skills)
- **US5 (Phase 7)**: Depends on Phase 4 (enhances implement/analyze commands)
- **US6 (Phase 8)**: Depends on Phase 2 (session commands are standalone)
- **US7 (Phase 9)**: Depends on Phase 2 (explain reads knowledge docs and skills)
- **US8 (Phase 10)**: Depends on Phase 2 (docs command reads docs skills)
- **US1 Templates (Phase 11)**: Depends on Phase 3 (copier must exist)
- **Polish (Phase 12)**: Depends on all previous phases

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **US3 (P2)**: Can start after Phase 2 — Independent of US1 CLI
- **US2 (P1)**: Depends on US3 (do.md chains the SDD commands)
- **US4 (P2)**: Can start after Phase 2 — Independent of US1/US3
- **US5 (P3)**: Depends on US3 (enhances implement.md and analyze.md)
- **US6 (P3)**: Can start after Phase 2 — Independent session commands
- **US7 (P4)**: Can start after Phase 2 — Independent explain command
- **US8 (P4)**: Can start after Phase 2 — Independent docs command

### Within Each User Story

- Models/schemas before services
- Services before CLI commands
- Core implementation before enhancements
- Story complete before moving to next priority

### Parallel Opportunities

- All Phase 2 tasks marked [P] can run in parallel (130+ files across different directories)
- Phase 3 (US1), Phase 4 (US3), Phase 6 (US4), Phase 8 (US6), Phase 9 (US7), Phase 10 (US8) can all start after Phase 2
- Within Phase 2: all rule tasks, agent tasks, skill category tasks, and knowledge doc tasks are independent
- Phase 11 (templates) tasks are all independent of each other

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Launch all rules in parallel:
Task: "Create naming conventions rule in rules/naming.md"
Task: "Create C# coding style rule in rules/coding-style.md"
Task: "Create localization rule in rules/localization.md"
# ... (all 6 rules)

# Launch all agents in parallel:
Task: "Create dotnet-architect agent in agents/dotnet-architect.md"
Task: "Create api-designer agent in agents/api-designer.md"
# ... (all 13 agents)

# Launch all skill categories in parallel:
Task: "Create 4 core skills in skills/core/"
Task: "Create 5 architecture skills in skills/architecture/"
# ... (all 22 skill categories)

# Launch all knowledge docs in parallel:
Task: "Create event-sourcing-flow knowledge doc"
Task: "Create outbox-pattern knowledge doc"
# ... (all 11 knowledge docs)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (CLI + init + config)
4. **STOP and VALIDATE**: Install CLI, run `dotnet-ai init` in a test project
5. Demo: "dotnet-ai-kit installed, detected Clean Architecture .NET 10, copied 25 commands + 6 rules"

### Incremental Delivery

1. Complete Setup + Foundational → Knowledge base ready
2. Add US1 (CLI) → Test installation → Demo (MVP!)
3. Add US3 (SDD commands) → Test lifecycle → Demo
4. Add US2 (do.md) → Test one-command flow → Demo
5. Add US4 (code gen) → Test add-crud → Demo
6. Add US5-US8 → Test multi-repo, sessions, learning, docs
7. Add US1 Templates → Test scaffolding
8. Polish → Validate token budgets → Release

### Parallel Team Strategy

With multiple developers after Phase 2 completes:

1. Developer A: US1 (CLI modules + tests)
2. Developer B: US3 (SDD commands) → then US2 (do.md)
3. Developer C: US4 (code gen commands) + US6 (session commands)
4. Developer D: US7 (explain) + US8 (docs) + US5 (multi-repo enhancements)
5. Developer E: US1 Templates (11 scaffolds)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Each skill file must include YAML frontmatter (name, description, category, agent)
- Each command file must include YAML frontmatter (description) and be ≤200 lines
- Each rule file must include YAML frontmatter (alwaysApply: true, description) and be ≤100 lines
- Source content for each file is specified in the Content Source Mapping table in plan.md
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Task phases (1-12) are organized by user story for independent testability; they differ from the plan's build phases (1-15) which are organized by component type
