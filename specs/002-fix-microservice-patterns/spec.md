# Feature Specification: Fix Microservice Pattern Content to Match Production Projects

**Feature Branch**: `002-fix-microservice-patterns`
**Created**: 2026-03-16
**Status**: Draft
**Input**: User description: "Fix all microservice skill, knowledge doc, agent, and template content to match real production project patterns from ../projects/"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Command-Side Patterns Match Real Projects (Priority: P1)

A developer using dotnet-ai-kit to generate command-side microservice code
gets output that matches the exact patterns used in the production
`Anis.competition-commands` project: correct aggregate base class, event
hierarchy with abstract Event base + Event&lt;TData&gt; subclass, outbox with
Event FK reference, CommitEventService using IUnitOfWork, ServiceBusPublisher
with lock+scope+batch pattern, and correct DI container class names.

**Why this priority**: The command side defines the event structure that all
other services consume. If command-side patterns are wrong, every downstream
service (query, processor, gateway) generates incorrect code.

**Independent Test**: Compare the generated skill code examples, knowledge
doc patterns, and template files against the real
`Anis.competition-commands` project. Every code snippet MUST be
structurally identical to the production code.

**Acceptance Scenarios**:

1. **Given** the aggregate-design skill, **When** a developer reads it,
   **Then** the code example shows `Aggregate<T>` with abstract `Event`
   base class (long Id, protected set), `ApplyChange` with sequence
   validation (`if (@event.Sequence != Sequence) throw`), and
   `Activator.CreateInstance` in `LoadFromHistory`.

2. **Given** the outbox skill, **When** a developer reads it, **Then** the
   code shows `OutboxMessage` wrapping `Event` via FK relationship (not
   duplicating event fields), with static `ToManyMessages()` factory, and
   `CommitEventService` using `IUnitOfWork.Events.AddRangeAsync()` +
   `IUnitOfWork.OutboxMessages.AddRangeAsync()` + `SaveChangesAsync()` +
   `_serviceBusPublisher.StartPublish()`.

3. **Given** the event-design skill, **When** a developer reads it,
   **Then** the code shows abstract `Event` base with `long Id`,
   `EventType` enum (not string), `IEventData` with `EventType Type`
   property (JsonIgnored), and concrete events using primary constructors
   inheriting from `Event<TData>`.

4. **Given** the ServiceBusPublisher pattern in knowledge docs, **When** a
   developer reads it, **Then** it shows `lock(_lockObject)` +
   `lockedScopes` counter, `Task.Run(PublishNonPublishedMessages)`,
   `_serviceProvider.CreateScope()`, batch-read outbox (200), publish and
   remove one-by-one, `MessageBody` with Newtonsoft.Json, and full
   `ServiceBusMessage` properties (SessionId, PartitionKey, Subject,
   CorrelationId, MessageId, ApplicationProperties).

5. **Given** the command template, **When** a developer scaffolds a new
   command project, **Then** the DI containers are named
   `ApplicationContainer` and `InfraContainer` (not
   `ApplicationServiceExtensions` / `InfraServiceExtensions`).

---

### User Story 2 - Query-Side Patterns Match Real Projects (Priority: P2)

A developer using dotnet-ai-kit to generate query-side microservice code
gets output that matches the production `anis.competition-queries` project:
entities with event-based constructors and behavior methods, event handlers
returning `bool` for idempotency, explicit sequence checking, and IUnitOfWork
with lazy-loaded repositories.

**Why this priority**: Query-side is the second most common service type
and consumes events from the command side. Incorrect patterns break the
event flow.

**Independent Test**: Compare query skill code examples against the real
`anis.competition-queries` project.

**Acceptance Scenarios**:

1. **Given** the query-entity skill, **When** a developer reads it,
   **Then** entities show event-based constructors accepting
   `Event<TData>`, behavior methods with `(TData data, int sequence)`
   signature, `private set` on all properties, and `Sequence` tracking.

2. **Given** the event-handler skill, **When** a developer reads it,
   **Then** handlers implement `IRequestHandler<Event<T>, bool>` (not
   `IRequestHandler<Event<T>>`), return `true` for success and
   idempotent duplicate processing.

3. **Given** the sequence-checking skill, **When** a developer reads it,
   **Then** the pattern shows `if (entity.Sequence >= @event.Sequence)
   return true;` for idempotency guard.

---

### User Story 3 - Processor Patterns Match Real Projects (Priority: P2)

A developer using dotnet-ai-kit to generate processor microservice code
gets output matching the production `anis.competition-processor` project:
ServiceBusSessionProcessor listeners with specific configuration options,
subject-based switch routing, paired DLQ processors, batch processing with
BackgroundService and deduplication.

**Why this priority**: Processors handle complex event routing and batch
processing. Incorrect listener patterns cause message loss or duplication.

**Independent Test**: Compare processor skill code examples against the real
`anis.competition-processor` project.

**Acceptance Scenarios**:

1. **Given** the listener-pattern skill, **When** a developer reads it,
   **Then** it shows `ServiceBusSessionProcessor` with PrefetchCount=1,
   MaxConcurrentCallsPerSession=1, MaxConcurrentSessions=1000,
   SessionIdleTimeout=1min, MaxAutoLockRenewalDuration=5min,
   AutoCompleteMessages=false.

2. **Given** the event-routing skill, **When** a developer reads it,
   **Then** routing uses subject-based `switch` statement dispatching to
   typed `HandleAsync<T>()` methods that deserialize JSON to `Event<T>`
   and send via `IMediator.Send()`.

3. **Given** the batch-processing skill, **When** a developer reads it,
   **Then** it shows a separate `BackgroundService` (not SessionProcessor)
   with `AcceptNextSessionAsync()`, semaphore-based concurrent session
   limiting, batch receive, GroupBy deduplication, and batch handler.

4. **Given** any listener skill, **When** a developer reads it, **Then**
   every listener has a paired DLQ processor created with
   `SubQueue.DeadLetter` and `ServiceBusProcessorOptions`.

---

### User Story 4 - Gateway & Knowledge Docs Match Real Projects (Priority: P3)

A developer using dotnet-ai-kit gets gateway patterns matching the real
`anis.gateways-cards-store-management` project, and knowledge docs that
accurately describe the production event sourcing, outbox, and service bus
flows.

**Why this priority**: Gateway and knowledge doc fixes are important for
accuracy but have lower blast radius since gateways are the simplest
service type and knowledge docs are reference material.

**Independent Test**: Compare gateway skills and knowledge docs against
real projects.

**Acceptance Scenarios**:

1. **Given** the gateway skills, **When** a developer reads them, **Then**
   they show `AddPentagon()` for rate limiting, `AddPolicies(ApiScope)`
   for authorization, shared common project pattern, and correct gRPC
   client registration with `IOptions<ExternalServicesOptions>`.

2. **Given** the event-sourcing-flow knowledge doc, **When** a developer
   reads it, **Then** it describes the real flow: Aggregate.ApplyChange()
   → Event added to UncommittedEvents → CommitEventService calls
   UnitOfWork to save Events + OutboxMessages in single SaveChanges →
   StartPublish fires Task.Run → ServiceBusPublisher creates scope, reads
   outbox batch, publishes + removes one-by-one.

3. **Given** the outbox-pattern knowledge doc, **When** a developer reads
   it, **Then** it shows the real OutboxMessage entity (wraps Event via
   FK, not duplicated fields), the real CommitEventService (IUnitOfWork,
   not manual transactions), and the real ServiceBusPublisher (lock +
   scope + batch + fire-and-forget).

---

### Edge Cases

- What happens when the fix changes a code example that a command file
  references? The command file's description of the pattern must remain
  consistent with the updated skill content. Verify all cross-references.

- What happens when a production project uses a pattern that differs from
  the planning docs? Production code takes precedence over planning docs
  for pattern accuracy. Planning docs describe the intent; production
  projects show the actual implementation.

- What happens when the real project has domain-specific code (competition,
  accounts) that shouldn't be in generic skills? Skills must use
  `{Company}`, `{Domain}` placeholders and generic entity names (Order,
  Product) while preserving the structural pattern from production code.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All 6 command-side skills MUST have code examples matching
  the exact class hierarchy, method signatures, and patterns from
  `Anis.competition-commands`.

- **FR-002**: All 5 query-side skills MUST have code examples matching the
  entity pattern, handler return type (`bool`), and sequence checking from
  `anis.competition-queries`.

- **FR-003**: All 4 processor skills MUST have code examples matching the
  ServiceBusSessionProcessor configuration, subject-based routing, paired
  DLQ pattern, and batch processing from `anis.competition-processor`.

- **FR-004**: All 4 gateway skills MUST have code examples matching the
  Pentagon rate limiting, ApiScope policies, and gRPC client registration
  from `anis.gateways-cards-store-management`.

- **FR-005**: The event-sourcing-flow and outbox-pattern knowledge docs
  MUST accurately describe the production flow using IUnitOfWork, not
  manual transaction management.

- **FR-006**: The service-bus-patterns knowledge doc MUST show the real
  ServiceBusSessionProcessor configuration and DLQ paired processor
  pattern from production.

- **FR-007**: The dead-letter-reprocessing knowledge doc MUST show the
  paired processor pattern (main SessionProcessor + DLQ Processor per
  listener) from production.

- **FR-008**: The command template (`templates/command/`) MUST use
  `ApplicationContainer` and `InfraContainer` as DI registration class
  names, and scaffold the correct Event hierarchy (abstract Event base +
  Event&lt;TData&gt;).

- **FR-009**: All updated content MUST continue to use `{Company}`,
  `{Domain}` placeholders and generic entity names — no production domain
  specifics (competition, accounts) in skills or templates.

- **FR-010**: All updated skill files MUST remain within the 400-line
  budget. All updated knowledge docs have no line limit but must be
  focused and practical.

### Key Entities

- **Skill File**: A code pattern file (max 400 lines) in `skills/` with
  YAML frontmatter. 19 skill files affected (6 command, 5 query, 4
  processor, 4 gateway).

- **Knowledge Document**: A reference document in `knowledge/`. 4
  knowledge docs affected (event-sourcing-flow, outbox-pattern,
  service-bus-patterns, dead-letter-reprocessing).

- **Template**: A project scaffold in `templates/`. 1 template affected
  (command template).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of command-side skill code examples are structurally
  identical to `Anis.competition-commands` patterns (same class names,
  same method signatures, same inheritance hierarchy).

- **SC-002**: 100% of query-side skill code examples match
  `anis.competition-queries` patterns (event-based constructors, bool
  return type, sequence checking).

- **SC-003**: 100% of processor skill code examples match
  `anis.competition-processor` patterns (SessionProcessor config,
  subject-based routing, paired DLQ, batch processing).

- **SC-004**: All 4 affected knowledge docs accurately describe the
  production flow — a developer reading them would produce code matching
  the real projects.

- **SC-005**: The command template scaffolds a project structurally
  matching `Anis.competition-commands` (correct DI names, event
  hierarchy, outbox pattern).

- **SC-006**: All updated files remain within their token budgets (skills
  ≤400 lines).

- **SC-007**: Zero cross-reference inconsistencies between updated skills,
  knowledge docs, and command files that reference them.
