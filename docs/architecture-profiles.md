# Architecture Profiles Reference

dotnet-ai-kit ships 12 architecture profiles. After `/dai.detect` identifies
your project type, the matching profile is deployed to your AI tool's rules
directory and remains active for every session — the AI behaves as a specialist
in your exact pattern without being told every time.

---

## How profiles work

```bash
# Run AI-powered detection
/dai.detect

# Or pass the type directly at init
dotnet-ai init . --ai claude --type command
```

Detection writes the profile to `.dotnet-ai-kit/project.yml :: project_type`.
A PreToolUse hook reads `project.yml` at every Write/Edit and enforces
the active profile before any code is written — violations are caught
before they land in the file, not in code review.

Only **one profile** is active per project at a time.

---

## Microservice profiles (7)

For event-driven CQRS microservice architectures. See
[docs/multi-repo-cqrs.md](multi-repo-cqrs.md) for the full multi-repo setup.

---

### `command` — Event-Sourced Write Side

Use for the service that owns domain aggregates and publishes events.

**Key pattern**: Aggregate → Event → Outbox → Service Bus

| Constraint | Rule |
|-----------|------|
| Aggregate creation | Static factory methods only (`Order.Create(cmd)`) — never `new Order()` in handlers |
| Aggregate rebuild | `LoadFromHistory(events)` — never construct manually |
| Aggregate state | Private setters only |
| Event routing | Dynamic dispatch `((dynamic)this).Apply(@event)` — never switch statements |
| Business logic | Inside the aggregate — never in handlers |
| Event schemas | Immutable once published — never remove/rename fields |
| Event records | Immutable `record` types only — never mutable classes |
| Atomicity | Save events + outbox in one `SaveChangesAsync` call — never publish before DB save |
| Outbox call | `CommitNewEventsAsync(aggregate)` — never pass the events list directly |
| Publisher | `ServiceBusPublisher` as singleton; `StartPublish()` fire-and-forget |
| Data access | `IUnitOfWork` only — never inject `ApplicationDbContext` directly |
| Event store | TPH with single `Events` table and discriminator; unique index on `(AggregateId, Sequence)` |
| Serialization | Newtonsoft.Json for `Data` column — never System.Text.Json |

**Anti-patterns**: returning aggregates from handlers, creating transactions in handlers,
loading multiple aggregates in one handler, using `new Aggregate()` anywhere outside a factory.

---

### `query-sql` — SQL Server Read Side

Use for the service that projects events into SQL Server read models.

**Key pattern**: Event → Sequence guard → Entity update → `SaveChangesAsync`

| Constraint | Rule |
|-----------|------|
| Entity properties | `{ get; private set; }` everywhere — never public setters |
| Sequence field | Every entity has `int Sequence { get; private set; }` |
| EF Core constructor | Private constructor with ALL parameters — never parameterless |
| Handler return type | `bool` — `true` = CompleteMessage, `false` = AbandonMessage |
| Idempotency | Never throw in handlers — return `false` for retry |
| Duplicate events | Return `true` (creation) or follow sequence guard (update) |

**The only correct sequence guard** (exact pattern, no variations):

```csharp
if (entity.Sequence != @event.Sequence - 1)
    return entity.Sequence >= @event.Sequence;
```

| Scenario | Return |
|----------|--------|
| Entity already at or ahead of this sequence | `true` (complete — duplicate) |
| Gap in sequence (event arrived early) | `false` (abandon — retry later) |
| Entity missing on update | `false` (abandon) |

**Anti-patterns**: sequence guard helper classes, returning void from handlers,
throwing exceptions in handlers, referencing command-side aggregate classes.

---

### `query-cosmos` — Cosmos DB Read Side

Use for the service that projects events into Cosmos DB containers.

| Constraint | Rule |
|-----------|------|
| Document interface | Implement `IContainerDocument` on every entity |
| ID property | Lowercase `id` — Cosmos requires it |
| Discriminator | Property returning `nameof(ClassName)` — required for polymorphic queries |
| ETag | `ETag` property on every entity — never skip concurrency |
| Partition keys | `PartitionKeyBuilder` (up to 3 levels); never use entity Id as sole key |
| Point reads | Use `ReadItemAsync` when id + partition key are known — never query |
| Batch limit | Max 100 operations per `TransactionalBatch` |
| Batch constraint | All batch operations must share the same partition key |
| ETag on write | Pass `IfMatchEtag` on replace/upsert — never skip |
| Pagination | `FeedIterator` with `MaxItemCount` — never unbounded queries |
| RU logging | Log `RequestCharge` from every response — never ignore it |
| ORM | Cosmos SDK `Container` directly in repositories — never EF Core for Cosmos |

**Anti-patterns**: using entity Id as partition key, ignoring ETag on updates,
cross-partition queries in hot paths, unbounded `FeedIterator` without `MaxItemCount`.

---

### `processor` — Event Consumer / Background Worker

Use for services that consume Service Bus events and trigger side effects.

| Constraint | Rule |
|-----------|------|
| Session-based listener | `IHostedService` — never `BackgroundService` |
| Batch processing | `BackgroundService` with `AcceptNextSessionAsync` — never `IHostedService` |
| AutoCompleteMessages | Always `false` — never auto-complete |
| PrefetchCount | `1` for reliable processing |
| MaxConcurrentCallsPerSession | `1` for per-aggregate ordering |
| MaxConcurrentSessions | `1000` for cross-aggregate parallelism |
| DLQ processor | Always pair with main processor — never skip |
| StopAsync | `CloseAsync` — never `StopProcessingAsync` |
| Event routing | Inline `switch` expression — never a separate `EventRouter` class |
| Unknown subjects | Return `true` (complete) — never retry unknown events |
| Deserialization | `Encoding.UTF8.GetString(message.Body)` + Newtonsoft.Json — never System.Text.Json |
| DI scope | Create per message, resolve `IMediator` from scope — never reuse |
| gRPC `AlreadyExists` | Treat as idempotent success (`return true`) |
| Retry | Custom `RetryCallerService` with while loop — never Polly |

**Anti-patterns**: auto-completing messages, swallowing exceptions (must re-throw for abandon),
skipping the DLQ processor, using `BackgroundService` for session-based listeners.

---

### `gateway` — REST-to-gRPC Bridge

Use for the API gateway service that exposes REST endpoints and delegates to gRPC backends.

| Constraint | Rule |
|-----------|------|
| Base class | `ControllerBaseV1` — never raw `ControllerBase` |
| Routes | `[Route(DefaultRoute)]` from base class |
| gRPC client registration | `AddGrpcClient<T>((provider, options) => ...)` callback — never resolve URLs at registration time |
| Service URLs | `ServicesURLsOptions` with `[Required, Url]` + `ValidateOnStart()` |
| Response mapping | Inline in controller actions — never separate mapping classes |
| Enum conversions | Only exception allowed for separate extension methods |
| List responses | `Paginated<T>` — never raw collections |
| Command responses | `Response { Message }` wrapper — never raw strings |
| Proto types | Never expose in REST responses — always map to REST-specific DTOs |
| Business logic | None in gateway — map and delegate only |
| Authorization | `[Authorize]` / `[Authorize(Policy = ...)]` at class level |
| Policy names | `Policy` constants class — never hardcode strings |
| API docs | `AddBaseScalarApiDocumentation` — never Swagger UI |
| Startup validation | `MapControllersWithAuthorization()` — never `MapControllers()` without auth |

**Anti-patterns**: business logic in gateway controllers, exposing proto types to REST callers,
hardcoding service URLs, resolving gRPC client URLs outside the registration callback.

---

### `controlpanel` — Blazor WASM + MudBlazor

Use for the control panel UI service.

| Constraint | Rule |
|-----------|------|
| Data grids | `MudDataGrid<T>` with `ServerData` callback — never client-side filtering |
| Dialogs | `MudDialog` via `IDialogService` — never custom modals |
| Notifications | `MudSnackbar` — never alert boxes |
| Forms | `MudForm` with validation |
| Grid reload | `_dataGrid.ReloadServerData()` after every mutation |
| API calls | Typed gateway facade — never direct `HttpClient` in components |
| Gateway org | Nested management classes (`Gateway.Orders`) with lazy init (`??=`) |
| Return type | `ResponseResult<T>` from all gateway methods — never raw HTTP responses |
| Result handling | `ResponseResult<T>.Switch()` with both `onSuccess` and `onFailure` — never null checks |
| Error display | `Snackbar.Add(problem.Detail, Severity.Error)` in `onFailure` |
| Filter state | `QueryStringBindable` base class — never unsynced filter state |
| URL updates | `NavigateTo` with `replace: true` on filter change |
| Search debounce | 300ms — never fire API calls on every keystroke |
| Database access | None — always use gateway facade |

**Anti-patterns**: direct `HttpClient` in components, ignoring `ResponseResult` failures,
try/catch for API errors in UI components, unsynchronized filter state.

---

### `hybrid` — Command + Query Combined

Use when a single project handles both the write side (aggregates, events) and
the read side (event handlers, read models). Applies the highest-severity
constraints from both `command` and `query-sql`.

All `command` profile constraints apply to command-side code.
All `query-sql` profile constraints apply to query-side code.

Additional constraint: command and query sides **must use separate
`IUnitOfWork` implementations** and never share a `DbContext`.

---

## Generic profiles (5)

For standalone .NET applications. These profiles apply to any project type
without a specific microservice architecture.

---

### `generic` — Universal .NET (Fallback)

Applies when no more specific profile matches. Covers general .NET best practices.

| Area | Key constraints |
|------|----------------|
| Dependencies | One direction only — outer layers depend on inner, never reverse |
| Classes | `sealed` when not designed for inheritance; `private set` on entities |
| Immutable data | `record` types for DTOs, event data, value objects |
| Async | Never `async void`; always `Task`/`Task<T>` |
| Time | Always injected time provider — never `DateTime.Now` |
| Exceptions | Never catch generic `Exception` unless re-throwing with context |
| DI | Constructor injection only — never service locator |
| DbContext | Registered as `Scoped` — never Singleton or Transient |
| Queries | `.AsNoTracking()` for read-only; paginate all lists |
| Lazy loading | Never `UseLazyLoadingProxies()` |
| SaveChanges | Never inside loops — batch and save once |
| Raw SQL | Parameterized queries only — never string concatenation |

---

### `ddd` — Domain-Driven Design

| Area | Key constraints |
|------|----------------|
| Aggregates | All state changes through the root — never modify child entities directly |
| Creation | Factory methods only — never expose public constructors |
| Value objects | Immutable `sealed record` or `readonly record struct`; validate on construction |
| Typed IDs | Strongly-typed IDs for all aggregate roots and key entities |
| Domain events | Raised through aggregate root collection; dispatched in infrastructure only |
| Repositories | One per aggregate root (not per entity); interfaces in Domain, implementations in Infrastructure |
| Domain model | Business logic on entities — never anemic models |
| Collections | `IReadOnlyList<T>` — never expose `List<T>` |
| Bounded contexts | Never share entity classes across contexts; use anti-corruption layers |

---

### `clean-arch` — Clean Architecture

| Layer | Constraint |
|-------|-----------|
| **Domain** | Zero external package dependencies — pure C# only |
| **Domain** | Repository + `IUnitOfWork` interfaces defined here |
| **Application** | References only Domain — never Infrastructure or WebApi |
| **Application** | Defines interfaces for external services Infrastructure implements |
| **Infrastructure** | Implements Application/Domain interfaces; contains DbContext and repositories |
| **WebApi** | Composition root — wires all layers via DI; no business logic |
| **All** | Dependencies point inward: `WebApi → Infrastructure → Application → Domain` |
| **All** | Never create circular references between layers |
| **Never** | Return domain entities from API endpoints — always use DTOs |

---

### `vsa` — Vertical Slice Architecture

| Constraint | Rule |
|-----------|------|
| Organization | Feature folders — never layer folders (Domain/, Application/) |
| Slice content | Request, Response, Handler, Validator in a single file per operation |
| Handlers | `internal sealed` — never `public`; one per feature operation |
| Cross-feature | Never reference types from one feature folder inside another |
| Repositories | None — handlers talk to DbContext directly |
| Shared code | Only after 3+ proven duplications; goes in `Common/` only |
| Handlers | Each slice independently deletable without breaking others |
| Endpoint registration | Grouped by feature; co-located with the feature folder |

---

### `modular-monolith` — Modular Monolith

| Area | Key constraints |
|------|----------------|
| Module structure | Api (contracts) + Core (logic) + Infrastructure (data) |
| Module internals | `internal` — never expose implementation classes as `public` |
| Cross-module | Reference only the Api/contracts project — never Core or Infrastructure |
| Database | Separate `DbContext` per module; `HasDefaultSchema("{module}")` |
| Cross-module calls | Integration events (async) or module interfaces (sync reads only) |
| Write path | Never synchronous cross-module calls — eventual consistency |
| Shared kernel | Cross-cutting types only — no business logic |
| Module registration | Own DI extension method; registered by the host WebApi (composition root) |
| Public API | DTOs only through module interfaces — never domain entities |
| Migrations | Separate migrations history table per module |

---

## Quick reference

| Profile | Type | Data store | Architect agent |
|---------|------|-----------|-----------------|
| `command` | Microservice | SQL Server (event store) | `command-architect` |
| `query-sql` | Microservice | SQL Server (read models) | `query-architect` |
| `query-cosmos` | Microservice | Cosmos DB | `cosmos-architect` |
| `processor` | Microservice | Service Bus | `processor-architect` |
| `gateway` | Microservice | None (proxy) | `gateway-architect` |
| `controlpanel` | Microservice | None (HTTP) | `controlpanel-architect` |
| `hybrid` | Microservice | SQL Server (both sides) | `command-architect` + `query-architect` |
| `generic` | Any | Variable | `dotnet-architect` |
| `ddd` | Any | Variable | `dotnet-architect` |
| `clean-arch` | Any | Variable | `dotnet-architect` |
| `vsa` | Any | Variable | `dotnet-architect` |
| `modular-monolith` | Any | Multiple (per module) | `dotnet-architect` |
