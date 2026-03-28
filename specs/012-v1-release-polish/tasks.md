# Tasks: v1 Release Polish & Roadmap Alignment

**Input**: Design documents from `/specs/012-v1-release-polish/`
**Prerequisites**: plan.md (required), spec.md (required)

**Tests**: Not requested — deliverables verified by schema validation, grep, and file existence.

**Organization**: Tasks grouped by user story. US3 runs FIRST (creates 4 skills, changing count from 116→120) so all subsequent count updates use final number. US1 = Plugin Marketplace Compliance (P1), US2 = Hook Reliability & Project Context (P2), US3 = Complete Skill Inventory (P2, runs first), US4 = v1.0 Roadmap Docs (P3), US5 = v1.1 Roadmap Corrections (P3), US6 = v1.2+ Roadmap Additions (P3).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3, US4, US5, US6)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Read target files to understand current structure before modifications.

- [x] T001 Read `.claude-plugin/plugin.json` to understand full manifest structure
- [x] T002 Read `.claude/settings.json` to understand current hook format
- [x] T003 Read `README.md` lines 83-100 to identify insertion point for security section
- [x] T004 Read `planning/12-version-roadmap.md` to understand current v1.1/v1.2 sections

**Checkpoint**: All target files read and understood.

---

## Phase 2: User Story 3 — Complete v1.0 Skill Inventory (Priority: P2, runs FIRST)

**Goal**: Create 4 missing cross-cutting skills BEFORE count updates so all counts use final number (120).

**Independent Test**: All 4 new skill directories exist with SKILL.md files under 400 lines.

### Implementation for User Story 3

- [x] T005 [P] [US3] Create `skills/microservice/event-catalogue/SKILL.md` (FR-011, missing #89) — metadata: name=event-catalogue, category=microservice, agent=docs-engineer. Content: event schema documentation per service, cross-service event registry, event naming conventions, versioning strategy, catalogue generation from code, Mermaid event flow diagrams. Max 400 lines.

- [x] T006 [P] [US3] Create `skills/infra/feature-flags/SKILL.md` (FR-011, missing #91) — metadata: name=feature-flags, category=infra, agent=dotnet-architect. Content: Microsoft.FeatureManagement package, IFeatureManager injection, feature gates ([FeatureGate]), percentage rollouts, time-window flags, custom filters, feature flag configuration in appsettings.json, Azure App Configuration integration, when to use vs when to use config. Max 400 lines.

- [x] T007 [P] [US3] Create `skills/architecture/multi-tenancy/SKILL.md` (FR-011, missing #92) — metadata: name=multi-tenancy, category=architecture, agent=dotnet-architect. Content: tenant isolation strategies (database-per-tenant, schema-per-tenant, shared with discriminator), tenant resolution (subdomain, header, claim), EF Core global query filters for tenant, tenant-aware DI registration, data partitioning patterns, when to use which strategy. Max 400 lines.

- [x] T008 [P] [US3] Create `skills/api/grpc-design/SKILL.md` (FR-011, missing #93) — metadata: name=grpc-design, category=api, agent=api-designer. Content: proto file design principles, service naming conventions, message design (StringValue for nullable, Timestamp for DateTime, DecimalValue), package naming, gRPC-JSON transcoding, gRPC-Web for browser clients, client generation, proto versioning, backward compatibility. Max 400 lines.

**Checkpoint**: 4 new SKILL.md files exist. `find skills/ -name "SKILL.md" | wc -l` = 120. All subsequent count updates MUST use 120.

---

## Phase 3: User Story 1 — Plugin Marketplace Compliance (Priority: P1)

**Goal**: Plugin manifest passes schema validation, all 27 descriptions trigger correctly, README has security section.

**Independent Test**: `grep "keywords" plugin.json` succeeds, `grep "Use when" plugin.json | wc -l` = 27, `grep "Security & Permissions" README.md` succeeds.

### Implementation for User Story 1

- [x] T009 [US1] Rename `tags` to `keywords` in `.claude-plugin/plugin.json` — change JSON key only, keep same array values (FR-001)

- [x] T010 [US1] Convert `author` in `.claude-plugin/plugin.json` from `"author": "Faysil Alshareef"` to `"author": {"name": "Faysil Alshareef", "url": "https://github.com/FaysilAlshareef"}` (FR-002)

- [x] T011 [US1] Update description in `.claude-plugin/plugin.json` to reflect "120 skills, 15 rules" — this is the final count after 4 new skills from Phase 2 (FR-003)

- [x] T012 [US1] Rewrite all 27 command descriptions in `.claude-plugin/plugin.json` with action verb + "Use when..." format, each under 200 chars (FR-004):
  - dotnet-ai.do: "Runs the full SDD lifecycle from spec to PR. Use when building a complete feature end-to-end."
  - dotnet-ai.detect: "Detects project architecture, .NET version, and patterns. Use when initializing or learning project structure."
  - dotnet-ai.learn: "Generates a project constitution from detected patterns. Use when persisting project knowledge across sessions."
  - dotnet-ai.init: "Initializes dotnet-ai-kit in a .NET project. Use when setting up a new project for AI-assisted development."
  - dotnet-ai.configure: "Opens interactive configuration wizard. Use when changing company name, naming patterns, or permission levels."
  - dotnet-ai.specify: "Creates a feature specification from a description. Use when starting a new feature or user story."
  - dotnet-ai.clarify: "Resolves ambiguities in a feature specification. Use when the spec has unclear or conflicting requirements."
  - dotnet-ai.plan: "Generates an implementation plan from the spec. Use when ready to design the technical approach."
  - dotnet-ai.tasks: "Breaks the plan into ordered executable tasks. Use when ready to start coding after planning."
  - dotnet-ai.analyze: "Analyzes plan consistency before coding. Use when validating spec-plan-task alignment."
  - dotnet-ai.implement: "Executes all planned implementation tasks. Use when ready to generate code from the task list."
  - dotnet-ai.review: "Reviews code against standards and conventions. Use when implementation is complete and ready for quality check."
  - dotnet-ai.verify: "Verifies build, tests, and formatting pass. Use when validating implementation before creating a PR."
  - dotnet-ai.pr: "Creates a pull request with linked changes. Use when implementation is verified and ready for team review."
  - dotnet-ai.add-aggregate: "Generates an event-sourced aggregate with events. Use when adding a new command-side domain entity."
  - dotnet-ai.add-entity: "Generates a query-side entity with handler. Use when adding a new read model for projections."
  - dotnet-ai.add-event: "Generates a domain event type for an aggregate. Use when adding a new event to an existing aggregate."
  - dotnet-ai.add-endpoint: "Generates an API endpoint with request/response. Use when adding a new REST or Minimal API route."
  - dotnet-ai.add-page: "Generates a Blazor page with data grid. Use when adding a new control panel UI page."
  - dotnet-ai.add-crud: "Generates full CRUD stack for an entity. Use when adding complete create/read/update/delete operations."
  - dotnet-ai.add-tests: "Generates test suite for existing code. Use when adding unit or integration tests to untested code."
  - dotnet-ai.docs: "Generates project documentation. Use when creating README, API docs, ADRs, or deployment guides."
  - dotnet-ai.status: "Shows current feature progress and phase. Use when checking where you are in the SDD lifecycle."
  - dotnet-ai.undo: "Reverts the last AI-generated changes safely. Use when the last action produced incorrect results."
  - dotnet-ai.explain: "Explains code patterns with examples. Use when learning architecture patterns or understanding existing code."
  - dotnet-ai.checkpoint: "Saves a progress checkpoint for session handoff. Use when pausing work to resume in a later session."
  - dotnet-ai.wrap-up: "Ends session with summary and handoff notes. Use when finishing work for the day or handing off to a teammate."

- [x] T013 [US1] Update YAML `description` field in all 27 `commands/*.md` files to match the new plugin.json descriptions (FR-005). Depends on T012 (descriptions finalized in plugin.json first). All 27 files have YAML frontmatter. Files: do.md, detect.md, learn.md, init.md, configure.md, specify.md, clarify.md, plan.md, tasks.md, analyze.md, implement.md, review.md, verify.md, pr.md, add-aggregate.md, add-entity.md, add-event.md, add-endpoint.md, add-page.md, add-crud.md, add-tests.md, docs.md, status.md, undo.md, explain.md, checkpoint.md, wrap-up.md

- [x] T014 [P] [US1] Add "Security & Permissions" section to `README.md` after the Quick Start section (after line ~93, before "One Command, Full Feature") (FR-006). Content: (a) "### What the Plugin Accesses" — reads .csproj/.sln/source files, writes generated code + .dotnet-ai-kit/ config, executes dotnet CLI commands, (b) "### Safety Hooks" — table of 4 hooks (bash-guard/commit-lint/edit-format/scaffold-restore with event and description), (c) "### Permission Levels" — table of 3 levels (minimal/standard/full with scope and best-for), (d) "### What the Plugin Does NOT Do" — never deploys, never pushes without confirm, never deletes outside workdir, never accesses network beyond configured domains

- [x] T015 [US1] Update `.claude-plugin/marketplace.json` to match plugin.json: rename `tags`→`keywords` if present, update description to "120 skills, 15 rules" (FR-012)

- [x] T016 [US1] Update all doc skill counts from 116 to 120 across: README.md, CLAUDE.md, CONTRIBUTING.md, CHANGELOG.md, `.specify/memory/constitution.md` (increment to v1.0.6), `planning/11-expanded-skills-inventory.md`, and any other files referencing "116 skills". Also update `skills_summary.total` in plugin.json from 116 to 120, and add category counts for the 4 new skills (microservice +1, infra +1, architecture +1, api +1).

**Note**: FR-003 (keep informational arrays) is a constraint — do NOT remove commands/agents/skills_summary/hooks arrays.

**Checkpoint**: plugin.json schema compliant, 27 descriptions have "Use when", README has security section, marketplace.json synced.

---

## Phase 3: User Story 2 — Hook Reliability & Project Context (Priority: P2)

**Goal**: Hooks have timeouts. AGENTS.md exists.

**Independent Test**: `grep "timeout" settings.json | wc -l` = 4. AGENTS.md exists at root.

### Implementation for User Story 2

- [x] T017 [P] [US2] Add `timeout` and `statusMessage` to all 4 hook entries in `.claude/settings.json` (FR-007, FR-008): bash-guard timeout=10 statusMessage="Checking command safety...", commit-lint timeout=30 statusMessage="Verifying code formatting...", edit-format timeout=30 statusMessage="Formatting C# file...", scaffold-restore timeout=15 statusMessage="Restoring packages..."

- [x] T018 [P] [US2] Create `AGENTS.md` at project root (FR-009) — tool-agnostic plain markdown with sections: Project Overview (what dotnet-ai-kit is, mention Claude Code as supported tool), Setup (Python 3.10+, .NET 8.0+, install command), Build & Test (pytest, ruff, pip install -e), Architecture Detection (12 project types), Development Workflow (SDD lifecycle), Code Conventions (pathlib, subprocess.run, utf-8, pydantic v2, token budgets), Testing (pytest, tmp_path, mock externals), Project Structure (directory tree). No .claude/ paths or Claude-specific YAML syntax.

**Checkpoint**: 4 hooks have timeout+statusMessage. AGENTS.md exists with 8 sections.

---

## Phase 5: User Story 4 — v1.0 Roadmap Documentation (Priority: P3)

**Goal**: Version roadmap documents all v1.0 late additions.

**Independent Test**: v1.0 Late Additions section lists paradigm skills, rules, frontmatter refactor, marketplace, AGENTS.md.

### Implementation for User Story 4

- [x] T019 [US4] Update v1.0 Late Additions in `planning/12-version-roadmap.md` (FR-025) — add to existing late additions section: 10 paradigm/best-practice skills (solid-principles, design-patterns, functional-csharp, fluent-validation, mapping-strategies, caching-strategies, rate-limiting, signalr-realtime, cors-configuration, input-sanitization), 6 enforcement rules (security, async-concurrency, data-access, api-design, observability, performance), skill frontmatter refactor to Agent Skills spec (metadata block format), marketplace support (marketplace.json, hook registration in settings.json), AGENTS.md cross-tool project context, 4 missing cross-cutting skills created (event-catalogue, feature-flags, multi-tenancy, grpc-design)

**Checkpoint**: v1.0 Late Additions complete.

---

## Phase 6: User Story 5 — v1.1 Roadmap Corrections (Priority: P3)

**Goal**: v1.1 reflects 2026 .NET ecosystem reality.

**Independent Test**: v1.1 section contains NServiceBus, MassTransit licensing, Wolverine, .NET 10, expanded Aspire, cross-tool.

### Implementation for User Story 5

- [x] T020 [US5] Update v1.1 messaging section in `planning/12-version-roadmap.md` (FR-013, FR-014, FR-015): (a) Promote NServiceBus from v2.0 to v1.1 — add as enterprise-grade paid messaging option, (b) Add MassTransit v9 licensing warning: commercial $400+/mo or free under $1M revenue, v8 EOL end of 2026, (c) Add Wolverine as free open-source messaging alternative to MassTransit

- [x] T021 [US5] Update v1.1 platform section in `planning/12-version-roadmap.md` (FR-016, FR-017): (a) Make .NET 10 LTS support explicit — templates, detection, C# 14 features (field-backed properties, null-conditional assignment), (b) Expand Aspire from "enhanced orchestration" to deep patterns: module isolation, observability dashboard, Polly resilience, Directory.Build.props standards, CI/CD best practices

- [x] T022 [US5] Add cross-tool support to v1.1 in `planning/12-version-roadmap.md` (FR-018): Cursor (.cursorrules + AGENTS.md), Copilot (.github/copilot-instructions.md + AGENTS.md), Codex (AGENTS.md native), Windsurf (.windsurf/rules/ + AGENTS.md)

**Checkpoint**: v1.1 section has all 6 corrections.

---

## Phase 7: User Story 6 — v1.2+ Roadmap Additions (Priority: P3)

**Goal**: v1.2 has new items. v2.0 unchanged.

**Independent Test**: v1.2 has Semantic Kernel, Wolverine, GraphQL, Blazor United. v2.0 unchanged.

### Implementation for User Story 6

- [x] T023 [US6] Add v1.2 new items to `planning/12-version-roadmap.md` (FR-019 to FR-023): (a) Semantic Kernel — architecture/semantic-kernel skill for AI-augmented microservices (production-ready, Agent Framework at RC), (b) Wolverine full messaging support — consumers, producers, saga support as MassTransit v8 EOL approaches, (c) GraphQL (HotChocolate) promoted from v2.0 — Apollo Federation v2, schema-first, subscriptions, DataLoader, (d) Blazor United templates — unified server/client rendering, 40% WASM payload reduction via AOT, (e) Confirm Dapr stays v1.2 with Aspire integration noted

- [x] T024 [US6] Verify v2.0 scope in `planning/12-version-roadmap.md` remains unchanged (FR-024): EventStoreDB, Marten, Strangler Fig, Service Mesh, Azure Functions, Multi-Cloud, Antigravity. Add note that GraphQL moved to v1.2 and NServiceBus moved to v1.1.

- [x] T025 [US6] Update `planning/11-expanded-skills-inventory.md` to reflect v1.1/v1.2 planned skills from roadmap corrections: add NServiceBus, Wolverine, Semantic Kernel, GraphQL skill entries to appropriate future version sections

**Checkpoint**: v1.2 has 5 new items. v2.0 scope verified.

---

## Phase 8: Polish & Verification

**Purpose**: Final validation across all scopes.

- [x] T026 Verify plugin.json: (a) `grep "keywords" .claude-plugin/plugin.json` succeeds, (b) `grep '"tags"' .claude-plugin/plugin.json` returns zero, (c) `grep "Use when" .claude-plugin/plugin.json | wc -l` = 27, (d) author is object

- [x] T027 Verify README + hooks: (a) `grep "Security & Permissions" README.md` succeeds, (b) `grep "timeout" .claude/settings.json | wc -l` = 4, (c) `grep "statusMessage" .claude/settings.json | wc -l` = 4

- [x] T028 Verify AGENTS.md + skills: (a) AGENTS.md exists at root, (b) new skills exist: `test -f skills/microservice/event-catalogue/SKILL.md && test -f skills/infra/feature-flags/SKILL.md && test -f skills/architecture/multi-tenancy/SKILL.md && test -f skills/api/grpc-design/SKILL.md`

- [x] T029 Verify roadmap: (a) v1.0 Late Additions has paradigm skills + rules + refactor, (b) v1.1 has NServiceBus + MassTransit warning + Wolverine + .NET 10, (c) v1.2 has Semantic Kernel + GraphQL + Blazor United, (d) v2.0 unchanged

**Checkpoint**: All success criteria SC-001 through SC-010 verified.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — read files immediately
- **US3 Skills (Phase 2)**: Depends on Setup — creates 4 skills FIRST (count 116→120)
- **US1 Manifest (Phase 3)**: Depends on US3 — all counts must use 120
- **US2 Hooks+AGENTS (Phase 4)**: Independent of US1 — different files
- **US4-US6 Roadmap (Phases 5-7)**: Independent — planning docs only
- **Verification (Phase 8)**: Depends on all stories complete

### User Story Dependencies

- **US3**: Runs FIRST — creates skills that change total count to 120
- **US1**: Depends on US3 — plugin.json/marketplace/README counts must be 120
- **US2**: Independent (different files: settings.json, AGENTS.md)
- **US4, US5, US6**: Independent (planning docs, can run in parallel)
- T013 depends on T012 (command .md descriptions must match plugin.json)

### Parallel Opportunities

- T005-T008: all 4 skills in parallel (Phase 2)
- After Phase 2: US1, US2, US4, US5, US6 can start (US1 sequential internally)
- T017 + T018: hooks and AGENTS.md in parallel
- T019 + T020-T022 + T023-T025: roadmap tasks in parallel
- T026-T029: verification in parallel

---

## Implementation Strategy

### MVP First (US3 + US1)

1. Setup (T001-T004)
2. US3: Create 4 missing skills (T005-T008) — count becomes 120
3. US1: manifest + descriptions + security + counts (T009-T016)
4. **STOP and VALIDATE**: Plugin is marketplace-compliant with accurate counts

### Incremental Delivery

1. US1 (manifest + descriptions + security) → marketplace-ready
2. US2 (hooks + AGENTS.md) → reliability + cross-tool ready
3. US3 (4 missing skills) → inventory complete
4. US4 + US5 + US6 (roadmap) → planning aligned
5. Verify all

---

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 29 |
| US3 tasks | 4 (missing skills — runs FIRST) |
| US1 tasks | 8 (manifest + descriptions + security + marketplace + count updates) |
| US2 tasks | 2 (hooks + AGENTS.md) |
| US4 tasks | 1 (v1.0 roadmap) |
| US5 tasks | 3 (v1.1 corrections) |
| US6 tasks | 3 (v1.2+ additions) |
| Setup tasks | 4 |
| Verify tasks | 4 |
| Parallel opportunities | After US3: US1, US2, US4-6 can start. US2/US4-6 independent. |
| Suggested MVP | US3 + US1 (skills complete + marketplace compliance) |
