# Data Model: Fix Microservice Pattern Content

## Overview

This feature updates existing files — no new entities are created. The
"data model" here is the inventory of files to update and the specific
pattern corrections for each.

## File Inventory

### Command Skills (6 files)

| File | Key Correction |
|------|---------------|
| `skills/microservice/command/aggregate-design/SKILL.md` | Fix Aggregate<T> base: abstract Event base, long Id, sequence validation, Activator.CreateInstance in LoadFromHistory |
| `skills/microservice/command/event-design/SKILL.md` | Fix event hierarchy: abstract Event → Event<TData>, EventType enum, IEventData.Type property |
| `skills/microservice/command/event-store/SKILL.md` | Fix EF config: GenericEventConfiguration<TEntity,TData>, Newtonsoft.Json conversion, discriminator with EventType enum |
| `skills/microservice/command/outbox/SKILL.md` | Fix OutboxMessage (Event FK, ToManyMessages), CommitEventService (IUnitOfWork), ServiceBusPublisher (lock+scope+batch) |
| `skills/microservice/command/command-handler/SKILL.md` | Fix handler: ICommitEventService.CommitNewEventsAsync(aggregate), not manual event extraction |
| `skills/microservice/command/aggregate-testing/SKILL.md` | Align test patterns with correct aggregate/event structure |

### Query Skills (5 files)

| File | Key Correction |
|------|---------------|
| `skills/microservice/query/query-entity/SKILL.md` | Fix entity: event-based constructor, behavior methods with (TData, sequence), Sequence tracking |
| `skills/microservice/query/event-handler/SKILL.md` | Fix return type: IRequestHandler<Event<T>, bool>, idempotent true/false |
| `skills/microservice/query/query-handler/SKILL.md` | Align with IUnitOfWork repository pattern |
| `skills/microservice/query/sequence-checking/SKILL.md` | Fix: `if (entity.Sequence >= @event.Sequence) return true;` |
| `skills/microservice/query/listener-pattern/SKILL.md` | Fix: ServiceBusSessionProcessor config values, paired DLQ processor |

### Processor Skills (4 files)

| File | Key Correction |
|------|---------------|
| `skills/microservice/processor/hosted-service/SKILL.md` | Fix: ServiceBusSessionProcessor setup with exact config options |
| `skills/microservice/processor/event-routing/SKILL.md` | Fix: subject-based switch → HandleAsync<T> → deserialize → IMediator.Send |
| `skills/microservice/processor/batch-processing/SKILL.md` | Fix: separate BackgroundService, AcceptNextSessionAsync, semaphore, GroupBy dedup |
| `skills/microservice/processor/grpc-client/SKILL.md` | Fix: AddGrpcClient with IOptions<ExternalServicesOptions> pattern |

### Gateway Skills (4 files)

| File | Key Correction |
|------|---------------|
| `skills/microservice/gateway/gateway-endpoint/SKILL.md` | Fix: controller pattern with gRPC client delegation |
| `skills/microservice/gateway/endpoint-registration/SKILL.md` | Fix: AddGrpcClient with RegisterUrl helper, IOptions binding |
| `skills/microservice/gateway/gateway-security/SKILL.md` | Fix: AddPolicies(ApiScope), AddJwtAuthentication pattern |
| `skills/microservice/gateway/scalar-docs/SKILL.md` | Fix: AddOpenApiDocumentation pattern from production |

### Knowledge Documents (4 files)

| File | Key Correction |
|------|---------------|
| `knowledge/event-sourcing-flow.md` | Rewrite flow: aggregate → IUnitOfWork → SaveChanges → StartPublish → lock+scope+batch |
| `knowledge/outbox-pattern.md` | Rewrite: OutboxMessage FK, CommitEventService with IUnitOfWork, ServiceBusPublisher full impl |
| `knowledge/service-bus-patterns.md` | Fix: SessionProcessor config, paired DLQ processors, subject-based routing |
| `knowledge/dead-letter-reprocessing.md` | Fix: paired processor pattern from production |

### Template (1 directory)

| File | Key Correction |
|------|---------------|
| `templates/command/` | Fix DI class names (ApplicationContainer, InfraContainer), event hierarchy, outbox pattern |

## Relationships

```
Command skills ──defines──→ Event hierarchy used by Query/Processor skills
Knowledge docs ──describes──→ Same patterns as Command/Query/Processor skills
Template ──scaffolds──→ Code matching Command skill patterns
```

All corrections must be consistent — the same pattern described in a
command skill must appear identically in the knowledge doc and template.
