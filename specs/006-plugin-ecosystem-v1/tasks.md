# Tasks: Plugin Ecosystem v1.0

**Input**: Design documents from `/specs/006-plugin-ecosystem-v1/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the spec. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create plugin directory structure

- [x] T001 [P] Create `.claude-plugin/` directory at repository root
- [x] T002 [P] Create `hooks/` directory at repository root

---

## Phase 2: User Story 1 - Plugin Manifest (Priority: P1) 🎯 MVP

**Goal**: Make dotnet-ai-kit installable as a Claude Code plugin via `/plugin install`

**Independent Test**: Run `/plugin validate` on the repository and confirm plugin.json is valid. Verify all component directories (commands/, skills/, agents/, rules/, hooks/) are detected.

### Implementation for User Story 1

- [x] T003 [US1] Create plugin manifest at `.claude-plugin/plugin.json` with name `dotnet-ai-kit`, version `1.0.0`, description, author `Faysil Alshareef`, homepage URL, tags array (`dotnet`, `csharp`, `.net`, `cqrs`, `microservices`, `clean-architecture`, `vertical-slice`, `ddd`, `code-generation`, `sdd`), and category `development`. Schema per `specs/006-plugin-ecosystem-v1/contracts/plugin-json.md`.
- [x] T004 [US1] Verify plugin directory layout: `.claude-plugin/` contains only `plugin.json`; `commands/`, `skills/`, `agents/`, `rules/`, `hooks/` exist at repo root (not inside `.claude-plugin/`).

**Checkpoint**: Plugin manifest exists and validates. `/plugin install` can discover all component directories.

---

## Phase 3: User Story 2 - Agent Skills Compliance (Priority: P1)

**Goal**: Make all 104 SKILL.md files conform to the Agent Skills specification by adding `dotnet-ai-` prefix to the `name` field. Enables cross-agent compatibility with 16+ tools.

**Independent Test**: Parse every SKILL.md file, verify `name` starts with `dotnet-ai-` and `description` is non-empty.

### Implementation for User Story 2

- [x] T005 [US2] Write a Python migration script at `scripts/migrate_skill_names.py` that: reads each `skills/**/**/SKILL.md`, parses YAML frontmatter, prepends `dotnet-ai-` to the `name` field if not already prefixed, preserves all other frontmatter fields (`description`, `category`, `agent`), preserves the markdown body unchanged, and writes the file back. The script must be idempotent (running twice produces same result).
- [x] T006 [US2] Run the migration script on all 104 SKILL.md files in `skills/` directory.
- [x] T007 [US2] Write a validation script at `scripts/validate_skills.py` that checks every `skills/**/**/SKILL.md` has: (1) `name` field starting with `dotnet-ai-`, (2) `name` is lowercase kebab-case, (3) `description` is non-empty, (4) existing `category` and `agent` fields are preserved. Print pass/fail summary.
- [x] T008 [US2] Run validation script and confirm 100% of 104 files pass.

**Checkpoint**: All 104 SKILL.md files have `dotnet-ai-` prefixed names and pass Agent Skills spec validation.

---

## Phase 4: User Story 3 - Hooks (Priority: P2)

**Goal**: Add 4 safety/quality hooks that protect against dangerous commands, auto-format code, auto-restore packages, and lint before commits.

**Independent Test**: Manually trigger each hook event type and verify correct behavior (block dangerous commands, format .cs files, restore after scaffold, lint before commit).

### Implementation for User Story 3

- [x] T009 [P] [US3] Create pre-bash-guard hook at `hooks/pre-bash-guard.sh`. Must: parse the incoming command, split on pipes/chains, check first verb of each segment against a default blocklist of 20+ dangerous patterns (per `specs/006-plugin-ecosystem-v1/contracts/hooks-config.md`), exit non-zero with warning message if match found, exit 0 if safe. Must check if hook is enabled via settings. Include the default blocklist as an array variable. Support `extra_patterns` from settings.
- [x] T010 [P] [US3] Create post-edit-format hook at `hooks/post-edit-format.sh`. Must: check if edited file ends in `.cs`, check if `dotnet` is on PATH (skip silently if not), check if hook is enabled via settings, run `dotnet format` on the specific file, exit 0 regardless (non-blocking, warn mode).
- [x] T011 [P] [US3] Create post-scaffold-restore hook at `hooks/post-scaffold-restore.sh`. Must: check if the executed command contained `dotnet new`, check if `dotnet` is on PATH (skip silently if not), check if hook is enabled via settings, run `dotnet restore` in current directory, exit 0 regardless (non-blocking, warn mode).
- [x] T012 [P] [US3] Create pre-commit-lint hook at `hooks/pre-commit-lint.sh`. Must: check if the command contains `git commit`, check if `dotnet` is on PATH (skip silently if not), check if hook is enabled via settings, run `dotnet format --verify-no-changes`, exit non-zero if formatting issues found (blocking mode), exit 0 if clean.
- [x] T013 [US3] Make all 4 hook scripts executable (`chmod +x hooks/*.sh`). Verify each script has a proper shebang line (`#!/usr/bin/env bash`).

**Checkpoint**: All 4 hooks exist, are executable, check prerequisites before running, and support enable/disable toggling.

---

## Phase 5: User Story 4 - C# LSP MCP Configuration (Priority: P2)

**Goal**: Add MCP configuration pointing to csharp-ls for semantic C# code intelligence (go-to-definition, find references, diagnostics).

**Independent Test**: With `csharp-ls` installed, verify the MCP server starts and responds to tool calls. Without `csharp-ls`, verify no errors on plugin load.

### Implementation for User Story 4

- [x] T014 [US4] Create MCP configuration at `.mcp.json` in repository root. Define `csharp-ls` server with `command: "csharp-ls"`, `args: ["--solution", "."]`, `transport: "stdio"`. Schema per `specs/006-plugin-ecosystem-v1/contracts/mcp-json.md`. Verify graceful degradation: when `csharp-ls` is not installed, the plugin must load without errors (FR-009).

**Checkpoint**: `.mcp.json` exists and points to csharp-ls. When csharp-ls is installed, Claude can use C# language intelligence tools.

---

## Phase 6: User Story 5 - Marketplace Discovery & Differentiation (Priority: P3)

**Goal**: Clearly position dotnet-ai-kit in marketplaces with differentiation from Microsoft dotnet/skills and dotnet-claude-kit.

**Independent Test**: Read the README marketplace section and verify it explains unique value: SDD lifecycle, 7 code gen commands, AI detection, 12 project types. Verify no skill name conflicts with `dotnet-ai-` prefix.

### Implementation for User Story 5

- [x] T015 [P] [US5] Add a `## Plugin Installation` section to `README.md` (after Quick Start) with: Claude Code marketplace install instructions (`/plugin marketplace add FaysilAlshareef/dotnet-ai-kit`, `/plugin install dotnet-ai-kit`), optional csharp-ls install command, and pip-based alternative install.
- [x] T016 [P] [US5] Add a `## How dotnet-ai-kit Differs` section to `README.md` with a comparison table showing unique features vs Microsoft dotnet/skills (no SDD lifecycle, no code gen commands, no detection) and vs dotnet-claude-kit (no SDD lifecycle, fewer skills, no CLI tool). Highlight: 26 commands, 104 skills, 13 agents, full SDD lifecycle, 7 code gen commands, AI project detection, 12 project types.
- [x] T017 [US5] Update `CHANGELOG.md` under `[Unreleased]` section to document: Claude Code plugin format added, Agent Skills spec compliance, 4 hooks added, C# LSP MCP config added, marketplace metadata added.

**Checkpoint**: README has plugin install and differentiation sections. CHANGELOG documents all new features.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validation, documentation consistency, and cleanup

- [x] T018 Validate complete plugin structure: confirm `.claude-plugin/plugin.json` exists, all 104 SKILL.md files have `dotnet-ai-` prefix, all 4 hooks exist in `hooks/`, `.mcp.json` exists, README has marketplace section. Verify slash commands are auto-namespaced by the plugin format (FR-011) and MCP config loads cleanly when `csharp-ls` is not on PATH (FR-009).
- [x] T019 Run existing test suite (`pytest tests/ -q`) and linter (`ruff check src/ tests/`) to confirm no regressions from SKILL.md migration or other changes.
- [x] T020 Update CLAUDE.md to document the new plugin format, hooks directory, and .mcp.json in the Project Structure section.
- [x] T021 Remove the migration script (`scripts/migrate_skill_names.py`) and validation script (`scripts/validate_skills.py`) after confirming all SKILL.md files are migrated. These are one-time-use tools.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **User Stories (Phases 2-6)**: Depend on Setup (Phase 1) for directories to exist
  - US1 (Plugin Manifest) and US2 (Skills Migration) are both P1 and can run in parallel
  - US3 (Hooks) and US4 (MCP) are both P2 and can run in parallel after Setup
  - US5 (Marketplace) is P3 and can run after US1+US2 complete (needs final counts for README)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 1 — No dependencies on other stories
- **US2 (P1)**: Can start after Phase 1 — No dependencies on other stories
- **US3 (P2)**: Can start after Phase 1 — No dependencies on other stories
- **US4 (P2)**: Can start after Phase 1 — No dependencies on other stories
- **US5 (P3)**: Soft dependency on US1+US2 for accurate feature counts in README

### Within Each User Story

- US1: Single manifest file, sequential
- US2: Migration script → run migration → validation script → validate (sequential)
- US3: All 4 hooks can be created in parallel [P], then chmod at end
- US4: Single config file, no internal dependencies
- US5: README sections can be written in parallel [P], then CHANGELOG

### Parallel Opportunities

- T001 and T002 can run in parallel (different directories)
- US1 (T003-T004) and US2 (T005-T008) can run in parallel (different files entirely)
- US3 (T009-T012) hooks can all be created in parallel (different files)
- US3 and US4 can run in parallel
- T015 and T016 can run in parallel (different README sections)

---

## Parallel Example: User Story 3 (Hooks)

```text
# Launch all 4 hooks in parallel (different files, no dependencies):
Task: "Create pre-bash-guard hook at hooks/pre-bash-guard.sh"
Task: "Create post-edit-format hook at hooks/post-edit-format.sh"
Task: "Create post-scaffold-restore hook at hooks/post-scaffold-restore.sh"
Task: "Create pre-commit-lint hook at hooks/pre-commit-lint.sh"

# Then sequentially:
Task: "Make all hook scripts executable"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: US1 Plugin Manifest (T003-T004)
3. **STOP and VALIDATE**: Plugin validates via `/plugin validate`
4. This alone makes dotnet-ai-kit discoverable as a Claude Code plugin

### Incremental Delivery

1. Setup → Plugin Manifest (MVP: plugin discoverable)
2. Add Skills Migration → All skills cross-agent compatible
3. Add Hooks → Safety/quality automation active
4. Add MCP Config → Semantic code intelligence available
5. Add Marketplace Docs → Differentiation clear to users

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup (Phase 1) together
2. Once Setup is done:
   - Developer A: US1 (Plugin Manifest) + US4 (MCP Config) — both are small
   - Developer B: US2 (Skills Migration) — bulk work, 104 files
   - Developer C: US3 (Hooks) — 4 scripts
3. Once US1+US2 complete: Developer A does US5 (Marketplace Docs)
4. Everyone validates in Phase 7

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- SKILL.md migration (US2) is the largest task by file count (104 files) but is automated via script
- Hooks (US3) are the most complex code to write — each has prerequisite checks, blocklist matching, and enable/disable logic
- MCP config (US4) is a single JSON file — smallest task
- All user stories are independently testable after completion
