# Tasks: v2 Corpus Correctness and Delivery Foundation

**Input**: Design documents from `specs/023-v2-corpus-correctness-and-delivery-foundation/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
**Tests**: Required by FR-010, FR-012, FR-015 and standing gates.
**Organization**: Tasks are grouped by user story so each repair slice can be implemented and tested independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete tasks.
- **[Story]**: Maps the task to the matching user story from `spec.md`.
- Every task names the primary file or directory it changes or validates.

---

## Phase 1: Setup

**Purpose**: Confirm the feature branch, command context, and baseline gates before changing implementation files.

- [X] T001 Confirm current branch and active feature paths in `specs/023-v2-corpus-correctness-and-delivery-foundation/spec.md`
- [X] T002 Run `.specify/scripts/powershell/check-prerequisites.ps1 -Json` and validate `specs/023-v2-corpus-correctness-and-delivery-foundation/plan.md`
- [X] T003 [P] Run `dotnet build dotnet-ai-kit.slnx -warnaserror` for `dotnet-ai-kit.slnx`
- [X] T004 [P] Run `dotnet test dotnet-ai-kit.slnx` for `tests/`
- [X] T005 [P] Run `dotnet run --project src/DotnetAiKit.Cli -- generate --check` for `build/`

---

## Phase 2: Foundational

**Purpose**: Add reusable test and review support that blocks all story implementation.

- [X] T006 Add shared corpus loading helpers for repair tests in `tests/DotnetAiKit.Acceptance.Tests/CorpusRepairTestHelpers.cs`
- [X] T007 [P] Add generated-output path assertion helpers in `tests/DotnetAiKit.Acceptance.Tests/GeneratedOutputAssertions.cs`
- [X] T008 [P] Add manifest JSON parsing helpers in `tests/DotnetAiKit.Acceptance.Tests/ManifestJsonAssertions.cs`
- [X] T009 Record broad deferred defects and target follow-on specs in `specs/023-v2-corpus-correctness-and-delivery-foundation/research.md`

**Checkpoint**: Shared helpers and deferral policy are ready; user story work can begin.

---

## Phase 3: User Story 1 - Broken Shipped Guidance Is Repaired (Priority: P1) MVP

**Goal**: Repair the eight broken shipped samples and localized serious correctness/security defects selected from `planning/30`.

**Independent Test**: Targeted artifact repair tests fail before repairs, then pass after authored artifacts are corrected and regenerated.

### Tests for User Story 1

- [X] T010 [US1] Add guards for the eight broken artifact samples in `tests/DotnetAiKit.Acceptance.Tests/ArtifactContentRepairTests.cs`
- [X] T011 [US1] Add guards for localized serious correctness/security repairs in `tests/DotnetAiKit.Acceptance.Tests/ArtifactContentRepairTests.cs`
- [X] T012 [US1] Add a `RuntimeMoniker.Net10_0` guard for touched testing guidance in `tests/DotnetAiKit.Acceptance.Tests/ArtifactContentRepairTests.cs`

### Implementation for User Story 1

- [X] T013 [US1] Move `[ValidatableType]` to the valid class target and add the .NET 10 experimental caveat in `artifacts/skills/api/minimal-api-validation/SKILL.md`
- [X] T014 [P] [US1] Remove the duplicate constructor sample in `artifacts/skills/core/configuration/SKILL.md`
- [X] T015 [P] [US1] Fix JWT inbound claim mapping, refresh expiry, null user handling, permission claims, and token handler guidance in `artifacts/skills/security/auth-jwt/SKILL.md`
- [X] T016 [P] [US1] Add `IDialogService`, define `OpenEditDialog`, and align nested gateway usage in `artifacts/skills/microservice/controlpanel/blazor-component/SKILL.md`
- [X] T017 [P] [US1] Replace the nonexistent generic delete call in `artifacts/skills/microservice/controlpanel/gateway-facade/SKILL.md`
- [X] T018 [P] [US1] Fix the single-operation Replace/Delete transactional batch path in `artifacts/skills/microservice/cosmos/transactional-batch/SKILL.md`
- [X] T019 [P] [US1] Reconcile proto cents fields and decimal mapping in `artifacts/skills/microservice/grpc/service-definition/SKILL.md`
- [X] T020 [US1] Rewrite mismatched outbox/event-sourcing tests and update runtime moniker in `artifacts/knowledge/testing-patterns.md`
- [X] T021 [P] [US1] Fix EF multi-tenant query filter caching and sync tenant stamping guidance in `artifacts/skills/architecture/multi-tenancy/SKILL.md`
- [X] T022 [P] [US1] Encode model values in HTML email samples in `artifacts/skills/infra/email-notifications/SKILL.md`
- [X] T023 [P] [US1] Catch timeout cancellation and execute compensation in `artifacts/skills/messaging/dapr-workflow/SKILL.md`
- [X] T024 [P] [US1] Replace dead circuit-breaker health check logic with state-provider guidance in `artifacts/skills/resilience/circuit-breaker/SKILL.md`
- [X] T025 [P] [US1] Fix changelog git-log filtering so conventional commit subjects are matched in `artifacts/skills/docs/changelog-gen/SKILL.md`
- [X] T026 [P] [US1] Await service-bus processor lifecycle close paths in `artifacts/skills/microservice/processor/hosted-service/SKILL.md`
- [X] T027 [P] [US1] Await listener lifecycle close paths and avoid poison-message redelivery loops in `artifacts/skills/microservice/query/listener-pattern/SKILL.md`
- [X] T028 [P] [US1] Persist the Cosmos partition-key value used by reads in `artifacts/skills/microservice/cosmos/cosmos-entity/SKILL.md`
- [X] T029 [P] [US1] Fix real-database factory construction and remove the EF InMemory lead example in `artifacts/skills/testing/integration-testing/SKILL.md`
- [X] T030 [P] [US1] Declare cancellation token usage in fixture samples in `artifacts/skills/testing/test-fixtures/SKILL.md`
- [X] T031 [P] [US1] Fix undeclared cancellation token and outbox typo guidance in `artifacts/skills/microservice/command/outbox/SKILL.md`
- [X] T032 [P] [US1] Replace async work in synchronous MudBlazor switch handlers with async-safe handlers in `artifacts/skills/microservice/controlpanel/mudblazor-patterns/SKILL.md`
- [X] T033 [US1] Remove false at-least-once and racy guard claims in `artifacts/knowledge/event-sourcing-flow.md`
- [X] T034 [P] [US1] Remove false at-least-once and racy guard claims in `artifacts/knowledge/outbox-pattern.md`
- [X] T035 [US1] Run `dotnet test dotnet-ai-kit.slnx --filter "FullyQualifiedName~ArtifactContentRepair"` for `tests/DotnetAiKit.Acceptance.Tests/ArtifactContentRepairTests.cs`

**Checkpoint**: All selected broken and localized serious artifact defects are repaired in authored source.

---

## Phase 4: User Story 2 - License-Safe Mediator Guidance Is Consistent (Priority: P1)

**Goal**: Remove Tier-A MediatR policy drift and route default CQRS dispatch through the license-safe abstraction policy.

**Independent Test**: Targeted policy tests reject Domain `: INotification` leaks and unqualified MediatR-as-default guidance in the Tier-A artifact set.

### Tests for User Story 2

- [X] T036 [P] [US2] Add Tier-A mediator policy guard tests in `tests/DotnetAiKit.Acceptance.Tests/MediatorPolicyRepairTests.cs`

### Implementation for User Story 2

- [X] T037 [US2] Abstract the root handler guidance away from unqualified MediatR defaults in `artifacts/skills/cqrs/mediatr-handlers/SKILL.md`
- [X] T038 [P] [US2] Remove Domain `IDomainEvent : INotification` guidance in `artifacts/skills/architecture/ddd-patterns/SKILL.md`
- [X] T039 [P] [US2] Remove Domain `IDomainEvent : INotification` guidance in `artifacts/skills/cqrs/notification-handlers/SKILL.md`
- [X] T040 [P] [US2] Reframe DI mediator registration as project-owned port or licensed opt-in in `artifacts/skills/core/dependency-injection/SKILL.md`
- [X] T041 [P] [US2] Reframe pattern examples away from unqualified MediatR defaults in `artifacts/skills/core/design-patterns/SKILL.md`
- [X] T042 [P] [US2] Add commercial-library caveats for mediator and mapper defaults in `artifacts/skills/core/solid-principles/SKILL.md`
- [X] T043 [P] [US2] Reframe transaction examples around mediator abstraction in `artifacts/skills/data/db-transactions/SKILL.md`
- [X] T044 [P] [US2] Update command generator guidance to use application-owned dispatch abstractions in `artifacts/skills/cqrs/command-generator/SKILL.md`
- [X] T045 [P] [US2] Fix MediatR behavior registration guidance and license framing in `artifacts/skills/cqrs/pipeline-behaviors/SKILL.md`
- [X] T046 [P] [US2] Update query generator guidance to use application-owned dispatch abstractions in `artifacts/skills/cqrs/query-generator/SKILL.md`
- [X] T047 [P] [US2] Update request/response guidance to make MediatR opt-in or abstracted in `artifacts/skills/cqrs/request-response/SKILL.md`
- [X] T048 [P] [US2] Reframe Clean Architecture use-case dispatch guidance in `artifacts/skills/architecture/clean-architecture/SKILL.md`
- [X] T049 [P] [US2] Reframe Modular Monolith integration-event dispatch guidance in `artifacts/skills/architecture/modular-monolith/SKILL.md`
- [X] T050 [P] [US2] Reframe Vertical Slice handler registration guidance in `artifacts/skills/architecture/vertical-slice/SKILL.md`
- [X] T051 [P] [US2] Reframe API caching invalidation examples away from unqualified MediatR defaults in `artifacts/skills/api/caching-strategies/SKILL.md`
- [X] T052 [P] [US2] Reframe controller dispatch guidance around the project-owned sender port in `artifacts/skills/api/controller-patterns/SKILL.md`
- [X] T053 [P] [US2] Reframe command handler guidance around domain command contracts and an app-owned sender port in `artifacts/skills/microservice/command/command-handler/SKILL.md`
- [X] T054 [P] [US2] Remove MediatR-as-default language from `artifacts/agents/ef-specialist.md`
- [X] T055 [P] [US2] Remove MediatR-as-default language from `artifacts/agents/processor-architect.md`
- [X] T056 [P] [US2] Update architecture rule detection wording to respect mediator abstraction in `artifacts/rules/domain/architecture.md`
- [X] T057 [US2] Reframe CQRS knowledge around mediator abstraction and existing-license policy in `artifacts/knowledge/cqrs-patterns.md`
- [X] T058 [US2] Reconcile mediator-abstraction wording with prior event-sourcing repairs in `artifacts/knowledge/event-sourcing-flow.md`
- [X] T059 [US2] Run `dotnet test dotnet-ai-kit.slnx --filter "FullyQualifiedName~MediatorPolicyRepair"` for `tests/DotnetAiKit.Acceptance.Tests/MediatorPolicyRepairTests.cs`

**Checkpoint**: Tier-A mediator policy drift is removed or redirected to the license-safe abstraction policy.

---

## Phase 5: User Story 3 - Cursor Plugin Delivery Is Structurally Valid (Priority: P1)

**Goal**: Generate a coherent Cursor plugin tree where every manifest-declared path resolves.

**Independent Test**: Cursor projection tests parse the generated manifest and assert each declared agent file exists under the plugin root.

### Tests for User Story 3

- [X] T060 [P] [US3] Add Cursor manifest reference-resolution tests in `tests/DotnetAiKit.Acceptance.Tests/CursorPluginDeliveryTests.cs`
- [X] T061 [P] [US3] Update golden projection expectations for Cursor plugin shape in `tests/DotnetAiKit.Hosts.Tests/GoldenProjectionTests.Full_projection_shape_is_byte_stable.verified.txt`

### Implementation for User Story 3

- [X] T062 [US3] Emit Cursor agent files and align manifest path/root handling in `src/DotnetAiKit.Hosts/Cursor/CursorProjector.cs`
- [X] T063 [US3] Run `dotnet test dotnet-ai-kit.slnx --filter "FullyQualifiedName~CursorPluginDelivery"` for `tests/DotnetAiKit.Acceptance.Tests/CursorPluginDeliveryTests.cs`

**Checkpoint**: Cursor generated output is structurally coherent and reference-checked.

---

## Phase 6: User Story 4 - Manifest Integrity Detects Tampering (Priority: P2)

**Goal**: Make `check` distinguish valid, missing, and tampered `.dotnet-ai-kit/manifest.json` states.

**Independent Test**: A valid initialized solution passes, missing manifest fails clearly, and a tampered manifest fails `manifest-integrity`.

### Tests for User Story 4

- [X] T064 [P] [US4] Add missing-manifest and tampered-manifest tests in `tests/DotnetAiKit.Acceptance.Tests/CheckContractTests.cs`
- [X] T065 [P] [US4] Add unit coverage for the manifest hash contract in `tests/DotnetAiKit.Application.Tests/CapabilityAndIntegrityTests.cs`

### Implementation for User Story 4

- [X] T066 [US4] Define the initialized footprint manifest hash contract in `src/DotnetAiKit.Hosts/Claude/ClaudeHostAdapter.cs`
- [X] T067 [US4] Verify actual manifest integrity from `CheckService` using the hash contract in `src/DotnetAiKit.Application/UseCases/CheckService.cs`
- [X] T068 [US4] Extend manifest hashing behavior if needed in `src/DotnetAiKit.Infrastructure/ManifestIntegrityService.cs`
- [X] T069 [US4] Run `dotnet test dotnet-ai-kit.slnx --filter "FullyQualifiedName~CheckContract|FullyQualifiedName~CapabilityAndIntegrity"` for `tests/DotnetAiKit.Acceptance.Tests/CheckContractTests.cs`

**Checkpoint**: Manifest integrity is a real tamper signal, not a presence check.

---

## Phase 7: User Story 5 - v1/Python Residue Is Removed From Touched Shipped Guidance (Priority: P2)

**Goal**: Ensure touched guidance describes the v2 .NET CLI as the active implementation and does not point users to removed v1 Python tooling.

**Independent Test**: Residue guard tests fail on `pip install`, nonexistent Python helper calls, `pytest`/`ruff` guidance in touched files, and stale `RuntimeMoniker.Net90`.

### Tests for User Story 5

- [X] T070 [P] [US5] Add v1/Python residue guards for touched artifacts in `tests/DotnetAiKit.Acceptance.Tests/V2ResidueRepairTests.cs`

### Implementation for User Story 5

- [X] T071 [P] [US5] Replace `pip install dotnet-ai-kit` guidance in `artifacts/skills/commands/init/SKILL.md`
- [X] T072 [P] [US5] Remove nonexistent Python `mcp_check` helper guidance in `artifacts/skills/commands/configure/SKILL.md`
- [X] T073 [P] [US5] Remove orphaned Python scaffold assumptions in `artifacts/skills/commands/constitution/SKILL.md`
- [X] T074 [P] [US5] Remove Python-tooling branches and stale command references in `artifacts/skills/workflow/git-worktree-isolation/SKILL.md`
- [X] T075 [P] [US5] Remove Python test-pattern section from the .NET rule guidance in `artifacts/rules/domain/testing.md`
- [X] T076 [P] [US5] Remove `ruff` verification residue in `artifacts/skills/workflow/verification-gate/SKILL.md`
- [X] T077 [P] [US5] Update stale runtime moniker guidance in `artifacts/skills/testing/performance-testing/SKILL.md`
- [X] T078 [US5] Run `dotnet test dotnet-ai-kit.slnx --filter "FullyQualifiedName~V2ResidueRepair"` for `tests/DotnetAiKit.Acceptance.Tests/V2ResidueRepairTests.cs`

**Checkpoint**: Touched shipped guidance no longer contradicts the v2 .NET CLI implementation.

---

## Phase 8: Projection, Review & Verification

**Purpose**: Replace the missing review command with explicit executable review tasks after implementation and before final polish.

- [X] T079 Run `dotnet run --project src/DotnetAiKit.Cli -- generate` and inspect generated paths in `build/`
- [X] T080 Review changed authored artifacts for correctness, scope, and policy consistency in `artifacts/`
- [X] T081 Review changed source and tests for deterministic, cross-platform behavior in `src/` and `tests/`
- [X] T082 Review generated output only as projection output, not source of truth, in `build/`
- [X] T083 Verify Cursor manifest references resolve in `build/cursor/.cursor-plugin/plugin.json`
- [X] T084 Verify manifest tampering coverage and error details in `tests/DotnetAiKit.Acceptance.Tests/CheckContractTests.cs`
- [X] T085 Run `dotnet build dotnet-ai-kit.slnx -warnaserror` for `dotnet-ai-kit.slnx`
- [X] T086 Run `dotnet test dotnet-ai-kit.slnx` for `tests/`
- [X] T087 Run `dotnet format dotnet-ai-kit.slnx --verify-no-changes` for `dotnet-ai-kit.slnx`
- [X] T088 Run `dotnet run --project src/DotnetAiKit.Cli -- generate --check` for `build/`

**Checkpoint**: Post-implementation review and all standing gates are complete.

---

## Phase 9: Polish

**Purpose**: Finish documentation and ensure the feature artifacts reflect the implemented state.

- [X] T089 Update deferred/fixed issue notes after implementation in `specs/023-v2-corpus-correctness-and-delivery-foundation/research.md`
- [X] T090 Update validation instructions if commands changed in `specs/023-v2-corpus-correctness-and-delivery-foundation/quickstart.md`
- [X] T091 Confirm every task is marked complete in `specs/023-v2-corpus-correctness-and-delivery-foundation/tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup.
- **User Stories (Phases 3-7)**: Depend on Foundational.
- **Projection, Review & Verification (Phase 8)**: Depends on selected user stories being complete.
- **Polish (Phase 9)**: Depends on Review & Verification.

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational; required before full projection review.
- **US2 (P1)**: Starts after Foundational; overlaps with US1 only on `artifacts/knowledge/event-sourcing-flow.md`, so that file must be handled sequentially.
- **US3 (P1)**: Starts after Foundational; independent from artifact text repairs.
- **US4 (P2)**: Starts after Foundational; independent from artifact text repairs but depends on check/init source understanding.
- **US5 (P2)**: Starts after Foundational; shares `artifacts/knowledge/testing-patterns.md` context with US1 and should run after T020.

### Within Each User Story

- Tests first, then authored/source changes, then targeted test command.
- For artifacts, edit only `artifacts/` source and regenerate `build/`.
- For same-file conflicts, complete the earlier phase task first and fold later policy wording into the same final file state.

---

## Parallel Opportunities

### User Story 1

Run T013-T034 in parallel by artifact file except T020/T033 sequencing where knowledge docs cross-reference one another.

### User Story 2

Run T038-T056 in parallel by file after T037 establishes the root wording, then complete T057-T058 sequentially for knowledge-doc consistency.

### User Story 3

Run T060 and T061 test/snapshot preparation independently, then apply T062 and run T063.

### User Story 4

Run T064 and T065 in parallel, then complete T066-T068 sequentially because they define one manifest-integrity contract.

### User Story 5

Run T071-T077 in parallel by artifact after T070 defines the guard expectations.

---

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational phases.
2. Complete US1 repairs and targeted artifact repair tests.
3. Complete US2 mediator-policy repairs.
4. Regenerate and run the standing gates before continuing to P2 stories if time is constrained.

### Incremental Delivery

1. Deliver artifact correctness and mediator policy first because they fix shipped user guidance.
2. Deliver Cursor projection and manifest-integrity behavior next because they fix install/check reliability.
3. Deliver v1/Python residue cleanup before final review so touched outputs are coherent.

### Review Discipline

Phase 8 is mandatory for this feature because `.claude/commands` has no review command. Treat it as the post-implementation review phase before final polish.
