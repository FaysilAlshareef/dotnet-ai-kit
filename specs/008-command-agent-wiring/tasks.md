# Tasks: Wire All Commands to Appropriate Agents and Skills

**Input**: Design documents from `/specs/008-command-agent-wiring/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: Not required — this is a markdown-only change. Verification is file existence + line count checks.

**Organization**: Tasks grouped by user story to enable independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3, US4)

---

## Phase 1: Setup

**Purpose**: Inventory current state and prepare the skill path reference table.

- [x] T001 Build a complete skill path reference by listing all `skills/` files with `find skills -name "SKILL.md" | sort` and save output for cross-referencing during implementation
- [x] T002 Read all 13 agent files in `agents/` and document current "Skills Loaded" entries alongside actual skill paths for the mismatch fix in Phase 2

---

## Phase 2: Foundational — Fix Agent Skill Paths (US4 prerequisite)

**Purpose**: Correct all agent "Skills Loaded" entries to use actual file paths. This must complete before commands can reference agents with confidence.

**Goal**: Every skill reference in every agent file maps to a real `skills/{category}/{subcategory}/SKILL.md` path.

- [x] T003 [US4] Fix `agents/command-architect.md` — update all skill references to full paths matching actual `skills/` directory. Replace shorthand like `microservice/aggregate` with `skills/microservice/command/aggregate-design/SKILL.md`. Remove references to non-existent skills.
- [x] T004 [P] [US4] Fix `agents/query-architect.md` — update all skill references to full paths matching actual `skills/` directory.
- [x] T005 [P] [US4] Fix `agents/cosmos-architect.md` — update all skill references to full paths matching actual `skills/` directory.
- [x] T006 [P] [US4] Fix `agents/processor-architect.md` — update all skill references to full paths matching actual `skills/` directory.
- [x] T007 [P] [US4] Fix `agents/gateway-architect.md` — update all skill references to full paths matching actual `skills/` directory.
- [x] T008 [P] [US4] Fix `agents/controlpanel-architect.md` — update all skill references to full paths matching actual `skills/` directory.
- [x] T009 [P] [US4] Fix `agents/dotnet-architect.md` — update all skill references to full paths matching actual `skills/` directory.
- [x] T010 [P] [US4] Fix `agents/api-designer.md` — update all skill references to full paths matching actual `skills/` directory.
- [x] T011 [P] [US4] Fix `agents/ef-specialist.md` — update all skill references to full paths matching actual `skills/` directory.
- [x] T012 [P] [US4] Fix `agents/test-engineer.md` — update all skill references to full paths matching actual `skills/` directory.
- [x] T013 [P] [US4] Fix `agents/devops-engineer.md` — update all skill references to full paths matching actual `skills/` directory.
- [x] T014 [P] [US4] Fix `agents/docs-engineer.md` — update all skill references to full paths matching actual `skills/` directory. Known mismatches: `docs/readme-generator` → `docs/readme-gen`, `docs/api-documentation` → `docs/api-docs`, `docs/deployment-guide` → `docs/runbook`, `docs/release-notes` → `docs/changelog-gen`.
- [x] T015 [P] [US4] Fix `agents/reviewer.md` — update all skill references to full paths matching actual `skills/` directory.

**Checkpoint**: After T015, verify every skill reference in every agent file resolves to an existing file: `for agent in agents/*.md; do grep -oP 'skills/[^\s`]+' "$agent" | while read p; do test -f "$p" || echo "MISSING: $p in $agent"; done; done`

---

## Phase 3: User Story 1 — Code Generation Commands Load Agents + Skills (Priority: P1)

**Goal**: Each of the 7 code-gen commands loads the correct specialist agent(s) and their skills.

**Independent Test**: Read each command file, verify agent loading section exists with correct agent(s) for the command's domain.

- [x] T016 [US1] Update `commands/add-aggregate.md` — add agent loading section: "Read `agents/command-architect.md` for aggregate design guidance. Load all skills listed in the agent's Skills Loaded section."
- [x] T017 [P] [US1] Update `commands/add-event.md` — add agent loading section: "Read `agents/command-architect.md` for event design guidance. Load all skills listed in the agent's Skills Loaded section."
- [x] T018 [P] [US1] Update `commands/add-entity.md` — add conditional agent loading section: "For SQL projects: Read `agents/query-architect.md`. For Cosmos projects: Read `agents/cosmos-architect.md`. Also read `agents/ef-specialist.md` for data access patterns. Load all skills listed in each loaded agent's Skills Loaded section."
- [x] T019 [P] [US1] Update `commands/add-endpoint.md` — add agent loading section: "Read `agents/gateway-architect.md` for gateway patterns. Also read `agents/api-designer.md` for REST API design. Load all skills listed in each agent's Skills Loaded section."
- [x] T020 [P] [US1] Update `commands/add-page.md` — add agent loading section: "Read `agents/controlpanel-architect.md` for Blazor page patterns. Load all skills listed in the agent's Skills Loaded section."
- [x] T021 [P] [US1] Update `commands/add-tests.md` — add agent loading section: "Read `agents/test-engineer.md` for testing patterns. Also read the project's primary architect agent for architecture context. Load all skills listed in each agent's Skills Loaded section."
- [x] T022 [P] [US1] Update `commands/add-crud.md` — add conditional agent loading section: "For generic mode: Read `agents/dotnet-architect.md`. For microservice mode: Read the project's primary architect. Also read `agents/ef-specialist.md` for data patterns and `agents/api-designer.md` for API patterns. Load all skills listed in each agent's Skills Loaded section."

**Checkpoint**: After T022, verify all 7 code-gen commands have agent loading sections. Verify each file is under 200 lines.

---

## Phase 4: User Story 2 — Implement Command Routes to All 13 Agents (Priority: P1)

**Goal**: Expand `implement.md`'s agent routing to cover all 13 agents via project type + task type matrix.

**Independent Test**: Read `implement.md` and verify all 13 agents are reachable.

- [x] T023 [US2] Update `commands/implement.md` Step 2b (Load Specialist Agent) — expand the project-type routing to include generic-mode projects: "vsa, clean-arch, ddd, modular-monolith, generic → Read `agents/dotnet-architect.md`"
- [x] T024 [US2] Update `commands/implement.md` Step 2b — add cosmos routing: "query-cosmos → Read `agents/cosmos-architect.md`" (currently missing, only query-sql is covered)
- [x] T025 [US2] Update `commands/implement.md` — add task-type-based secondary agent loading after Step 2b: "Additionally, based on the current task's domain, load secondary agents: API/endpoint tasks → `agents/api-designer.md`, Entity/data/EF tasks → `agents/ef-specialist.md`, Test tasks → `agents/test-engineer.md`, DevOps/Docker/CI tasks → `agents/devops-engineer.md`, Documentation tasks → `agents/docs-engineer.md`, Review tasks → `agents/reviewer.md`"
- [x] T026 [US2] Verify `commands/implement.md` is under 200 lines after all changes. If over, consolidate the routing into a compact table format.

**Checkpoint**: After T026, count agents reachable from implement.md routing. Must be 13.

---

## Phase 5: User Story 3 — Lifecycle Commands Load Appropriate Agents (Priority: P2)

**Goal**: Each lifecycle command loads the specialist agent(s) relevant to its purpose.

**Independent Test**: Read each command, verify agent loading section exists with the correct agent.

- [x] T027 [US3] Update `commands/review.md` — add agent loading section near the top: "Read `agents/reviewer.md` for review standards and quality checks. Load all skills listed in the agent's Skills Loaded section."
- [x] T028 [P] [US3] Update `commands/docs.md` — add agent loading section: "Read `agents/docs-engineer.md` for documentation patterns. Load all skills listed in the agent's Skills Loaded section."
- [x] T029 [P] [US3] Update `commands/verify.md` — add agent loading section: "Read `agents/test-engineer.md` for test verification. Read `agents/devops-engineer.md` for build/deploy checks. Load all skills from both agents."
- [x] T030 [P] [US3] Update `commands/analyze.md` — add agent loading section: "Read the project's primary architect agent (by project type — see routing matrix) for architecture consistency analysis. Load all skills from the agent."
- [x] T031 [P] [US3] Update `commands/plan.md` — add agent loading section: "Read the project's primary architect agent for planning guidance. Load all skills from the agent."
- [x] T032 [P] [US3] Update `commands/tasks.md` — add agent loading section: "Read the project's primary architect agent for task decomposition. Load all skills from the agent."
- [x] T033 [P] [US3] Update `commands/specify.md` — add agent loading section: "Read the project's primary architect agent for feature scoping. Load all skills from the agent."
- [x] T034 [P] [US3] Update `commands/clarify.md` — add agent loading section: "Read the project's primary architect agent for ambiguity detection. Load all skills from the agent."

**Checkpoint**: After T034, verify all 8 lifecycle commands have agent loading. All files under 200 lines.

---

## Phase 6: Polish & Verification

**Purpose**: Final validation across all changes.

- [x] T035 Verify all modified command files are under 200 lines: `wc -l commands/add-aggregate.md commands/add-entity.md commands/add-event.md commands/add-endpoint.md commands/add-page.md commands/add-tests.md commands/add-crud.md commands/implement.md commands/review.md commands/docs.md commands/verify.md commands/analyze.md commands/plan.md commands/tasks.md commands/specify.md commands/clarify.md`
- [x] T036 [P] Verify all skill paths referenced in commands resolve to existing files: scan each modified command for `skills/` paths and check file existence
- [x] T037 [P] Verify all agent "Skills Loaded" entries resolve to existing files: scan each agent file for `skills/` paths and check file existence
- [x] T038 Verify 9 utility commands were NOT modified: `git diff --name-only commands/checkpoint.md commands/configure.md commands/detect.md commands/explain.md commands/init.md commands/pr.md commands/status.md commands/undo.md commands/wrap-up.md` should show no changes
- [x] T039 Cross-reference: verify all 13 agents are reachable from at least one command by grepping all commands for each agent filename

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Agent Fixes)**: Depends on Phase 1 (need skill path reference)
- **Phase 3 (US1 Code-Gen)**: Can start after Phase 2 (agents must have correct paths first)
- **Phase 4 (US2 Implement)**: Can start after Phase 2 (same reason)
- **Phase 5 (US3 Lifecycle)**: Can start after Phase 2 (same reason)
- **Phase 6 (Polish)**: Depends on all user stories complete

### User Story Dependencies

- **US4 (Phase 2)**: Must complete first — other stories depend on correct agent skill paths
- **US1 (Phase 3)**: Independent after US4
- **US2 (Phase 4)**: Independent after US4
- **US3 (Phase 5)**: Independent after US4

### Parallel Opportunities

**Maximum parallelism**: After Phase 2, US1 + US2 + US3 can all run simultaneously (3 streams).

```
Phase 1: T001 → T002
                ↓
Phase 2: T003 → T004∥T005∥T006∥T007∥T008∥T009∥T010∥T011∥T012∥T013∥T014∥T015
                ↓
Phase 3 (US1): T016 → T017∥T018∥T019∥T020∥T021∥T022
Phase 4 (US2): T023 → T024 → T025 → T026
Phase 5 (US3): T027 → T028∥T029∥T030∥T031∥T032∥T033∥T034
                ↓
Phase 6: T035 → T036∥T037 → T038 → T039
```

---

## Implementation Strategy

### MVP First (Phase 2 + US1 Only)

1. Complete Phase 1 + Phase 2: Fix agent skill paths (15 tasks)
2. Complete Phase 3 (US1): Wire 7 code-gen commands (7 tasks)
3. **STOP and VALIDATE**: Verify agents have correct paths, code-gen commands load agents
4. This alone fixes the most impactful gap — code generation without specialist guidance

### Incremental Delivery

1. Phase 2 → US1 → Validate (MVP: code-gen commands wired)
2. Add US2 → Validate (implement.md routes to all 13 agents)
3. Add US3 → Validate (lifecycle commands wired)
4. Polish → Final validation

---

## Notes

- All changes are markdown-only — no Python code, no tests to run
- Each command must stay under 200 lines (token budget)
- Agent loading pattern: "Read `agents/{name}.md` for {domain} guidance. Load all skills listed in the agent's Skills Loaded section."
- Primary agent is project-type-based, secondary agent is task-type-based
- 9 utility commands are explicitly NOT modified
