# Tasks: v2 Profile, Rule, and Dynamic Delivery

**Input**: Design documents from `specs/024-v2-profile-rule-and-dynamic-delivery/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
**Tests**: Required by FR-021/FR-022, the contracts, and the standing gates (constitution mandates TDD).
**Organization**: Grouped by user story. **US2 (dedup) is sequenced before US1 (always-on delivery)** because always-on profile delivery would otherwise double-inject the duplicated generic constraints (planning/29 C2, hard prerequisite).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallelizable — different files, no dependency on an incomplete task.
- **[Story]**: Maps the task to the user story from `spec.md`.
- Every task names the primary file or directory it changes or validates.

---

## Phase 1: Setup

**Purpose**: Confirm branch/context and baseline gates before changing implementation files.

- [ ] T001 Confirm branch and feature paths in `specs/024-v2-profile-rule-and-dynamic-delivery/spec.md`
- [ ] T002 Run `.specify/scripts/powershell/check-prerequisites.ps1 -Json` and validate `specs/024-v2-profile-rule-and-dynamic-delivery/plan.md`
- [ ] T003 [P] Run `dotnet build dotnet-ai-kit.slnx -warnaserror`
- [ ] T004 [P] Run `dotnet test dotnet-ai-kit.slnx`
- [ ] T005 [P] Run `dotnet run --project src/DotnetAiKit.Cli -- generate --check --out build/`

---

## Phase 2: Foundational

**Purpose**: Shared classification + test infrastructure that blocks the user stories.

- [ ] T006 Add a pure name-based `ProfileTier` classifier (architecture vs role/band sets) in `src/DotnetAiKit.Core/Artifacts/ProfileTier.cs`, with a corpus-integrity test asserting every authored profile name maps to exactly one tier in `tests/DotnetAiKit.Core.Tests/ProfileTierTests.cs`
- [ ] T007 [P] Add shared profile/rule delivery test helpers in `tests/DotnetAiKit.Acceptance.Tests/ProfileDeliveryTestHelpers.cs`
- [ ] T008 [P] Add the universal-rule signature corpus (the dedup check's expected-overlap source) in `tests/DotnetAiKit.Acceptance.Tests/ProfileDeliveryTestHelpers.cs`

**Checkpoint**: Tier classifier + helpers ready; user-story work can begin.

---

## Phase 3: User Story 2 - Guidance Is Not Duplicated Across Rules and Profiles (Priority: P1, prerequisite for US1)

**Goal**: Strip generic-rule restatement from profiles so always-on delivery cannot double-inject.

**Independent Test**: The dedup check fails before edits and passes after; no profile restates a universal-rule constraint.

### Tests for User Story 2

- [ ] T009 [US2] Add the rule/profile duplication check (C-RC-1) as a deterministic structural assertion — profiles MUST NOT contain rule-owned section headings — not fuzzy text overlap, in `tests/DotnetAiKit.Acceptance.Tests/RuleProfileCoherenceTests.cs`

### Implementation for User Story 2

- [ ] T010 [P] [US2] Strip universal-rule restatement and reference the rules in `artifacts/profiles/generic.md`
- [ ] T011 [P] [US2] Remove the duplicate `## Data Access` sections and generic tails in `artifacts/profiles/vsa.md`
- [ ] T012 [P] [US2] Remove the generic Testing/Data-Access tail in `artifacts/profiles/clean-arch.md`
- [ ] T013 [P] [US2] Remove the generic Testing/Data-Access tail in `artifacts/profiles/ddd.md`
- [ ] T014 [P] [US2] Remove the generic Testing/Data-Access tail in `artifacts/profiles/modular-monolith.md`
- [ ] T015 [US2] Run `dotnet test dotnet-ai-kit.slnx --filter "FullyQualifiedName~RuleProfileCoherence"` for `tests/DotnetAiKit.Acceptance.Tests/RuleProfileCoherenceTests.cs`

**Checkpoint**: Profiles carry only architecture/role-specific constraints; dedup check green. Always-on delivery is now safe.

---

## Phase 4: User Story 1 - Architecture Profile Reaches the Project as Always-On Guidance (Priority: P1) MVP

**Goal**: Deliver the single selected architecture profile always-on on Claude and fix the output-style bug. **Depends on US2 (dedup).**

**Independent Test**: After `init`, `.claude/profiles/<arch>.md` exists for the resolved architecture only, the hook injects it always-on, and the output-style references it.

### Tests for User Story 1

- [ ] T016 [US1] Add `ProfileDeliveryTests` for C-PD-1 (footprint file, single-select, hook always-on injection, output-style reference) and C-PD-4 (default generic) in `tests/DotnetAiKit.Acceptance.Tests/ProfileDeliveryTests.cs`

### Implementation for User Story 1

- [ ] T017 [US1] Write `.claude/profiles/<arch>.md` (selected from `metadata.Architecture`, default `generic`, deduped content) in `src/DotnetAiKit.Hosts/Claude/ClaudeHostAdapter.cs`
- [ ] T018 [US1] Extend the hook to load `.claude/profiles/*.md` and inject by tier — the architecture profile (no globs) always-on, role profiles (their `TargetPaths`) glob-matched JIT exactly like domain rules — in `src/DotnetAiKit.Cli/Commands/HookCommand.cs` and `src/DotnetAiKit.Application/UseCases/PreToolUseHookService.cs`
- [ ] T019 [US1] Reference the delivered profile (fix the names-but-never-ships bug) in `src/DotnetAiKit.Hosts/Claude/ClaudeOutputStyleWriter.cs`
- [ ] T020 [US1] Fold the per-project profile file into the footprint hash in `src/DotnetAiKit.Infrastructure/ManifestIntegrityService.cs` (and the call in `ClaudeHostAdapter.cs`)
- [ ] T021 [US1] Run `dotnet test dotnet-ai-kit.slnx --filter "FullyQualifiedName~ProfileDelivery"` for `tests/DotnetAiKit.Acceptance.Tests/ProfileDeliveryTests.cs`

**Checkpoint**: The architecture profile reaches Claude always-on; the output-style is honest. MVP demonstrable.

---

## Phase 5: User Story 3 - Role/Band Profiles Deliver Additively and Path-Scoped (Priority: P2)

**Goal**: Deliver role profiles path-scoped per host (never all always-on); mark host capability gaps explicitly.

**Independent Test**: Role profiles are path-scoped on path-capable hosts and absent from always-on channels; unsupported capabilities carry an explicit marker.

### Tests for User Story 3

- [ ] T022 [US3] Add role-profile path-scope (C-PD-2) and per-host channel/marker (C-PD-3) assertions in `tests/DotnetAiKit.Acceptance.Tests/ProfileDeliveryTests.cs`

### Implementation for User Story 3

- [ ] T023 [US3] Deliver Claude role profiles JIT by mirroring the domain-rule channel: write them per-solution to `.claude/profiles/` (with `paths:`) in `src/DotnetAiKit.Hosts/Claude/ClaudeHostAdapter.cs` so the hook (T018) glob-matches them; emit the plugin-distribution copy in `src/DotnetAiKit.Hosts/Claude/ClaudeProjector.cs`. NOTE: the hook reads the per-solution `.claude/profiles/`, not the plugin copy — same dual-emission pattern domain rules already use
- [ ] T024 [P] [US3] Project role profiles as `.mdc` with `globs` and arch profiles as selectable (`alwaysApply: false`) in `src/DotnetAiKit.Hosts/Cursor/CursorProjector.cs`
- [ ] T025 [P] [US3] Project role profiles as `.instructions.md applyTo` and arch profiles as selectable in `src/DotnetAiKit.Hosts/Copilot/CopilotProjector.cs`
- [ ] T026 [P] [US3] Add a profiles pointer/summary — NOT full profile bodies, since `AGENTS.md` is already ~950 lines (full trim is feature 026) — with an explicit no-gating marker in `src/DotnetAiKit.Hosts/Codex/CodexProjector.cs`
- [ ] T027 [US3] Re-accept the projection golden in `tests/DotnetAiKit.Hosts.Tests/GoldenProjectionTests.Full_projection_shape_is_byte_stable.verified.txt`
- [ ] T028 [US3] Run `dotnet test dotnet-ai-kit.slnx --filter "FullyQualifiedName~ProfileDelivery"`

**Checkpoint**: Role profiles deliver path-scoped across hosts; capability gaps explicit.

---

## Phase 6: User Story 4 - Rule Path-Scoping Is Honest (Priority: P2)

**Goal**: Narrow the three over-broad globs, keep the two genuinely broad, make `deterministic-enforcement` universal.

**Independent Test**: Glob assertions hold; `error-handling`/`performance` stay broad; `deterministic-enforcement` is universal; no testing residue.

### Tests for User Story 4

- [ ] T029 [US4] Add glob-scope assertions (C-RC-2/3) and the testing-residue guard (C-RC-4) in `tests/DotnetAiKit.Acceptance.Tests/RuleProfileCoherenceTests.cs`

### Implementation for User Story 4

- [ ] T030 [P] [US4] Narrow paths to DI/composition in `artifacts/rules/domain/mediator-abstraction.md`
- [ ] T031 [P] [US4] Narrow paths to DI/messaging in `artifacts/rules/domain/messaging-bus-selection.md`
- [ ] T032 [P] [US4] Narrow paths to AI features in `artifacts/rules/domain/ai-integration.md`
- [ ] T033 [US4] Convert to universal scope (remove path glob; registry/pointer framing) in `artifacts/rules/domain/deterministic-enforcement.md`
- [ ] T034 [US4] Assert `error-handling`/`performance` remain broad and confirm no v1/Python residue in `artifacts/rules/domain/testing.md` (verify the 023 removal is complete)
- [ ] T035 [US4] Re-accept golden in `tests/DotnetAiKit.Hosts.Tests/` and run `dotnet test --filter "FullyQualifiedName~RuleProfileCoherence"`

**Checkpoint**: Rule scoping is honest across all hosts.

---

## Phase 7: User Story 5 - MCP and LSP Configuration Is Projected to Hosts (Priority: P2)

**Goal**: Project MCP config per host from one descriptor; LSP for Claude/Copilot with explicit unsupported markers; wire LSP into nav agents.

**Independent Test**: Each host gets MCP config from the single descriptor; LSP present for supported hosts and explicitly marked for the rest; files are byte-stable.

### Tests for User Story 5

- [ ] T036 [US5] Add `McpLspProjectionTests` (C-ML-1..4) in `tests/DotnetAiKit.Acceptance.Tests/McpLspProjectionTests.cs`

### Implementation for User Story 5

- [ ] T037 [US5] Author a target-facing MCP descriptor in `artifacts/` — describing the future `dotnet-ai mcp serve`, **marked not-yet-available** (NOT the kit's dev `codebase-memory-mcp`) — and project it per host (Claude `.mcp.json`, Codex `[mcp_servers]`, Cursor `mcpServers`, Copilot form) via a shared writer in `src/DotnetAiKit.Hosts/` (new `McpProjection.cs` + per-projector calls). [D-MCP resolved 2026-06-02 → option (a); feature `029` activates the descriptor when the kit's server exists]
- [ ] T038 [US5] Project LSP config from the root `.lsp.json` (Claude GA, Copilot Preview) and emit an explicit unsupported marker for Codex/Cursor in `src/DotnetAiKit.Hosts/` (new `LspProjection.cs` + per-projector calls). LSP proceeds regardless of D-MCP — `csharp-ls` is target-relevant.
- [ ] T039 [P] [US5] Add symbol-precise navigation guidance (prefer `goToDefinition`/`findReferences`) in `artifacts/agents/reviewer.md`, `artifacts/agents/dotnet-architect.md`, `artifacts/agents/ef-specialist.md`
- [ ] T040 [US5] Re-accept golden for new MCP/LSP files and run `dotnet test --filter "FullyQualifiedName~McpLspProjection"`

**Checkpoint**: MCP/LSP configuration is projected deterministically with explicit support markers.

---

## Phase 8: Projection, Review & Verification

**Purpose**: The mandatory post-implementation review (no `/speckit.review` command), after implementation and before final polish (FR-021/FR-022).

- [ ] T041 Run `dotnet run --project src/DotnetAiKit.Cli -- generate` and inspect generated paths in `build/`
- [ ] T042 Review changed authored artifacts (`artifacts/profiles`, `artifacts/rules/domain`, `artifacts/agents`) for correctness, scope, dedup, and policy consistency
- [ ] T043 Review changed source and tests for deterministic, cross-platform, clean-architecture behavior in `src/` and `tests/`
- [ ] T044 Verify profile content reaches initialized/projected host outputs (US1/US3) in `build/` and the per-solution footprint
- [ ] T045 Verify no duplicate profile/rule injection (dedup check) in `tests/DotnetAiKit.Acceptance.Tests/RuleProfileCoherenceTests.cs`
- [ ] T046 Verify MCP/LSP determinism and explicit capability markers in `tests/DotnetAiKit.Acceptance.Tests/McpLspProjectionTests.cs`
- [ ] T047 Run `dotnet build dotnet-ai-kit.slnx -warnaserror`
- [ ] T048 Run `dotnet test dotnet-ai-kit.slnx`
- [ ] T049 Run `dotnet format dotnet-ai-kit.slnx --verify-no-changes`
- [ ] T050 Run `dotnet run --project src/DotnetAiKit.Cli -- generate --check --out build/`

**Checkpoint**: Post-implementation review and all standing gates complete.

---

## Phase 9: Polish

**Purpose**: Finish documentation and reflect the implemented state.

- [ ] T051 Update deferred/decision notes in `specs/024-v2-profile-rule-and-dynamic-delivery/research.md` and validation steps in `quickstart.md` if commands changed
- [ ] T052 Confirm every task is marked complete in `specs/024-v2-profile-rule-and-dynamic-delivery/tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup. `ProfileTier` (T006) blocks all profile-delivery work.
- **US2 dedup (Phase 3)**: Depends on Foundational. **Hard prerequisite for US1.**
- **US1 always-on (Phase 4)**: Depends on US2 (else always-on delivery double-injects the duplicated constraints).
- **US3 / US4 / US5 (Phases 5–7)**: Depend on Foundational; US3 depends on US1's profile-projection helper landing first. US4 and US5 are independent of profile delivery and of each other.
- **Review & Verification (Phase 8)**: Depends on all implemented stories.
- **Polish (Phase 9)**: Depends on Phase 8.

### Within Each User Story

- Tests first, then authored/source changes, then the targeted test command and golden re-accept.
- Edit only `artifacts/` source and regenerate `build/`; never hand-edit generated output.

---

## Parallel Opportunities

- **US2**: T010–T014 (five distinct profile files) run in parallel after T009.
- **US3**: T024–T026 (Cursor/Copilot/Codex projectors) run in parallel after T023 establishes the shared helper.
- **US4**: T030–T032 (three rule files) run in parallel after T029.
- **US5**: T039 (agent edits) runs parallel to T037/T038 (projection code).
- Across stories: US4 and US5 can proceed in parallel with US3 once US1 lands.

---

## Implementation Strategy

### MVP First

1. Setup + Foundational.
2. **US2 dedup** (the prerequisite), then **US1 always-on delivery** — this is the demonstrable MVP (the headline profile-delivery outcome) and is safe only after dedup.
3. Regenerate and run the standing gates before continuing to the P2 stories if time is constrained.

### Incremental Delivery

1. Deliver dedup + arch always-on first (fixes the highest-value gap and the output-style bug).
2. Deliver role path-scoping and rule-glob coherence next (cross-host consistency).
3. Deliver MCP/LSP projection last (additive install wiring; the 029 install track).

### Review Discipline

Phase 8 is mandatory because `.claude/commands` has no review command — treat it as the post-implementation review before final polish.
