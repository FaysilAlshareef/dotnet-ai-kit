# Implementation Plan: Fix Microservice Pattern Content

**Branch**: `002-fix-microservice-patterns` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-fix-microservice-patterns/spec.md`

## Summary

Update 24 files (19 skills + 4 knowledge docs + 1 template) so that all
microservice code examples and patterns match the real production projects
at `../projects/`. The production code is the definitive source of truth.
This is a content-correction pass — no new files are created, only
existing files are rewritten with accurate patterns.

## Technical Context

**Language/Version**: Markdown files containing C# code examples targeting .NET 8/9/10
**Primary Dependencies**: N/A (content files only, no runtime dependencies)
**Storage**: File-based (markdown files in skills/, knowledge/, templates/)
**Testing**: Manual comparison against production project source code
**Target Platform**: N/A (content consumed by AI coding assistants)
**Project Type**: Content correction / knowledge base update
**Performance Goals**: N/A
**Constraints**: Skills ≤400 lines; {Company}/{Domain} placeholders required; no production-specific domain names
**Scale/Scope**: 24 files to update across 4 service types

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Detect-First, Respect-Existing | PASS | Skills teach this principle; fix ensures code examples demonstrate correct detection patterns |
| II. Pattern Fidelity | PASS | This fix IS about pattern fidelity — aligning generated patterns with real production code |
| III. Architecture & Platform Agnostic | PASS | Skills cover all microservice types; {Company}/{Domain} placeholders maintained |
| IV. Best Practices & Quality | PASS | Production patterns ARE the best practices for this codebase |
| V. Safety & Token Discipline | PASS | 400-line skill budget enforced; no safety changes |

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/002-fix-microservice-patterns/
├── plan.md              # This file
├── research.md          # Production pattern analysis
├── data-model.md        # File inventory and change mapping
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Files to Update (repository root)

```text
skills/microservice/command/       # 6 skills (P1 - highest priority)
├── aggregate-design/SKILL.md
├── event-design/SKILL.md
├── event-store/SKILL.md
├── outbox/SKILL.md
├── command-handler/SKILL.md
└── aggregate-testing/SKILL.md

skills/microservice/query/         # 5 skills (P2)
├── query-entity/SKILL.md
├── event-handler/SKILL.md
├── query-handler/SKILL.md
├── sequence-checking/SKILL.md
└── listener-pattern/SKILL.md

skills/microservice/processor/     # 4 skills (P2)
├── hosted-service/SKILL.md
├── event-routing/SKILL.md
├── batch-processing/SKILL.md
└── grpc-client/SKILL.md

skills/microservice/gateway/       # 4 skills (P3)
├── gateway-endpoint/SKILL.md
├── endpoint-registration/SKILL.md
├── gateway-security/SKILL.md
└── scalar-docs/SKILL.md

knowledge/                         # 4 knowledge docs (P1-P3)
├── event-sourcing-flow.md         # P1
├── outbox-pattern.md              # P1
├── service-bus-patterns.md        # P2
└── dead-letter-reprocessing.md    # P2

templates/command/                 # 1 template (P1)
└── (multiple scaffold files)
```

**Structure Decision**: No new directories — all changes are updates to
existing files created in feature 001.

## Source of Truth Mapping

Each output file maps to a specific production project for pattern accuracy:

| Service Type | Production Project | Files Affected |
|-------------|-------------------|---------------|
| Command | `../projects/Anis.competition-commands` | 6 skills + 2 knowledge + 1 template |
| Query | `../projects/anis.competition-queries` | 5 skills |
| Processor | `../projects/anis.competition-processor` | 4 skills + 2 knowledge |
| Gateway | `../projects/anis.gateways-cards-store-management` | 4 skills |

## Key Pattern Corrections (from research)

### Command Side (6 critical fixes)

1. **Event hierarchy**: Abstract `Event` base (long Id, protected set) → `Event<TData>` subclass with constructor, `EventType` enum not string
2. **IEventData**: Has `EventType Type` property (JsonIgnored), not just marker
3. **OutboxMessage**: Wraps `Event` via FK, not duplicated fields; static `ToManyMessages()` factory
4. **CommitEventService**: Uses `IUnitOfWork` (AddRangeAsync events + outbox → SaveChangesAsync → StartPublish), NOT manual BeginTransactionAsync
5. **ServiceBusPublisher**: lock + lockedScopes + Task.Run + CreateScope + batch-200 + MessageBody + Newtonsoft.Json + full ServiceBusMessage properties
6. **DI containers**: `ApplicationContainer` / `InfraContainer`, not `*Extensions`

### Query Side (4 fixes)

7. **Entities**: Event-based constructors, behavior methods with `(TData data, int sequence)`, Sequence tracking
8. **Event handlers**: `IRequestHandler<Event<T>, bool>` — returns bool
9. **Sequence checking**: `if (entity.Sequence >= @event.Sequence) return true;`
10. **UnitOfWork**: Lazy-loaded repositories pattern

### Processor (4 fixes)

11. **Listeners**: `ServiceBusSessionProcessor` with specific config (PrefetchCount=1, MaxConcurrentSessions=1000, etc.) + paired DLQ processor
12. **Event routing**: Subject-based switch → HandleAsync<T>() → deserialize → IMediator.Send()
13. **Batch processing**: Separate BackgroundService, AcceptNextSessionAsync, semaphore, deduplication
14. **DLQ handling**: Every listener has paired DLQ processor with SubQueue.DeadLetter

### Gateway (3 fixes)

15. **Rate limiting**: AddPentagon() pattern
16. **Authorization**: AddPolicies(ApiScope) pattern
17. **gRPC clients**: IOptions<ExternalServicesOptions> with RegisterUrl helper

## Implementation Phases

| Phase | Focus | Files | Priority |
|-------|-------|-------|----------|
| 1 | Command skills + knowledge + template | 6 + 2 + 1 = 9 | P1 |
| 2 | Query skills | 5 | P2 |
| 3 | Processor skills + knowledge | 4 + 2 = 6 | P2 |
| 4 | Gateway skills | 4 | P3 |

### Parallel Opportunities

- Phase 1-4 can all run in parallel (different directories, no file conflicts)
- Within each phase, all skill files are independent

## Post-Design Constitution Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Detect-First | PASS | Skills teach correct detection patterns from production |
| II. Pattern Fidelity | PASS | This fix achieves pattern fidelity by definition |
| III. Agnostic | PASS | {Company}/{Domain} placeholders maintained |
| IV. Quality | PASS | Production patterns = proven quality |
| V. Safety & Token | PASS | 400-line budget enforced |
