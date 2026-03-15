# dotnet-ai-kit - Microservice Skills Specification

## Overview

This document specifies the code patterns and content for microservice-specific skills (Categories 9-15 + cross-cutting).
These skills apply primarily to microservice mode (CQRS + Event Sourcing).

Each actual skill file will be a `SKILL.md` (max 400 lines) with YAML frontmatter.
This spec provides the patterns and code examples that each skill must teach.

Patterns are extracted from scanned internal projects (Anis architecture).

> For generic .NET skills (Categories 1-8), see `14-generic-skills-spec.md`.

---

## CATEGORY 9: Command Side — Event Sourcing (6 skills)

---

### `microservice/event-structure` (#33) — Event&lt;TData&gt; Pattern

**Purpose**: Define the event structure used across all command-side services. Events are the source of truth — every state change is an event with typed data, sequence tracking, and aggregate identity.

**Packages**: Newtonsoft.Json

**Key Patterns**:
- `Event<TData>` base class with AggregateId, Sequence, Type, DateTime, Version
- `IEventData` interface for event data records
- EventType string constants matching class name
- Sequence tracking for ordering and idempotency
- JSON serialization with NullValueHandling.Ignore, StringEnumConverter

**Code Example**:
```csharp
public sealed class Event<TData> where TData : IEventData
{
    public Guid AggregateId { get; init; }
    public int Sequence { get; init; }
    public string Type { get; init; } = string.Empty;
    public DateTime DateTime { get; init; }
    public int Version { get; init; } = 1;
    public TData Data { get; init; } = default!;
}

public interface IEventData { }

// Event data as record
public sealed record OrderCreatedData(
    string CustomerName,
    decimal Total,
    List<OrderItemData> Items
) : IEventData;

// EventType constants
public static class EventTypes
{
    public const string OrderCreated = nameof(OrderCreated);
    public const string OrderUpdated = nameof(OrderUpdated);
}
```

**Detection**: Grep for `Event<` and `IEventData` in Domain layer
**Reference**: `knowledge/event-sourcing-flow.md`

---

### `microservice/aggregate` (#34) — Aggregate&lt;T&gt; Base Class

**Purpose**: Aggregates enforce business invariants and produce events. The base class provides LoadFromHistory (replay) and ApplyChange (new event) mechanics.

**Packages**: None (domain layer, no external deps)

**Key Patterns**:
- `Aggregate<T>` abstract base with Id, Sequence, Events list
- `LoadFromHistory(IEnumerable<Event<T>>)` replays events
- `ApplyChange(Event<T>)` applies new event and increments sequence
- Private `Apply(Event<T>)` method routes to typed handlers
- Factory methods for creation (not constructors)
- Uncommitted events list for persistence

**Code Example**:
```csharp
public abstract class Aggregate<T> where T : IEventData
{
    public Guid Id { get; protected set; }
    public int Sequence { get; protected set; }
    private readonly List<Event<T>> _uncommittedEvents = [];

    public IReadOnlyList<Event<T>> UncommittedEvents => _uncommittedEvents;

    public void LoadFromHistory(IEnumerable<Event<T>> history)
    {
        foreach (var @event in history)
        {
            Apply(@event);
            Sequence = @event.Sequence;
        }
    }

    protected void ApplyChange(Event<T> @event)
    {
        Apply(@event);
        _uncommittedEvents.Add(@event);
        Sequence = @event.Sequence;
    }

    protected abstract void Apply(Event<T> @event);

    // Factory method pattern
    public static Order Create(string customerName, decimal total)
    {
        var order = new Order();
        var @event = new Event<OrderCreatedData>
        {
            AggregateId = Guid.NewGuid(),
            Sequence = 1,
            Type = EventTypes.OrderCreated,
            DateTime = DateTime.UtcNow,
            Data = new OrderCreatedData(customerName, total, [])
        };
        order.ApplyChange(@event);
        return order;
    }
}
```

**Detection**: Grep for `class.*:.*Aggregate<` or `LoadFromHistory`
**Reference**: `knowledge/event-sourcing-flow.md`

---

### `microservice/event-sourcing-flow` (#35) — Complete Event Sourcing Flow

**Purpose**: The end-to-end flow from command handler → aggregate → event → database → outbox → service bus. This skill connects all command-side patterns together.

**Packages**: MediatR, EF Core, Azure.Messaging.ServiceBus

**Key Patterns**:
- Handler receives command via MediatR
- Handler loads aggregate from event store (or creates new)
- Aggregate produces event(s) via ApplyChange
- CommitEventService saves events + outbox in one transaction
- ServiceBusPublisher (background) reads outbox and sends to bus
- Outbox guarantees at-least-once delivery

**Code Example**:
```csharp
// Handler flow
public sealed class CreateOrderHandler(
    IEventStore<OrderEventData> eventStore,
    ICommitEventService<OrderEventData> commitService)
    : IRequestHandler<CreateOrderCommand, OrderOutput>
{
    public async Task<OrderOutput> Handle(CreateOrderCommand request, CancellationToken ct)
    {
        var order = Order.Create(request.CustomerName, request.Total);

        await commitService.CommitAsync(order.Id, order.UncommittedEvents, ct);

        return new OrderOutput(order.Id, order.Sequence);
    }
}
```

**Detection**: Grep for `ICommitEventService` or `CommitAsync.*UncommittedEvents`
**Reference**: `knowledge/event-sourcing-flow.md`, `knowledge/outbox-pattern.md`

---

### `microservice/outbox-pattern` (#36) — Outbox + ServiceBusPublisher

**Purpose**: Reliable event publishing via the outbox pattern. Events are saved to an outbox table in the same transaction as domain events, then published asynchronously by a background service.

**Packages**: EF Core, Azure.Messaging.ServiceBus

**Key Patterns**:
- OutboxMessage entity: EventId, Topic, Body, CreatedAt, PublishedAt
- CommitEventService: saves events + outbox rows in one DbTransaction
- ServiceBusPublisher: BackgroundService polls outbox, sends to Service Bus
- Topic naming: `{company}-{domain}-{side}`
- Message properties: Subject = EventType, SessionId = AggregateId
- At-least-once delivery (consumers must be idempotent)

**Code Example**:
```csharp
// CommitEventService
public sealed class CommitEventService<T>(ApplicationDbContext db) : ICommitEventService<T>
    where T : IEventData
{
    public async Task CommitAsync(Guid aggregateId, IReadOnlyList<Event<T>> events, CancellationToken ct)
    {
        await using var transaction = await db.Database.BeginTransactionAsync(ct);

        db.Events.AddRange(events);

        foreach (var @event in events)
        {
            db.OutboxMessages.Add(new OutboxMessage
            {
                EventId = @event.AggregateId,
                Topic = TopicName,
                Subject = @event.Type,
                SessionId = aggregateId.ToString(),
                Body = JsonConvert.SerializeObject(@event),
                CreatedAt = DateTime.UtcNow
            });
        }

        await db.SaveChangesAsync(ct);
        await transaction.CommitAsync(ct);
    }
}

// ServiceBusPublisher (background)
public sealed class ServiceBusPublisher(
    IServiceScopeFactory scopeFactory,
    ServiceBusSender sender) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            using var scope = scopeFactory.CreateScope();
            var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();

            var pending = await db.OutboxMessages
                .Where(m => m.PublishedAt == null)
                .OrderBy(m => m.CreatedAt)
                .Take(100)
                .ToListAsync(ct);

            foreach (var message in pending)
            {
                await sender.SendMessageAsync(new ServiceBusMessage(message.Body)
                {
                    Subject = message.Subject,
                    SessionId = message.SessionId
                }, ct);

                message.PublishedAt = DateTime.UtcNow;
            }

            await db.SaveChangesAsync(ct);
            await Task.Delay(TimeSpan.FromSeconds(1), ct);
        }
    }
}
```

**Detection**: Grep for `OutboxMessage` or `ServiceBusPublisher`
**Reference**: `knowledge/outbox-pattern.md`

---

### `microservice/command-handler` (#37) — MediatR Command Handler

**Purpose**: Command handlers orchestrate the business flow: validate, load/create aggregate, apply change, commit, return output.

**Packages**: MediatR, FluentValidation

**Key Patterns**:
- `IRequestHandler<TCommand, TOutput>` with MediatR
- Load aggregate from event store or create new
- Apply business rules through aggregate methods
- Commit via CommitEventService
- Return output DTO (not the aggregate)
- Validation via FluentValidation pipeline behavior

**Code Example**:
```csharp
public sealed record CreateOrderCommand(string CustomerName, decimal Total) : IRequest<OrderOutput>;

public sealed class CreateOrderHandler(
    ICommitEventService<OrderEventData> commitService)
    : IRequestHandler<CreateOrderCommand, OrderOutput>
{
    public async Task<OrderOutput> Handle(CreateOrderCommand request, CancellationToken ct)
    {
        var order = Order.Create(request.CustomerName, request.Total);
        await commitService.CommitAsync(order.Id, order.UncommittedEvents, ct);
        return new OrderOutput(order.Id, order.Sequence);
    }
}

public sealed class CreateOrderValidator : AbstractValidator<CreateOrderCommand>
{
    public CreateOrderValidator()
    {
        RuleFor(x => x.CustomerName).NotEmpty().WithMessage(Phrases.CustomerNameRequired);
        RuleFor(x => x.Total).GreaterThan(0).WithMessage(Phrases.InvalidTotal);
    }
}
```

**Detection**: Grep for `IRequestHandler<.*Command`
**Reference**: `knowledge/event-sourcing-flow.md`

---

### `microservice/command-db-config` (#38) — EF Core Configuration

**Purpose**: Database configuration for the command side: event storage, outbox table, discriminator columns, generic event configuration.

**Packages**: EF Core, SQL Server

**Key Patterns**:
- ApplicationDbContext with DbSet<Event<T>> and DbSet<OutboxMessage>
- GenericEventConfiguration<T> for event table mapping
- Discriminator column for event types
- JSON column for event data (SQL Server)
- Index on AggregateId + Sequence (unique)

**Code Example**:
```csharp
public class ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
    : DbContext(options)
{
    public DbSet<Event<OrderEventData>> Events => Set<Event<OrderEventData>>();
    public DbSet<OutboxMessage> OutboxMessages => Set<OutboxMessage>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfiguration(new GenericEventConfiguration<OrderEventData>());
        modelBuilder.ApplyConfiguration(new OutboxMessageConfiguration());
    }
}

public class GenericEventConfiguration<T> : IEntityTypeConfiguration<Event<T>>
    where T : IEventData
{
    public void Configure(EntityTypeBuilder<Event<T>> builder)
    {
        builder.HasKey(e => new { e.AggregateId, e.Sequence });
        builder.Property(e => e.Data).HasColumnType("nvarchar(max)")
            .HasConversion(
                v => JsonConvert.SerializeObject(v),
                v => JsonConvert.DeserializeObject<T>(v)!);
        builder.HasIndex(e => e.AggregateId);
    }
}
```

**Detection**: Grep for `GenericEventConfiguration` or `DbSet<Event<`
**Reference**: `knowledge/event-sourcing-flow.md`

---

## CATEGORY 10: Query Side — SQL Server (5 skills)

---

### `microservice/query-entity` (#39) — Query Entity Pattern

**Purpose**: Query entities have private setters, are constructed from events, and use strict sequence checking. They represent the read-side projection of events.

**Packages**: None (domain layer)

**Key Patterns**:
- Private setters on all properties
- Constructor from `Event<TData>` (creation event)
- `Apply(Event<TData>)` methods for update events
- Sequence field for idempotency
- Row version for concurrency
- No public setters — state changes ONLY through event application

**Code Example**:
```csharp
public sealed class Order
{
    public Guid Id { get; private set; }
    public string CustomerName { get; private set; } = string.Empty;
    public decimal Total { get; private set; }
    public int Sequence { get; private set; }
    public byte[] RowVersion { get; private set; } = [];

    private Order() { } // EF Core

    public Order(Event<OrderCreatedData> @event)
    {
        Id = @event.AggregateId;
        CustomerName = @event.Data.CustomerName;
        Total = @event.Data.Total;
        Sequence = @event.Sequence;
    }

    public void Apply(Event<OrderUpdatedData> @event)
    {
        if (@event.Sequence != Sequence + 1)
            throw new InvalidOperationException($"Expected sequence {Sequence + 1}, got {@event.Sequence}");

        CustomerName = @event.Data.CustomerName ?? CustomerName;
        Total = @event.Data.Total;
        Sequence = @event.Sequence;
    }
}
```

**Detection**: Grep for `private set` + constructor taking `Event<`
**Reference**: `knowledge/event-sourcing-flow.md`

---

### `microservice/query-event-handler` (#40) — Event Handler

**Purpose**: Handlers receive events from Service Bus and apply them to query entities. Strict sequence checking ensures consistency. Handlers are idempotent.

**Packages**: MediatR, EF Core

**Key Patterns**:
- `IRequestHandler<Event<TData>, bool>` returning true (processed) or false (retry)
- Load entity by AggregateId
- Check sequence: if already applied, return true (idempotent)
- If sequence gap, return false (out of order, retry later)
- Apply event, save changes

**Code Example**:
```csharp
public sealed class OrderCreatedHandler(ApplicationDbContext db)
    : IRequestHandler<Event<OrderCreatedData>, bool>
{
    public async Task<bool> Handle(Event<OrderCreatedData> @event, CancellationToken ct)
    {
        var exists = await db.Orders.AnyAsync(o => o.Id == @event.AggregateId, ct);
        if (exists) return true; // Idempotent: already processed

        var order = new Order(@event);
        db.Orders.Add(order);
        await db.SaveChangesAsync(ct);
        return true;
    }
}

public sealed class OrderUpdatedHandler(ApplicationDbContext db)
    : IRequestHandler<Event<OrderUpdatedData>, bool>
{
    public async Task<bool> Handle(Event<OrderUpdatedData> @event, CancellationToken ct)
    {
        var order = await db.Orders.FindAsync([@event.AggregateId], ct);
        if (order is null) return false; // Entity not yet created, retry

        if (@event.Sequence <= order.Sequence) return true; // Already applied
        if (@event.Sequence != order.Sequence + 1) return false; // Gap, retry

        order.Apply(@event);
        await db.SaveChangesAsync(ct);
        return true;
    }
}
```

**Detection**: Grep for `IRequestHandler<Event<.*>, bool>`
**Reference**: `knowledge/event-sourcing-flow.md`

---

### `microservice/service-bus-listener` (#41) — Service Bus Session Processor

**Purpose**: Background service that listens to Azure Service Bus topics, deserializes events, and dispatches them via MediatR. Uses sessions for ordered processing per aggregate.

**Packages**: Azure.Messaging.ServiceBus, MediatR

**Key Patterns**:
- IHostedService with ServiceBusSessionProcessor
- Session = AggregateId (ensures ordered processing per aggregate)
- Subject = EventType (for routing)
- Deserialize → MediatR.Send → if false, abandon (retry)
- Dead letter after max retries
- Graceful shutdown: close processor in StopAsync

**Code Example**:
```csharp
public sealed class OrderEventListener(
    ServiceBusClient client,
    IServiceScopeFactory scopeFactory) : IHostedService
{
    private ServiceBusSessionProcessor? _processor;

    public async Task StartAsync(CancellationToken ct)
    {
        _processor = client.CreateSessionProcessor("company-order-commands", "query-subscription",
            new ServiceBusSessionProcessorOptions { MaxConcurrentSessions = 10 });

        _processor.ProcessMessageAsync += ProcessMessageAsync;
        _processor.ProcessErrorAsync += ProcessErrorAsync;

        await _processor.StartProcessingAsync(ct);
    }

    private async Task ProcessMessageAsync(ProcessSessionMessageEventArgs args)
    {
        using var scope = scopeFactory.CreateScope();
        var mediator = scope.ServiceProvider.GetRequiredService<IMediator>();

        var eventType = args.Message.Subject;
        var body = args.Message.Body.ToString();
        var @event = EventDeserializer.Deserialize(eventType, body);

        var result = await mediator.Send(@event);

        if (result is true)
            await args.CompleteMessageAsync(args.Message);
        else
            await args.AbandonMessageAsync(args.Message);
    }

    public async Task StopAsync(CancellationToken ct)
    {
        if (_processor is not null)
            await _processor.StopProcessingAsync(ct);
    }
}
```

**Detection**: Grep for `ServiceBusSessionProcessor` or `CreateSessionProcessor`
**Reference**: `knowledge/service-bus-patterns.md`

---

### `microservice/query-handler` (#42) — MediatR Query Handler

**Purpose**: Query handlers implement read operations: filtered lists with pagination, single entity lookups, and DTO projections.

**Packages**: MediatR, EF Core

**Key Patterns**:
- `IRequest<Paginated<TOutput>>` for list queries
- `IRequest<TOutput?>` for single entity queries
- AsNoTracking for read queries
- Projection to output DTOs (Select, not AutoMapper)
- Pagination with Skip/Take or cursor-based
- Filtering via IQueryable extensions

**Code Example**:
```csharp
public sealed record GetOrdersQuery(int Page, int PageSize, string? Search)
    : IRequest<Paginated<OrderOutput>>;

public sealed class GetOrdersHandler(ApplicationDbContext db)
    : IRequestHandler<GetOrdersQuery, Paginated<OrderOutput>>
{
    public async Task<Paginated<OrderOutput>> Handle(GetOrdersQuery request, CancellationToken ct)
    {
        var query = db.Orders.AsNoTracking();

        if (!string.IsNullOrEmpty(request.Search))
            query = query.Where(o => o.CustomerName.Contains(request.Search));

        var total = await query.CountAsync(ct);

        var items = await query
            .OrderByDescending(o => o.Sequence)
            .Skip((request.Page - 1) * request.PageSize)
            .Take(request.PageSize)
            .Select(o => new OrderOutput(o.Id, o.CustomerName, o.Total))
            .ToListAsync(ct);

        return new Paginated<OrderOutput>(items, total, request.Page, request.PageSize);
    }
}
```

**Detection**: Grep for `IRequest<Paginated<` or `AsNoTracking()`
**Reference**: Internal query project patterns

---

### `microservice/query-repository` (#43) — Repository + UnitOfWork

**Purpose**: Generic async repository pattern for query-side data access with UnitOfWork for transaction management.

**Packages**: EF Core

**Key Patterns**:
- `IAsyncRepository<T>` with CRUD operations
- `IUnitOfWork` wrapping DbContext.SaveChangesAsync
- Specialized repositories for complex queries
- No repository for simple queries (use DbContext directly via MediatR handlers)

**Code Example**:
```csharp
public interface IAsyncRepository<T> where T : class
{
    Task<T?> FindAsync(Guid id, CancellationToken ct);
    Task<List<T>> ListAsync(CancellationToken ct);
    Task AddAsync(T entity, CancellationToken ct);
    void Update(T entity);
}

public sealed class AsyncRepository<T>(ApplicationDbContext db) : IAsyncRepository<T>
    where T : class
{
    public async Task<T?> FindAsync(Guid id, CancellationToken ct) =>
        await db.Set<T>().FindAsync([id], ct);

    public async Task<List<T>> ListAsync(CancellationToken ct) =>
        await db.Set<T>().ToListAsync(ct);

    public async Task AddAsync(T entity, CancellationToken ct) =>
        await db.Set<T>().AddAsync(entity, ct);

    public void Update(T entity) =>
        db.Set<T>().Update(entity);
}
```

**Detection**: Grep for `IAsyncRepository` or `AsyncRepository`
**Reference**: Internal query project patterns

---

## CATEGORY 11: Cosmos DB (4 skills)

---

### `microservice/cosmos-entity` (#44) — IContainerDocument

**Purpose**: Cosmos DB entities implement IContainerDocument with partition keys, discriminator, and ETag for concurrency.

**Packages**: Microsoft.Azure.Cosmos

**Key Patterns**:
- `IContainerDocument` interface with ContainerName, PartitionKeys, Discriminator
- 3-level hierarchical PartitionKeys via PartitionKeyBuilder
- Discriminator string for polymorphic containers
- ETag for optimistic concurrency
- `id` property (Cosmos requirement)

**Code Example**:
```csharp
public interface IContainerDocument
{
    string ContainerName { get; }
    PartitionKey PartitionKeys { get; }
    string Discriminator { get; }
    string? ETag { get; set; }
}

public sealed class MerchantSalesReport : IContainerDocument
{
    public string id { get; set; } = string.Empty;
    public string MerchantId { get; private set; } = string.Empty;
    public string ReportMonth { get; private set; } = string.Empty;
    public decimal TotalSales { get; private set; }

    public string ContainerName => "sales-reports";
    public string Discriminator => "MerchantSalesReport";
    public string? ETag { get; set; }

    public PartitionKey PartitionKeys => new PartitionKeyBuilder()
        .Add(MerchantId)
        .Add(ReportMonth)
        .Add(Discriminator)
        .Build();
}
```

**Detection**: Grep for `IContainerDocument` or `PartitionKeyBuilder`
**Reference**: `knowledge/cosmos-patterns.md`

---

### `microservice/cosmos-repository` (#45) — Cosmos Repository

**Purpose**: Repository pattern for Cosmos DB with LINQ queries, FeedIterator, and RU monitoring.

**Packages**: Microsoft.Azure.Cosmos

**Key Patterns**:
- Container-based repository (one per document type)
- LINQ queries via `GetItemLinqQueryable<T>()`
- FeedIterator for large result sets
- RU charge tracking from response headers
- Point reads via `ReadItemAsync` (most efficient)

**Code Example**:
```csharp
public sealed class CosmosRepository<T>(Container container) where T : IContainerDocument
{
    public async Task<T?> GetByIdAsync(string id, PartitionKey pk, CancellationToken ct)
    {
        try
        {
            var response = await container.ReadItemAsync<T>(id, pk, cancellationToken: ct);
            return response.Resource;
        }
        catch (CosmosException ex) when (ex.StatusCode == HttpStatusCode.NotFound)
        {
            return default;
        }
    }

    public async Task UpsertAsync(T document, CancellationToken ct)
    {
        await container.UpsertItemAsync(document, document.PartitionKeys,
            new ItemRequestOptions { IfMatchEtag = document.ETag }, ct);
    }
}
```

**Detection**: Grep for `Container` + `ReadItemAsync` or `GetItemLinqQueryable`
**Reference**: `knowledge/cosmos-patterns.md`

---

### `microservice/cosmos-unit-of-work` (#46) — TransactionalBatch

**Purpose**: Atomic multi-document operations in Cosmos DB using TransactionalBatch. All operations in a batch share the same partition key.

**Packages**: Microsoft.Azure.Cosmos

**Key Patterns**:
- `container.CreateTransactionalBatch(partitionKey)`
- CreateItem, UpsertItem, ReplaceItem, DeleteItem in batch
- All items must share same partition key
- ExecuteAsync returns batch response with per-item status
- Chunked batches for >100 operations

**Code Example**:
```csharp
public async Task CommitBatchAsync(PartitionKey pk, List<IContainerDocument> documents, CancellationToken ct)
{
    var batch = container.CreateTransactionalBatch(pk);

    foreach (var doc in documents)
    {
        if (doc.ETag is null)
            batch.CreateItem(doc);
        else
            batch.UpsertItem(doc, new TransactionalBatchItemRequestOptions { IfMatchEtag = doc.ETag });
    }

    var response = await batch.ExecuteAsync(ct);

    if (!response.IsSuccessStatusCode)
        throw new CosmosException($"Batch failed: {response.StatusCode}", response.StatusCode, 0, "", 0);
}
```

**Detection**: Grep for `CreateTransactionalBatch`
**Reference**: `knowledge/cosmos-patterns.md`

---

### `microservice/cosmos-config` (#47) — Cosmos Configuration

**Purpose**: Cosmos DB client configuration with ServicePrincipal or AuthKey, direct mode, and DatabaseRunner for initialization.

**Packages**: Microsoft.Azure.Cosmos, Azure.Identity

**Key Patterns**:
- CosmosClient with DefaultAzureCredential (production) or AuthKey (dev)
- Direct mode for performance
- DatabaseRunner: ensure database + containers exist on startup
- Container throughput configuration

**Code Example**:
```csharp
// Registration
services.AddSingleton(sp =>
{
    var options = sp.GetRequiredService<IOptions<CosmosOptions>>().Value;

    var clientOptions = new CosmosClientOptions
    {
        SerializerOptions = new CosmosSerializationOptions
        {
            PropertyNamingPolicy = CosmosPropertyNamingPolicy.CamelCase
        },
        ConnectionMode = ConnectionMode.Direct
    };

    return string.IsNullOrEmpty(options.AuthKey)
        ? new CosmosClient(options.Endpoint, new DefaultAzureCredential(), clientOptions)
        : new CosmosClient(options.Endpoint, options.AuthKey, clientOptions);
});
```

**Detection**: Grep for `CosmosClient` or `CosmosOptions`
**Reference**: `knowledge/cosmos-patterns.md`

---

## CATEGORY 12: Processor (4 skills)

---

### `microservice/hosted-service` (#48) — Background Service

**Purpose**: IHostedService-based background services that listen to Service Bus topics and process events. Manages lifecycle, graceful shutdown, and error handling.

**Packages**: Azure.Messaging.ServiceBus

**Key Patterns**:
- IHostedService (not BackgroundService — more control over lifecycle)
- ServiceBusSessionProcessor for ordered processing
- Start/Stop lifecycle management
- Error handler with logging
- Configurable MaxConcurrentSessions

**Detection**: Grep for `IHostedService` + `ServiceBusSessionProcessor`
**Reference**: `knowledge/service-bus-patterns.md`

---

### `microservice/event-routing` (#49) — Subject-Based Routing

**Purpose**: Route incoming events to the correct handler based on the event subject (type). Uses MediatR for dispatch.

**Packages**: MediatR, Newtonsoft.Json

**Key Patterns**:
- Message.Subject contains EventType string
- EventDeserializer maps subject → Event<TData> type
- MediatR.Send dispatches to correct handler
- Unknown subjects: log warning, complete message (don't retry unknown events)

**Code Example**:
```csharp
public static class EventDeserializer
{
    public static object Deserialize(string subject, string body) => subject switch
    {
        EventTypes.OrderCreated => JsonConvert.DeserializeObject<Event<OrderCreatedData>>(body)!,
        EventTypes.OrderUpdated => JsonConvert.DeserializeObject<Event<OrderUpdatedData>>(body)!,
        _ => throw new UnknownEventTypeException(subject)
    };
}
```

**Detection**: Grep for `EventDeserializer` or switch on `Subject`
**Reference**: `knowledge/service-bus-patterns.md`

---

### `microservice/grpc-client` (#50) — gRPC Client Factory

**Purpose**: Register and use gRPC clients for calling other microservices from processor or gateway.

**Packages**: Grpc.Net.ClientFactory

**Key Patterns**:
- `AddGrpcClient<T>` with address from options
- ExternalServicesOptions for service URLs
- ValidateOnStart for URL validation
- Error handling: RpcException → retry or dead letter

**Code Example**:
```csharp
// Registration
services.AddGrpcClient<OrderQueries.OrderQueriesClient>(o =>
{
    o.Address = new Uri(externalServices.QueryServiceUrl);
});

// Usage in handler
public sealed class NotifyQueryHandler(OrderQueries.OrderQueriesClient queryClient)
{
    public async Task Handle(Event<OrderCreatedData> @event, CancellationToken ct)
    {
        await queryClient.SyncOrderAsync(new SyncOrderRequest
        {
            OrderId = @event.AggregateId.ToString()
        }, cancellationToken: ct);
    }
}
```

**Detection**: Grep for `AddGrpcClient<` or `GrpcClientFactory`
**Reference**: `knowledge/grpc-patterns.md`

---

### `microservice/batch-processing` (#51) — Batch Event Processing

**Purpose**: Process multiple events in order within a Service Bus session. Uses SemaphoreSlim for concurrency control and handles deduplication.

**Packages**: Azure.Messaging.ServiceBus

**Key Patterns**:
- Session-based ordered processing (one aggregate at a time)
- SemaphoreSlim for max concurrent sessions
- Process all messages in a session before moving to next
- Deduplication via sequence checking (handled by event handlers)

**Detection**: Grep for `SemaphoreSlim` + `ServiceBusSessionProcessor`
**Reference**: `knowledge/service-bus-patterns.md`

---

## CATEGORY 13: gRPC (3 skills)

---

### `microservice/grpc-service` (#52) — gRPC Service Implementation

**Purpose**: Implement gRPC services from proto definitions. Services delegate to MediatR handlers and use mapping extensions.

**Packages**: Grpc.AspNetCore, MediatR

**Key Patterns**:
- Proto file with service/rpc definitions
- Service class inherits generated base
- Mapping extensions: Request → Command, Output → Response
- Proto types: StringValue for nullable, Timestamp for DateTime
- Pagination in proto: PageRequest, PageResponse

**Code Example**:
```csharp
// Proto: service OrderCommands { rpc CreateOrder (CreateOrderRequest) returns (CreateOrderResponse); }

public sealed class OrderCommandsService(IMediator mediator)
    : OrderCommands.OrderCommandsBase
{
    public override async Task<CreateOrderResponse> CreateOrder(
        CreateOrderRequest request, ServerCallContext context)
    {
        var command = request.ToCommand(); // Mapping extension
        var output = await mediator.Send(command);
        return output.ToResponse(); // Mapping extension
    }
}

// Mapping extensions
public static class OrderCommandExtensions
{
    public static CreateOrderCommand ToCommand(this CreateOrderRequest request) =>
        new(request.CustomerName, (decimal)request.Total);

    public static CreateOrderResponse ToResponse(this OrderOutput output) =>
        new() { OrderId = output.Id.ToString(), Sequence = output.Sequence };
}
```

**Detection**: Grep for `.proto` files or class inheriting `*Base` from generated gRPC
**Reference**: `knowledge/grpc-patterns.md`

---

### `microservice/grpc-interceptors` (#53) — gRPC Interceptors

**Purpose**: Cross-cutting concerns for gRPC: exception handling, culture switching, logging, access claims.

**Packages**: Grpc.AspNetCore

**Key Patterns**:
- ApplicationExceptionInterceptor: catch domain exceptions → RpcException with ProblemDetails
- ThreadCultureInterceptor: read "language" header → set thread culture
- Access claims from "access-claims-bin" metadata header
- Registration order matters

**Code Example**:
```csharp
public sealed class ApplicationExceptionInterceptor : Interceptor
{
    public override async Task<TResponse> UnaryServerHandler<TRequest, TResponse>(
        TRequest request, ServerCallContext context,
        UnaryServerMethod<TRequest, TResponse> continuation)
    {
        try { return await continuation(request, context); }
        catch (DomainException ex) when (ex is IProblemDetailsProvider provider)
        {
            var metadata = new Metadata();
            var problemDetails = provider.ToProblemDetails();
            metadata.Add("problem-details-bin", JsonConvert.SerializeObject(problemDetails));
            throw new RpcException(new Status(MapStatusCode(ex), ex.Message), metadata);
        }
    }
}
```

**Detection**: Grep for `Interceptor` + `UnaryServerHandler`
**Reference**: `knowledge/grpc-patterns.md`

---

### `microservice/grpc-validation` (#54) — FluentValidation + gRPC

**Purpose**: Validate gRPC requests using FluentValidation before they reach handlers.

**Packages**: FluentValidation, Calzolari.Grpc.AspNetCore.Validation

**Key Patterns**:
- `AbstractValidator<TRequest>` for each gRPC request
- Calzolari integration: `AddGrpcValidation()` + `AddValidator<T>()`
- Validation errors → RpcException with InvalidArgument status
- Resource-based error messages (Phrases.InvalidXxx)

**Code Example**:
```csharp
public sealed class CreateOrderRequestValidator : AbstractValidator<CreateOrderRequest>
{
    public CreateOrderRequestValidator()
    {
        RuleFor(x => x.CustomerName).NotEmpty().WithMessage(Phrases.CustomerNameRequired);
        RuleFor(x => x.Total).GreaterThan(0).WithMessage(Phrases.InvalidTotal);
    }
}

// Registration
services.AddGrpcValidation();
services.AddAppValidators(); // Scans assembly for validators
```

**Detection**: Grep for `AddGrpcValidation` or `Calzolari`
**Reference**: `knowledge/grpc-patterns.md`

---

## CATEGORY 14: Gateway (4 skills)

---

### `microservice/gateway-endpoint` (#55) — REST Controller

**Purpose**: Gateway controllers expose REST endpoints that delegate to gRPC services. Handle model binding, response mapping, and pagination.

**Packages**: ASP.NET Core, Grpc.Net.Client

**Key Patterns**:
- [ApiController] with [Route("api/v1/[controller]")]
- Inject gRPC client via constructor
- Map REST request → gRPC request → gRPC response → REST response
- Paginated<T> wrapper for list endpoints
- Export endpoints (CSV/Excel)

**Code Example**:
```csharp
[ApiController]
[Route("api/v1/orders")]
public sealed class OrderController(OrderCommands.OrderCommandsClient commandClient,
    OrderQueries.OrderQueriesClient queryClient) : ControllerBase
{
    [HttpPost]
    public async Task<ActionResult<OrderResponse>> Create(CreateOrderRequest request, CancellationToken ct)
    {
        var grpcRequest = request.ToGrpcRequest();
        var result = await commandClient.CreateOrderAsync(grpcRequest, cancellationToken: ct);
        return Ok(result.ToResponse());
    }

    [HttpGet]
    public async Task<ActionResult<Paginated<OrderResponse>>> GetAll(
        [FromQuery] int page = 1, [FromQuery] int pageSize = 20, CancellationToken ct = default)
    {
        var result = await queryClient.GetOrdersAsync(new GetOrdersRequest
        {
            Page = page, PageSize = pageSize
        }, cancellationToken: ct);
        return Ok(result.ToPaginatedResponse());
    }
}
```

**Detection**: Grep for `[ApiController]` + `GrpcClient` injection
**Reference**: Internal gateway project patterns

---

### `microservice/gateway-registration` (#56) — gRPC Client Registration

**Purpose**: Register gRPC clients for all backend services with URL configuration and validation.

**Packages**: Grpc.Net.ClientFactory, Microsoft.Extensions.Options

**Key Patterns**:
- ExternalServicesOptions with service URLs
- AddGrpcClient<T> per service
- ValidateOnStart ensures URLs are configured
- Channel configuration (interceptors, deadlines)

**Code Example**:
```csharp
public sealed class ExternalServicesOptions
{
    public string CommandServiceUrl { get; set; } = string.Empty;
    public string QueryServiceUrl { get; set; } = string.Empty;
}

// Registration
services.AddOptions<ExternalServicesOptions>()
    .BindConfiguration("ExternalServices")
    .ValidateDataAnnotations()
    .ValidateOnStart();

var externalServices = configuration.GetSection("ExternalServices").Get<ExternalServicesOptions>()!;

services.AddGrpcClient<OrderCommands.OrderCommandsClient>(o =>
    o.Address = new Uri(externalServices.CommandServiceUrl));

services.AddGrpcClient<OrderQueries.OrderQueriesClient>(o =>
    o.Address = new Uri(externalServices.QueryServiceUrl));
```

**Detection**: Grep for `ExternalServicesOptions` or multiple `AddGrpcClient`
**Reference**: Internal gateway project patterns

---

### `microservice/gateway-security` (#57) — Security Policies

**Purpose**: API authentication and authorization for gateway endpoints.

**Packages**: Microsoft.AspNetCore.Authentication.JwtBearer

**Key Patterns**:
- JWT Bearer authentication
- Policy-based authorization
- API key validation middleware
- Scalar UI with auth configuration

**Detection**: Grep for `AddAuthentication` + `AddJwtBearer` or `[Authorize(Policy =`
**Reference**: Internal gateway project patterns

---

### `microservice/gateway-documentation` (#58) — Scalar API Docs

**Purpose**: Scalar API documentation for all gateway types. Scalar replaces Swagger for all new and existing projects.

**Packages**: Scalar.AspNetCore

**Key Patterns**:
- `app.MapScalarApiReference()` replaces `app.UseSwaggerUI()`
- Theme configuration
- Authentication prefill for testing
- Group by controller/tag

**Code Example**:
```csharp
// Program.cs
builder.Services.AddOpenApi();

var app = builder.Build();

app.MapOpenApi();
app.MapScalarApiReference(options =>
{
    options.WithTitle("Order Gateway API")
           .WithTheme(ScalarTheme.Mars);
});
```

**Detection**: Grep for `MapScalarApiReference` or `Scalar.AspNetCore`
**Reference**: Internal gateway project patterns

---

## CATEGORY 15: Control Panel (5 skills)

---

### `microservice/cp-gateway-facade` (#59) — Gateway HTTP Client

**Purpose**: Typed HttpClient wrapper that calls gateway REST endpoints from Blazor WASM.

**Packages**: System.Net.Http.Json

**Key Patterns**:
- Typed HttpClient per gateway
- Nested management: OrdersGateway.Create(), OrdersGateway.GetAll()
- HttpExtensions for consistent serialization
- ResponseResult<T> wrapping

**Code Example**:
```csharp
public sealed class OrdersGateway(HttpClient http)
{
    public async Task<ResponseResult<OrderResponse>> CreateAsync(CreateOrderRequest request) =>
        await http.PostAsJsonAsync<ResponseResult<OrderResponse>>("api/v1/orders", request);

    public async Task<ResponseResult<Paginated<OrderResponse>>> GetAllAsync(int page, int pageSize) =>
        await http.GetFromJsonAsync<ResponseResult<Paginated<OrderResponse>>>(
            $"api/v1/orders?page={page}&pageSize={pageSize}");
}
```

**Detection**: Grep for `Gateway` class with `HttpClient` constructor
**Reference**: Internal control panel patterns

---

### `microservice/cp-response-result` (#60) — ResponseResult&lt;T&gt;.Switch()

**Purpose**: Unified response handling for gateway calls. Switch() pattern routes success/failure to appropriate UI actions.

**Packages**: None (custom pattern)

**Key Patterns**:
- `ResponseResult<T>` with Success/Failure state
- `.Switch(onSuccess, onFailure)` extension method
- ProblemDetails parsing from gateway errors
- Snackbar/toast for error display

**Code Example**:
```csharp
var result = await OrdersGateway.CreateAsync(request);

result.Switch(
    onSuccess: order =>
    {
        Snackbar.Add("Order created", Severity.Success);
        NavigationManager.NavigateTo($"/orders/{order.Id}");
    },
    onFailure: problem =>
    {
        Snackbar.Add(problem.Detail ?? "Error creating order", Severity.Error);
    }
);
```

**Detection**: Grep for `ResponseResult<` or `.Switch(`
**Reference**: Internal control panel patterns

---

### `microservice/cp-blazor-page` (#61) — MudBlazor Page Patterns

**Purpose**: Blazor WASM page patterns using MudBlazor components for data grids, dialogs, and forms.

**Packages**: MudBlazor

**Key Patterns**:
- MudDataGrid with ServerData for server-side pagination
- MudDialog for create/edit forms
- Loading states and error handling
- Injection of Gateway facade

**Detection**: Grep for `MudDataGrid` or `MudDialog`
**Reference**: Internal control panel patterns

---

### `microservice/cp-filter-model` (#62) — QueryStringBindable Filters

**Purpose**: URL-synchronized filter state for data grids. Filter changes update the URL, and URL changes update filters.

**Packages**: Microsoft.AspNetCore.WebUtilities

**Key Patterns**:
- QueryStringBindable base class
- Two-way binding: filter ↔ URL query string
- PropertyChanged notification for UI update
- Debounce for text search fields

**Code Example**:
```csharp
public sealed class OrderFilter : QueryStringBindable
{
    public string? Search { get; set; }
    public int Page { get; set; } = 1;
    public int PageSize { get; set; } = 20;
    public string? SortBy { get; set; }
}
```

**Detection**: Grep for `QueryStringBindable`
**Reference**: Internal control panel patterns

---

### `microservice/cp-services` (#63) — Module Registration

**Purpose**: Service registration pattern for control panel modules: menu items, API clients, and page routing.

**Packages**: MudBlazor, Microsoft.Extensions.DependencyInjection

**Key Patterns**:
- `AddOrderModule()` extension method
- Register gateway facade as scoped HttpClient
- Add navigation menu items
- Module-level service configuration

**Detection**: Grep for `Add*Module()` extension methods
**Reference**: Internal control panel patterns

---

## Cross-Cutting Microservice Skills

---

### `microservice/event-versioning` (#84) — Event Schema Evolution

**Purpose**: Handle event schema changes over time with versioned handlers and upcasting.

**Key Patterns**:
- Event.Version field (default: 1)
- Versioned handlers: `HandleV1`, `HandleV2`
- Upcasting: convert old event data to new schema on read
- Never delete old event fields — add new ones

**Detection**: Grep for `Version` field on events or versioned handler methods
**Reference**: `knowledge/event-versioning.md`

---

### `microservice/event-catalogue` (#85) — Per-Service Event Registry

**Purpose**: Maintain a catalogue of all events produced and consumed by each service.

**Key Patterns**:
- `event-catalogue.md` per service listing all events
- Producer/consumer mapping
- Schema documentation per event
- Updated during `/dotnet-ai.implement`

**Reference**: `knowledge/event-sourcing-flow.md`

---

### `cross-cutting/db-migrations` (#86) — EF Core Migrations

**Purpose**: Database migration patterns for CI/CD pipelines.

**Key Patterns**:
- `dotnet ef migrations add` naming convention
- Migration in CI pipeline (GitHub Actions)
- Idempotent migrations for production
- Cosmos: manual migration plan (no EF migrations)

**Reference**: Official EF Core migration docs

---

### `testing/microservice-testing` (#66) — Cross-Service Test Patterns

**Purpose**: Testing patterns specific to microservice architecture: fakers, assertion helpers, WebApplicationFactory.

**Key Patterns**:
- CustomConstructorFaker extending Bogus
- AssertEquality extension methods for comparing entities
- WebApplicationFactory with in-memory bus/db
- Full-cycle tests: command → event → query → verify

**Code Example**:
```csharp
public sealed class OrderFaker : CustomConstructorFaker<Order>
{
    public OrderFaker()
    {
        RuleFor(o => o.CustomerName, f => f.Person.FullName);
        RuleFor(o => o.Total, f => f.Finance.Amount(10, 1000));
    }
}

public static class OrderAssert
{
    public static void AssertEquality(this Order actual, Order expected)
    {
        Assert.Equal(expected.Id, actual.Id);
        Assert.Equal(expected.CustomerName, actual.CustomerName);
        Assert.Equal(expected.Total, actual.Total);
    }
}
```

**Detection**: Grep for `CustomConstructorFaker` or `AssertEquality`
**Reference**: `knowledge/testing-patterns.md`

---

### `devops/k8s-manifest` (#69) — Kubernetes Deployment

**Purpose**: K8s manifest generation per environment with token placeholders.

**Key Patterns**:
- `{env}-manifest.yaml` naming (dev-manifest.yaml, prod-manifest.yaml)
- Deployment, Service, ConfigMap, Secret resources
- Token placeholders: `#{IMAGE_TAG}#`, `#{DB_CONNECTION}#`
- Health check probes (/health/ready, /health/live)

**Reference**: `knowledge/deployment-patterns.md`

---

### `devops/github-actions` (#70) — CI/CD Pipeline

**Purpose**: GitHub Actions workflow for build, test, push to ACR, and deploy to AKS.

**Key Patterns**:
- Build + test on PR
- Push Docker image to Azure Container Registry
- Deploy to AKS via kubectl with manifest token replacement
- Environment secrets per deployment stage
- OIDC authentication to Azure

**Reference**: `knowledge/deployment-patterns.md`

---

### `devops/aspire` (#71) — .NET Aspire

**Purpose**: .NET Aspire service orchestration for local development.

**Key Patterns**:
- AppHost with service defaults
- Local development with Aspire dashboard
- Service discovery via Aspire
- Resource provisioning (SQL, Cosmos, Service Bus emulator)

**Reference**: Official .NET Aspire docs

---

## Appendix: Skill-to-Agent Mapping

| Agent | Skills Loaded |
|-------|--------------|
| command-architect | #33-38 (command side) + #84, #85 (event versioning, catalogue) |
| query-architect | #39-43 (query side) + #84 (event versioning) |
| cosmos-architect | #44-47 (cosmos) + #85 (event catalogue) |
| processor-architect | #48-51 (processor) + #84 (event versioning) |
| gateway-architect | #55-58 (gateway) + #86 (rate limiting) |
| controlpanel-architect | #59-63 (control panel) |
| test-engineer | #64-67 (testing) + #87 (performance testing) |
| devops-engineer | #68-72 (devops) + #85, #91 (db-migrations, feature-flags) |
| docs-engineer | #94-101 (documentation) |
