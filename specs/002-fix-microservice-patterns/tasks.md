# Tasks: Fix Microservice Pattern Content

**Input**: Design documents from `/specs/002-fix-microservice-patterns/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md

**Tests**: No automated tests. Validation is manual comparison against production projects at `../projects/`.

**Organization**: Tasks grouped by user story (service type). All phases can run in parallel since they target different directories.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1=Command, US2=Query, US3=Processor, US4=Gateway)
- Include exact file paths in descriptions

## Path Conventions

- **Skills**: `skills/microservice/{service-type}/{skill-name}/SKILL.md`
- **Knowledge**: `knowledge/{name}.md`
- **Templates**: `templates/command/`
- **Source of truth**: `../projects/Anis.competition-commands`, `../projects/anis.competition-queries`, `../projects/anis.competition-processor`, `../projects/anis.gateways-cards-store-management`

## Phase 1: Setup

**Purpose**: No setup needed — all files already exist from feature 001. Each task reads the production project, then rewrites the corresponding file.

- [x] T001 Read all .cs files from ../projects/Anis.competition-commands to build a reference pattern index (aggregates, events, outbox, handlers, gRPC, DI containers)

---

## Phase 2: User Story 1 - Command-Side Patterns (Priority: P1) 🎯 MVP

**Goal**: All 6 command skills + 2 knowledge docs + command template match the exact patterns from `Anis.competition-commands`.

**Independent Test**: Compare each updated file's code examples against the production project. Class names, method signatures, inheritance hierarchy, and DI patterns must be structurally identical.

### Command Skills

- [x] T002 [P] [US1] Rewrite aggregate-design skill: fix Aggregate&lt;T&gt; base class to use abstract Event base (long Id, protected set), ApplyChange with sequence validation, Activator.CreateInstance in LoadFromHistory, MarkChangesAsCommitted. Source: ../projects/Anis.competition-commands/...Domain/Core/Aggregate.cs. Write to skills/microservice/command/aggregate-design/SKILL.md

- [x] T003 [P] [US1] Rewrite event-design skill: fix event hierarchy to abstract Event base → Event&lt;TData&gt; subclass with constructor, EventType enum (not string), IEventData with EventType Type property (JsonIgnored), concrete events using primary constructors. Source: ../projects/Anis.competition-commands/...Domain/Events/. Write to skills/microservice/command/event-design/SKILL.md

- [x] T004 [P] [US1] Rewrite event-store skill: fix EF config to GenericEventConfiguration&lt;TEntity,TData&gt; with Newtonsoft.Json Data conversion, discriminator using EventType enum, OutboxMessageConfiguration with Event FK. Source: ../projects/Anis.competition-commands/...Infra/Persistence/Configurations/. Write to skills/microservice/command/event-store/SKILL.md

- [x] T005 [P] [US1] Rewrite outbox skill: fix OutboxMessage (wraps Event via FK, static ToManyMessages factory), CommitEventService (IUnitOfWork.Events.AddRangeAsync + OutboxMessages.AddRangeAsync + SaveChangesAsync + StartPublish), ServiceBusPublisher (lock + lockedScopes + Task.Run + CreateScope + batch-200 + MessageBody + Newtonsoft.Json + full ServiceBusMessage properties). Source: ../projects/Anis.competition-commands/...Infra/. Write to skills/microservice/command/outbox/SKILL.md

- [x] T006 [P] [US1] Rewrite command-handler skill: fix handler pattern to use ICommitEventService.CommitNewEventsAsync(aggregate), IUnitOfWork for event history lookup, proper command records with IRequest. Source: ../projects/Anis.competition-commands/...Application/Features/Commands/. Write to skills/microservice/command/command-handler/SKILL.md

- [x] T007 [P] [US1] Rewrite aggregate-testing skill: align test patterns with correct aggregate (Aggregate&lt;T&gt;), event (abstract Event base + Event&lt;TData&gt;), and outbox (Event FK) structure. Write to skills/microservice/command/aggregate-testing/SKILL.md

### Command Knowledge Docs

- [x] T008 [P] [US1] Rewrite event-sourcing-flow knowledge doc: fix entire flow to match production — Aggregate.ApplyChange → UncommittedEvents → CommitEventService with IUnitOfWork (AddRangeAsync events + outbox) → SaveChangesAsync → StartPublish → ServiceBusPublisher (lock + scope + batch-200 + publish-and-remove). Source: ../projects/Anis.competition-commands. Write to knowledge/event-sourcing-flow.md

- [x] T009 [P] [US1] Rewrite outbox-pattern knowledge doc: fix OutboxMessage (Event FK, ToManyMessages), CommitEventService (IUnitOfWork pattern), ServiceBusPublisher (full production implementation with lock, lockedScopes, Task.Run, CreateScope, MessageBody, Newtonsoft.Json, ServiceBusMessage properties). Source: ../projects/Anis.competition-commands/...Infra/. Write to knowledge/outbox-pattern.md

### Command Template

- [x] T010 [depends: T003, T005] [US1] Fix command template: rename DI classes to ApplicationContainer/InfraContainer, fix Event hierarchy (abstract Event base + Event&lt;TData&gt;), fix OutboxMessage (Event FK), fix CommitEventService and ServiceBusPublisher patterns. Update all affected files in templates/command/

**Checkpoint**: All command-side content matches production project patterns.

---

## Phase 3: User Story 2 - Query-Side Patterns (Priority: P2)

**Goal**: All 5 query skills match the exact patterns from `anis.competition-queries`.

**Independent Test**: Compare each updated file's code examples against the production project.

- [x] T011 [P] [US2] Rewrite query-entity skill: fix entity pattern to event-based constructors accepting Event&lt;TData&gt;, behavior methods with (TData data, int sequence) signature, private set on all properties, Sequence tracking. Source: ../projects/anis.competition-queries/...Domain/Entities/. Write to skills/microservice/query/query-entity/SKILL.md

- [x] T012 [P] [US2] Rewrite event-handler skill: fix return type to IRequestHandler&lt;Event&lt;T&gt;, bool&gt;, show idempotent duplicate handling (return true), sequence checking before processing. Source: ../projects/anis.competition-queries/...Application/Features/Events/. Write to skills/microservice/query/event-handler/SKILL.md

- [x] T013 [P] [US2] Rewrite query-handler skill: align with IUnitOfWork lazy-loaded repository pattern, show proper query with filtering and pagination. Source: ../projects/anis.competition-queries. Write to skills/microservice/query/query-handler/SKILL.md

- [x] T014 [P] [US2] Rewrite sequence-checking skill: fix to show exact pattern `if (entity.Sequence >= @event.Sequence) return true;` as idempotency guard, explain why returning true (CompleteMessage in listener). Source: ../projects/anis.competition-queries. Write to skills/microservice/query/sequence-checking/SKILL.md

- [x] T015 [P] [US2] Rewrite listener-pattern skill: fix ServiceBusSessionProcessor config (PrefetchCount=1, MaxConcurrentCallsPerSession=1, MaxConcurrentSessions=1000, SessionIdleTimeout=1min, MaxAutoLockRenewalDuration=5min, AutoCompleteMessages=false), add paired DLQ processor. Source: ../projects/anis.competition-queries. Write to skills/microservice/query/listener-pattern/SKILL.md

**Checkpoint**: All query-side content matches production project patterns.

---

## Phase 4: User Story 3 - Processor Patterns (Priority: P2)

**Goal**: All 4 processor skills + 2 knowledge docs match the exact patterns from `anis.competition-processor`.

**Independent Test**: Compare each updated file's code examples against the production project.

### Processor Skills

- [x] T016 [P] [US3] Rewrite hosted-service skill: fix to ServiceBusSessionProcessor with exact config options, show paired DLQ processor creation, show ProcessMessageAsync + ProcessErrorAsync handler setup. Source: ../projects/anis.competition-processor/...Infra/ServiceBus/Listeners/. Write to skills/microservice/processor/hosted-service/SKILL.md

- [x] T017 [P] [US3] Rewrite event-routing skill: fix to subject-based switch statement dispatching to typed HandleAsync&lt;T&gt;() methods, show JSON deserialization to Event&lt;T&gt;, IMediator.Send(), CompleteMessage/AbandonMessage pattern. Source: ../projects/anis.competition-processor. Write to skills/microservice/processor/event-routing/SKILL.md

- [x] T018 [P] [US3] Rewrite batch-processing skill: fix to separate BackgroundService with AcceptNextSessionAsync, semaphore-based concurrent session limiting, ReceiveMessagesAsync with batch size, GroupBy deduplication, BatchRequest handler pattern. Source: ../projects/anis.competition-processor/...Listeners/PointsQueueListener.cs. Write to skills/microservice/processor/batch-processing/SKILL.md

- [x] T019 [P] [US3] Rewrite grpc-client skill: fix to AddGrpcClient&lt;T&gt; with IOptions&lt;ExternalServicesOptions&gt; pattern, RegisterUrl helper method, show RetryCallerService wrapper. Source: ../projects/anis.competition-processor/...Setup/ExternalServicesRegistrationExtensions.cs. Write to skills/microservice/processor/grpc-client/SKILL.md

### Processor Knowledge Docs

- [x] T020 [P] [US3] Rewrite service-bus-patterns knowledge doc: fix SessionProcessor configuration section, add paired DLQ processor pattern, fix subject-based routing, add batch processing section. Source: ../projects/anis.competition-processor. Write to knowledge/service-bus-patterns.md

- [x] T021 [P] [US3] Rewrite dead-letter-reprocessing knowledge doc: fix to paired processor pattern (main SessionProcessor + separate DLQ Processor per listener), show SubQueue.DeadLetter config, show CompleteMessage/AbandonMessage semantics. Source: ../projects/anis.competition-processor. Write to knowledge/dead-letter-reprocessing.md

**Checkpoint**: All processor content matches production project patterns.

---

## Phase 5: User Story 4 - Gateway Patterns (Priority: P3)

**Goal**: All 4 gateway skills match the exact patterns from `anis.gateways-cards-store-management`.

**Independent Test**: Compare each updated file's code examples against the production project.

- [x] T022 [P] [US4] Rewrite gateway-endpoint skill: fix controller pattern to show gRPC client delegation, proper request/response mapping extensions, ServerCallContext usage. Source: ../projects/anis.gateways-cards-store-management. Write to skills/microservice/gateway/gateway-endpoint/SKILL.md

- [x] T023 [P] [US4] Rewrite endpoint-registration skill: fix to AddGrpcClient&lt;T&gt; with RegisterUrl helper method, IOptions&lt;ExternalServicesOptions&gt; binding, ServicesURLsOptions pattern. Source: ../projects/anis.gateways-cards-store-management. Write to skills/microservice/gateway/endpoint-registration/SKILL.md

- [x] T024 [P] [US4] Rewrite gateway-security skill: fix to AddPolicies(ApiScope.Management) pattern, AddJwtAuthentication from configuration, show policy-based [Authorize] on controllers. Source: ../projects/anis.gateways-cards-store-management. Write to skills/microservice/gateway/gateway-security/SKILL.md

- [x] T025 [P] [US4] Rewrite scalar-docs skill: fix to AddOpenApiDocumentation pattern from production, show Scalar UI configuration, environment-aware setup. Source: ../projects/anis.gateways-cards-store-management. Write to skills/microservice/gateway/scalar-docs/SKILL.md

**Checkpoint**: All gateway content matches production project patterns.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verify consistency across all updated files.

- [x] T026 Validate all 19 updated skill files are ≤400 lines
- [x] T027 [P] Verify cross-references: patterns described in command skills match patterns in knowledge docs and template
- [x] T028 [P] Verify all updated files use {Company}/{Domain} placeholders — no production-specific domain names (competition, accounts)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Read production projects — can start immediately
- **US1 Command (Phase 2)**: Can start after T001 — highest priority
- **US2 Query (Phase 3)**: Can start after T001 — independent of US1
- **US3 Processor (Phase 4)**: Can start after T001 — independent of US1/US2
- **US4 Gateway (Phase 5)**: Can start after T001 — independent of all others
- **Polish (Phase 6)**: Depends on all previous phases

### Parallel Opportunities

- ALL user story phases (2-5) can run in parallel — different directories, zero file conflicts
- ALL tasks within each phase are marked [P] — different files
- Only T001 (read production) and T010 (template fix) are sequential within their phase

---

## Implementation Strategy

### MVP First (User Story 1 — Command Side)

1. Complete T001: Read production command project
2. Complete T002-T010: Fix all command-side content
3. **STOP and VALIDATE**: Compare against production code
4. Proceed to query, processor, gateway in parallel

### Full Parallel Execution

After T001 completes, launch 4 parallel teams:
- Team A: T002-T010 (command skills + knowledge + template)
- Team B: T011-T015 (query skills)
- Team C: T016-T021 (processor skills + knowledge)
- Team D: T022-T025 (gateway skills)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps to service type: US1=Command, US2=Query, US3=Processor, US4=Gateway
- Source of truth: ../projects/ production code, NOT planning documents
- Each skill rewrite must READ the production project FIRST, then write the skill
- CRITICAL: Use {Company}/{Domain} placeholders — generic entity names (Order, Product), not competition/accounts. Replace all production-specific names (Anis, Competition, Account) with placeholders before writing
- Every task agent MUST verify no production domain names leak into output before completing
- Preserve YAML frontmatter (name, description, category, agent) in each skill file
- Task phases (1-6) are organized by user story; plan phases (1-4) are organized by service type — numbering differs intentionally
