# Tasks: Architecture Profiles, Multi-Repo Deployment, and Enforcement Optimization

**Input**: Design documents from `/specs/015-arch-enforcement-multi-repo/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included — spec explicitly lists 6 new test files.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Foundation constants and model changes that multiple stories depend on

- [x] T001 [P] Add PROFILE_MAP dict and FALLBACK_PROFILE constant to src/dotnet_ai_kit/copier.py — 12 entries mapping project_type strings to profile source paths per research.md R1
- [x] T002 [P] Add AGENT_FRONTMATTER_MAP dict to src/dotnet_ai_kit/agents.py — claude entry with role/expertise/complexity/max_iterations mappings per research.md R2
- [x] T003 [P] Add `detected_paths: Optional[dict[str, str]] = None` field to DetectedProject model in src/dotnet_ai_kit/models.py
- [x] T004 [P] Add `linked_from: Optional[str] = None` field to DotnetAiConfig model in src/dotnet_ai_kit/models.py
- [x] T068 [P] Write tests in tests/test_models_new_fields.py — test: detected_paths field on DetectedProject (None default, dict accepted, serializes to YAML), linked_from field on DotnetAiConfig (None default, string accepted, serializes to YAML)

**Checkpoint**: Foundation constants, models, and model tests ready — story implementation can begin

---

## Phase 2: User Story 1 — Project-Type-Specific Architecture Enforcement (Priority: P1) MVP

**Goal**: Create 12 architecture profiles and deploy the matching one during configure/upgrade based on detected project type.

**Independent Test**: Deploy a command profile to a test project and verify the rules directory contains it. Deploy generic fallback when project_type is missing.

### Implementation for User Story 1

- [x] T005 [P] [US1] Create profiles/microservice/command.md — command-side CQRS constraints (aggregate boundaries, one-aggregate-per-handler, outbox pattern, event immutability, integration test patterns). Derive from skills in skills/microservice/command/. Must be under 100 lines with alwaysApply: true frontmatter
- [x] T006 [P] [US1] Create profiles/microservice/query-sql.md — query-side SQL constraints (read-model entities, event handler idempotency, sequence checking, no aggregate access). Derive from skills in skills/microservice/query/. Under 100 lines
- [x] T007 [P] [US1] Create profiles/microservice/query-cosmos.md — query-side Cosmos constraints (partition strategy, transactional batch, cosmos entity patterns). Derive from skills in skills/microservice/cosmos/. Under 100 lines
- [x] T008 [P] [US1] Create profiles/microservice/processor.md — processor constraints (hosted service patterns, event routing, grpc client, batch processing). Derive from skills in skills/microservice/processor/. Under 100 lines
- [x] T009 [P] [US1] Create profiles/microservice/gateway.md — gateway constraints (endpoint registration, security, scalar docs, versioning). Derive from skills in skills/microservice/gateway/. Under 100 lines
- [x] T010 [P] [US1] Create profiles/microservice/controlpanel.md — control panel constraints (blazor component patterns, gateway facade, MudBlazor patterns). Derive from skills in skills/microservice/controlpanel/. Under 100 lines
- [x] T011 [P] [US1] Create profiles/microservice/hybrid.md — hybrid constraints combining top command + query constraints (aggregate boundaries, event handler idempotency, sequence checking). Under 100 lines
- [x] T012 [P] [US1] Create profiles/generic/vsa.md — VSA constraints (feature folder boundaries, no cross-feature dependencies, handler-per-feature). Derive from skills/architecture/vertical-slice/. Under 100 lines
- [x] T013 [P] [US1] Create profiles/generic/clean-arch.md — clean architecture constraints (layer dependency direction, no inner-to-outer references). Derive from skills/architecture/clean-architecture/. Under 100 lines
- [x] T014 [P] [US1] Create profiles/generic/ddd.md — DDD constraints (aggregate roots, value objects, domain events, repository boundaries). Derive from skills/architecture/ddd-patterns/. Under 100 lines
- [x] T015 [P] [US1] Create profiles/generic/modular-monolith.md — modular monolith constraints (module boundaries, no direct cross-module DB access). Derive from skills/architecture/modular-monolith/. Under 100 lines
- [x] T016 [P] [US1] Create profiles/generic/generic.md — generic fallback constraints (layer dependency direction, no circular references, test coverage). Universal .NET constraints only. Under 100 lines
- [x] T017 [US1] Implement copy_profile() function in src/dotnet_ai_kit/copier.py — look up PROFILE_MAP, fallback to generic on low confidence or missing type, copy to rules_dir/architecture-profile.md per contracts/copier-functions.md
- [x] T018 [US1] Extend configure() in src/dotnet_ai_kit/cli.py — after existing copy_rules/agents/skills calls, read project.yml for project_type and confidence, call copy_profile() for each configured AI tool
- [x] T019 [US1] Extend upgrade() in src/dotnet_ai_kit/cli.py — after existing re-deployment, call copy_profile() to re-deploy profile matching current version
- [x] T020 [US1] Write tests in tests/test_copier_profiles.py — test copy_profile() for: correct profile selection per project_type, generic fallback on low confidence, generic fallback on missing project_type, cross-tool deployment (claude rules_dir, cursor rules_dir), returns None for tools with no rules_dir (e.g., codex), line count validation (all profiles under 100 lines), FileNotFoundError on missing source

**Checkpoint**: Profile deployment works. Running configure deploys the correct profile. US1 independently testable.

---

## Phase 3: User Story 5 — Universal Agent Frontmatter (Priority: P3)

**Goal**: Update all 13 agent files to universal schema and transform to Claude Code-specific frontmatter during deployment.

**Independent Test**: Deploy an agent with `role: advisory` and verify the output contains `disallowedTools: [Write, Edit]`.

> Note: US5 is implemented before US2/US3/US4 because it's a Phase 1 foundation item (per quickstart.md) that other stories depend on for correct agent deployment to secondary repos.

### Implementation for User Story 5

- [x] T021 [P] [US5] Update agents/command-architect.md frontmatter to universal schema: role: advisory, expertise: [aggregate-design, event-design, event-store, outbox, command-handler, event-versioning, aggregate-testing], complexity: high, max_iterations: 20. Preserve existing name, description, and markdown body
- [x] T022 [P] [US5] Update agents/query-architect.md frontmatter: role: advisory, expertise: [query-entity, event-handler, listener-pattern, query-handler, sequence-checking, event-versioning], complexity: high, max_iterations: 20
- [x] T023 [P] [US5] Update agents/cosmos-architect.md frontmatter: role: advisory, expertise: [cosmos-entity, cosmos-repository, transactional-batch, partition-strategy, event-handler], complexity: high, max_iterations: 20
- [x] T024 [P] [US5] Update agents/processor-architect.md frontmatter: role: advisory, expertise: [hosted-service, event-routing, grpc-client, batch-processing, event-versioning], complexity: high, max_iterations: 20
- [x] T025 [P] [US5] Update agents/gateway-architect.md frontmatter: role: advisory, expertise: [gateway-endpoint, endpoint-registration, gateway-security, scalar-docs, versioning], complexity: high, max_iterations: 20. Note: 'authorization' removed — no matching skill name found
- [x] T026 [P] [US5] Update agents/controlpanel-architect.md frontmatter: role: advisory, expertise: [blazor-component, gateway-facade, mudblazor-patterns, query-string-bindable, response-result], complexity: high, max_iterations: 20
- [x] T027 [P] [US5] Update agents/test-engineer.md frontmatter: role: testing, expertise: [aggregate-testing, unit-testing, integration-testing, test-fixtures], complexity: high, max_iterations: 25
- [x] T028 [P] [US5] Update agents/reviewer.md frontmatter: role: review, expertise: [review-checklist, architectural-fitness], complexity: medium, max_iterations: 15
- [x] T029 [P] [US5] Update agents/ef-specialist.md frontmatter: role: advisory, expertise: [ef-core-basics, repository-patterns, specification-pattern, audit-trail, ef-migrations], complexity: medium, max_iterations: 15
- [x] T030 [P] [US5] Update agents/api-designer.md frontmatter: role: advisory, expertise: [minimal-api, controllers, versioning, openapi-scalar, rate-limiting], complexity: medium, max_iterations: 15
- [x] T031 [P] [US5] Update agents/dotnet-architect.md frontmatter: role: advisory, expertise: [clean-architecture, vertical-slice, ddd-patterns, modular-monolith], complexity: high, max_iterations: 20
- [x] T032 [P] [US5] Update agents/devops-engineer.md frontmatter: role: advisory, expertise: [dockerfile, github-actions, kubernetes, aspire-orchestration, azure-resources], complexity: medium, max_iterations: 15
- [x] T033 [P] [US5] Update agents/docs-engineer.md frontmatter: role: advisory, expertise: [readme-gen, api-docs, architecture-docs, changelog-gen, adr], complexity: low, max_iterations: 10
- [x] T034 [US5] Update copy_agents() in src/dotnet_ai_kit/copier.py — add tool_name parameter (default "claude"), parse YAML frontmatter from source, look up AGENT_FRONTMATTER_MAP[tool_name], transform universal fields to tool-specific, write transformed frontmatter + original body. Log warning and skip if tool not in map
- [x] T035 [US5] Update all callers of copy_agents() in src/dotnet_ai_kit/cli.py to pass tool_name parameter
- [x] T036 [US5] Write tests in tests/test_copier_agents.py — test: role: advisory → disallowedTools: [Write, Edit], role: implementation → no disallowedTools, expertise list → skills list, complexity: high → effort: high + model: opus, max_iterations: 20 → maxTurns: 20, unsupported tool logs warning

**Checkpoint**: Agent deployment produces correct Claude Code frontmatter. US5 independently testable.

---

## Phase 4: User Story 3 — Auto-Commit Branch Safety (Priority: P2)

**Goal**: All secondary repo auto-commits use dedicated branches, never main/master/develop.

**Independent Test**: Run specify with a linked repo and verify the commit lands on a chore branch.

### Implementation for User Story 3

- [x] T037 [P] [US3] Update commands/dai.specify.md — add branch safety instructions for secondary repo brief projections: check current branch, create/switch to chore/brief-{NNN}-{name}, warn and skip on dirty working directory. Must stay under 200 lines
- [x] T038 [P] [US3] Update commands/dai.plan.md — add branch reuse instructions for secondary repo brief updates: check for existing chore/brief-{NNN}-{name} branch, switch to it if exists, create if not. Must stay under 200 lines
- [x] T039 [P] [US3] Update commands/dai.tasks.md — add same branch reuse instructions as dai.plan.md for secondary repo brief updates. Must stay under 200 lines

**Checkpoint**: AI commands use dedicated branches for secondary repo commits. US3 independently testable.

---

## Phase 5: User Story 7 — Command Context Optimization (Priority: P4)

**Goal**: Review, verify, and check commands run in forked subagent context.

**Independent Test**: Verify command frontmatter contains context: 'fork' and agent fields.

### Implementation for User Story 7

- [x] T040 [P] [US7] Update commands/dai.review.md — add `context: 'fork'` and `agent: reviewer` to YAML frontmatter. Must stay under 200 lines
- [x] T041 [P] [US7] Update commands/dai.verify.md — add `context: 'fork'` and `agent: general-purpose` to YAML frontmatter. Must stay under 200 lines
- [x] T042 [P] [US7] Update commands/dai.analyze.md — add `context: 'fork'` and `agent: general-purpose` to YAML frontmatter. Must stay under 200 lines

**Checkpoint**: Forked commands work correctly. US7 independently testable.

---

## Phase 6: User Story 6 — Skill Auto-Activation (Priority: P3)

**Goal**: Skills use detected paths for file-based activation and when-to-use for behavioral activation.

**Independent Test**: Deploy a skill with path tokens, verify resolved paths in output. Verify when-to-use field present.

### Implementation for User Story 6

- [x] T043 [P] [US6] Add when-to-use and paths token to skills/microservice/command/aggregate-design/SKILL.md — when-to-use: "When creating or modifying event-sourced aggregates, factory methods, Apply methods", paths: "${detected_paths.aggregates}/**/*.cs"
- [x] T044 [P] [US6] Add when-to-use and paths token to skills/microservice/command/event-design/SKILL.md — when-to-use: "When creating or modifying domain events, event data records, EventType enums", paths: "${detected_paths.events}/**/*.cs"
- [x] T045 [P] [US6] Add when-to-use and paths token to skills/microservice/command/command-handler/SKILL.md — when-to-use: "When creating or modifying command handlers using MediatR IRequestHandler", paths: "${detected_paths.handlers}/**/*.cs"
- [x] T046 [P] [US6] Add when-to-use to skills/microservice/query/event-handler/SKILL.md — "When creating or modifying event handlers on query side, sequence checking"
- [x] T047 [P] [US6] Add when-to-use to skills/microservice/query/query-entity/SKILL.md — "When creating or modifying read-model entities with private setters"
- [x] T048 [P] [US6] Add when-to-use to skills/microservice/gateway/gateway-endpoint/SKILL.md — "When creating or modifying REST controllers or gRPC service endpoints"
- [x] T049 [P] [US6] Add when-to-use to skills/microservice/cosmos/cosmos-entity/SKILL.md — "When creating or modifying Cosmos DB entities, partition keys, discriminators"
- [x] T050 [P] [US6] Add when-to-use to skills/data/ef-core-basics/SKILL.md — "When configuring EF Core DbContext, entity configurations, migrations"
- [x] T051 [P] [US6] Add when-to-use to skills/testing/unit-testing/SKILL.md — "When writing unit tests, creating fakers, assertion extensions"
- [x] T052 [P] [US6] Add when-to-use to skills/testing/integration-testing/SKILL.md — "When writing integration tests with WebApplicationFactory"
- [x] T053 [P] [US6] Add when-to-use to skills/microservice/command/aggregate-testing/SKILL.md — "When writing tests for event-sourced aggregates"
- [x] T054 [US6] Update copy_skills() in src/dotnet_ai_kit/copier.py — add detected_paths parameter, resolve ${detected_paths.*} tokens using regex per research.md R5, remove paths: line if token resolves to empty
- [x] T055 [US6] Update commands/dai.detect.md — add path detection step instructing the AI to scan for Aggregate<T>, Event directories, Handler directories, Test directories, etc. and populate detected_paths section in .dotnet-ai-kit/project.yml
- [x] T056 [US6] Update all callers of copy_skills() in src/dotnet_ai_kit/cli.py — read detected_paths from project.yml and pass to copy_skills()
- [x] T057 [US6] Write tests in tests/test_copier_skills.py — test: ${detected_paths.aggregates} resolves to actual path, unresolved token removes paths: line, None detected_paths leaves skill unchanged, multiple tokens in one file all resolve

**Checkpoint**: Skills deploy with resolved paths and when-to-use fields. US6 independently testable.

---

## Phase 7: User Story 4 — Code-Time Enforcement via Claude Code Hooks (Priority: P3)

**Goal**: PreToolUse prompt hook validates Write/Edit operations against profile constraints using haiku.

**Independent Test**: Configure a hook, verify settings.json contains the hook entry with baked-in constraints.

### Implementation for User Story 4

- [x] T058 [US4] Create templates/hook-prompt-template.md — Jinja2 template containing haiku instructions, .NET file scope filter (.cs, .csproj, .sln, .slnx, .razor, .proto, .cshtml), {{ constraints }} placeholder, and JSON response format instructions ({ok: true/false, reason: ...})
- [x] T059 [US4] Implement copy_hook() function in src/dotnet_ai_kit/copier.py — read profile, extract constraint text after frontmatter, render hook-prompt-template.md with constraints, read/create .claude/settings.json, add/update PreToolUse hook entry with model claude-haiku-4-5-20251001 and 15s timeout per contracts/copier-functions.md
- [x] T060 [US4] Extend configure() in src/dotnet_ai_kit/cli.py — after copy_profile(), if "claude" in ai_tools, call copy_hook() with the deployed profile path
- [x] T061 [US4] Extend upgrade() in src/dotnet_ai_kit/cli.py — after re-deploying profile, regenerate hook prompt if "claude" in ai_tools
- [x] T062 [US4] Write tests in tests/test_copier_hooks.py — test: constraint extraction from profile with frontmatter, prompt embedding into settings.json, .NET file scope filter in prompt, hook not deployed for non-claude tools, settings.json created if missing, existing hooks preserved

**Checkpoint**: Hook deployed with correct constraints. US4 independently testable.

---

## Phase 8: User Story 2 — Multi-Repo Tooling Deployment (Priority: P2)

**Goal**: Deploy full tooling stack (profiles, rules, agents, skills) to linked secondary repos during configure/upgrade.

**Independent Test**: Initialize two repos, link via configure, verify secondary receives correct profile and linked_from.

### Implementation for User Story 2

- [x] T063 [US2] Implement deploy_to_linked_repos() in src/dotnet_ai_kit/copier.py — iterate config.repos fields, check initialization (.dotnet-ai-kit/config.yml + project.yml exist), version-check (compare version.txt), deploy tooling using existing copy_* functions, write linked_from to secondary config, git branch creation/commit, log failures and continue per contracts/copier-functions.md and clarification Q1
- [x] T064 [US2] Extend configure() in src/dotnet_ai_kit/cli.py — after profile and hook deployment, if config.repos has local paths, call deploy_to_linked_repos(). Display results via rich table or JSON output
- [x] T065 [US2] Extend upgrade() in src/dotnet_ai_kit/cli.py — after re-deployment, call deploy_to_linked_repos() with branch name chore/dotnet-ai-kit-upgrade-{version}
- [x] T066 [US2] Update commands/dai.configure.md — add step documenting linked repo deployment behavior for user awareness
- [x] T067 [US2] Write tests in tests/test_multi_repo_deploy.py — test: deploy to initialized repo succeeds, uninitialized repo skipped with warning, newer version repo skipped, older version repo upgraded, same version adds profile only, remote URL repo skipped, dirty working directory skipped, partial failure continues to next repo, linked_from written to secondary config, branch created correctly

**Checkpoint**: Multi-repo deployment works end-to-end. US2 independently testable.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all stories

- [x] T069 [P] Validate all 12 profile files are under 100 lines — run line count check across profiles/ directory
- [x] T070 [P] Validate all updated command files are under 200 lines — check dai.specify.md, dai.plan.md, dai.tasks.md, dai.review.md, dai.verify.md, dai.analyze.md, dai.configure.md, dai.detect.md
- [x] T071 [P] Validate all updated skill files are under 400 lines — check the ~10 SKILL.md files with added when-to-use
- [x] T072 [P] Verify expertise values in all 13 agent files match actual skill names in skills/**/SKILL.md frontmatter
- [x] T073 Run full test suite: pytest --cov=dotnet_ai_kit — ensure all existing tests still pass (no regressions) and all 6 new test files pass
- [x] T074 Run linter: ruff check src/ tests/ — fix any issues

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — can start immediately
- **Phase 2 (US1 Profiles)**: Depends on T001 (PROFILE_MAP constant)
- **Phase 3 (US5 Agents)**: Depends on T002 (AGENT_FRONTMATTER_MAP constant)
- **Phase 4 (US3 Branches)**: No dependencies on other phases — can start after Phase 1
- **Phase 5 (US7 Context)**: No dependencies on other phases — can start after Phase 1
- **Phase 6 (US6 Skills)**: Depends on T003 (detected_paths model) and Phase 2 (profiles exist)
- **Phase 7 (US4 Hooks)**: Depends on Phase 2 (profiles exist, copy_profile works)
- **Phase 8 (US2 Multi-Repo)**: Depends on Phases 2, 3, 4, 6, 7 (all deployment functions ready)
- **Phase 9 (Polish)**: Depends on all previous phases

### User Story Dependencies

- **US1 (Profiles)**: Foundation — no dependencies on other stories
- **US5 (Agents)**: Foundation — no dependencies on other stories
- **US3 (Branches)**: Foundation — no dependencies on other stories
- **US7 (Context)**: Independent — no dependencies on other stories
- **US6 (Skills)**: Depends on US1 (profiles must exist for skill paths to make sense)
- **US4 (Hooks)**: Depends on US1 (hooks extract constraints from profiles)
- **US2 (Multi-Repo)**: Depends on US1, US5, US3, US6, US4 (deploys everything to secondary repos)

### Within Each User Story

- Constants/models before functions
- Functions before CLI integration
- CLI integration before tests
- All [P] tasks within a story can run in parallel

### Parallel Opportunities

- T002, T003, T004 can all run in parallel (different files)
- T005-T016 (all 12 profiles) can all run in parallel
- T021-T033 (all 13 agent updates) can all run in parallel
- T037-T039 (branch safety commands) can all run in parallel
- T040-T042 (context fork commands) can all run in parallel
- T043-T053 (skill when-to-use updates) can all run in parallel
- US1, US5, US3, US7 (Phases 2-5) can run in parallel after Phase 1
- US6 and US4 (Phases 6-7) can run in parallel after US1 completes

---

## Parallel Example: Phase 1 Setup

```
# All setup tasks in parallel (different files):
Task T001: PROFILE_MAP in copier.py
Task T002: AGENT_FRONTMATTER_MAP in agents.py
Task T003: detected_paths in models.py
Task T004: linked_from in models.py
```

## Parallel Example: US1 Profiles

```
# All 12 profiles in parallel (independent files):
Task T005: profiles/microservice/command.md
Task T006: profiles/microservice/query-sql.md
Task T007: profiles/microservice/query-cosmos.md
... (all 12 run simultaneously)
```

## Parallel Example: US5 Agents

```
# All 13 agent frontmatter updates in parallel:
Task T021: agents/command-architect.md
Task T022: agents/query-architect.md
... (all 13 run simultaneously)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: US1 Profiles (T005-T020)
3. **STOP and VALIDATE**: Run tests, verify profiles deploy correctly
4. This alone delivers the primary value — architectural constraint enforcement

### Incremental Delivery

1. Setup → US1 Profiles → MVP: Design-time enforcement works
2. + US5 Agents → Agent behavior quality improved
3. + US3 Branches + US7 Context → Safety and UX improvements
4. + US6 Skills + US4 Hooks → Auto-activation and code-time enforcement
5. + US2 Multi-Repo → Full multi-repo deployment
6. Each increment is independently valuable and testable

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Profile content MUST be derived from existing skills — read the corresponding skills directory before writing each profile
- Agent expertise values MUST match actual skill directory names in skills/**/SKILL.md
- All Python code must use pathlib.Path, never os.path.join()
- All subprocess calls must use list args, never shell=True
- Token budgets: profiles ≤100, commands ≤200, skills ≤400 lines
