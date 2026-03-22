# Concurrency Patterns

Row version, concurrency tokens, sequence-based idempotency, and optimistic concurrency patterns for .NET microservices.

---

## Overview

Concurrency control in event-sourced microservices operates at multiple levels:

1. **Aggregate level** — Sequence numbers prevent conflicting writes
2. **Database level** — Row versions detect concurrent updates
3. **Message level** — Idempotency ensures at-least-once processing is safe
4. **Cosmos DB level** — ETags provide optimistic concurrency

---

## Row Version (SQL Server)

Row version (timestamp) is an automatically incrementing binary value that changes on every update. EF Core uses it for optimistic concurrency checks.

### Entity Configuration

```csharp
public sealed class Order
{
    public Guid Id { get; private set; }
    public string CustomerName { get; private set; } = string.Empty;
    public decimal Total { get; private set; }
    public int Sequence { get; private set; }

    // SQL Server row version — auto-managed
    [Timestamp]
    public byte[] RowVersion { get; private set; } = [];
}
```

### Fluent Configuration

```csharp
public sealed class OrderConfiguration : IEntityTypeConfiguration<Order>
{
    public void Configure(EntityTypeBuilder<Order> builder)
    {
        builder.HasKey(o => o.Id);
        builder.Property(o => o.RowVersion)
            .IsRowVersion()
            .IsConcurrencyToken();
    }
}
```

### Handling Concurrency Conflicts

```csharp
public async Task UpdateOrderAsync(
    Guid orderId,
    string newCustomerName,
    CancellationToken ct)
{
    var maxRetries = 3;

    for (int attempt = 0; attempt < maxRetries; attempt++)
    {
        try
        {
            var order = await db.Orders.FindAsync([orderId], ct)
                ?? throw new NotFoundException($"Order {orderId} not found");

            order.UpdateCustomerName(newCustomerName);
            await db.SaveChangesAsync(ct);
            return;
        }
        catch (DbUpdateConcurrencyException ex)
        {
            if (attempt == maxRetries - 1)
                throw;

            // Reload entity with fresh data
            foreach (var entry in ex.Entries)
            {
                await entry.ReloadAsync(ct);
            }

            logger.LogWarning(
                "Concurrency conflict on Order {OrderId}, retrying (attempt {Attempt}/{Max})",
                orderId, attempt + 1, maxRetries);
        }
    }
}
```

---

## Concurrency Tokens

For databases without native row version support, or when you need semantic versioning.

### Integer Version Token

```csharp
public sealed class Order
{
    public Guid Id { get; private set; }
    public string CustomerName { get; private set; } = string.Empty;
    public int Version { get; private set; }

    public void UpdateCustomerName(string name, int expectedVersion)
    {
        if (Version != expectedVersion)
            throw new ConcurrencyException(
                $"Order {Id} version mismatch. Expected {expectedVersion}, actual {Version}");

        CustomerName = name;
        Version++;
    }
}
```

### EF Core Configuration

```csharp
builder.Property(o => o.Version)
    .IsConcurrencyToken();
```

### Client-Side Concurrency Check

```csharp
// API receives version from client
[HttpPut("{id}")]
public async Task<ActionResult> UpdateOrder(
    Guid id, UpdateOrderRequest request, CancellationToken ct)
{
    var order = await db.Orders.FindAsync([id], ct);
    if (order is null) return NotFound();

    // Client must send the version they read
    if (order.Version != request.Version)
        return Conflict(new ProblemDetails
        {
            Title = "Concurrency conflict",
            Detail = "The order was modified by another user. Please reload and try again.",
            Status = StatusCodes.Status409Conflict
        });

    order.UpdateCustomerName(request.CustomerName, request.Version);
    await db.SaveChangesAsync(ct);
    return Ok();
}
```

---

## Sequence-Based Idempotency

In event sourcing, the sequence number on each event provides natural idempotency for query-side handlers.

### How Sequence Checking Works

```
Command Side:                         Query Side:
  Event Seq 1 (OrderCreated)  ────▶  Handler checks: entity doesn't exist → create
  Event Seq 2 (OrderUpdated)  ────▶  Handler checks: entity.Sequence == 1 → apply
  Event Seq 2 (OrderUpdated)  ────▶  Handler checks: entity.Sequence == 2 → skip (already applied)
  Event Seq 4 (OrderShipped)  ────▶  Handler checks: entity.Sequence == 2 → retry (gap: seq 3 missing)
```

### Idempotent Event Handler

```csharp
public sealed class OrderUpdatedHandler(ApplicationDbContext db)
    : IRequestHandler<Event<OrderUpdatedData>, bool>
{
    public async Task<bool> Handle(
        Event<OrderUpdatedData> @event, CancellationToken ct)
    {
        var order = await db.Orders.FindAsync([@event.AggregateId], ct);

        // Entity not yet created — retry later (dependency not ready)
        if (order is null)
            return false;

        // Already processed this event — idempotent skip
        if (@event.Sequence <= order.Sequence)
            return true;

        // Sequence gap — out of order delivery, retry later
        if (@event.Sequence != order.Sequence + 1)
            return false;

        // Apply the event
        order.Apply(@event);
        await db.SaveChangesAsync(ct);
        return true;
    }
}
```

### Return Value Semantics

| Return Value | Meaning                      | Service Bus Action |
|-------------|------------------------------|--------------------|
| `true`      | Successfully processed       | Complete message   |
| `true`      | Already processed (skip)     | Complete message   |
| `false`     | Cannot process yet (retry)   | Abandon message    |
| Exception   | Unexpected error             | Abandon message    |

---

## Optimistic Concurrency in Cosmos DB

Cosmos DB uses ETags for optimistic concurrency control.

### ETag-Based Updates

```csharp
public async Task UpdateDocumentAsync(
    MerchantSalesReport report,
    CancellationToken ct)
{
    try
    {
        var response = await container.ReplaceItemAsync(
            report,
            report.id,
            report.PartitionKeys,
            new ItemRequestOptions { IfMatchEtag = report.ETag },
            ct);

        report.ETag = response.ETag;
    }
    catch (CosmosException ex) when (ex.StatusCode == HttpStatusCode.PreconditionFailed)
    {
        // ETag mismatch — document was modified by another process
        throw new ConcurrencyException(
            $"Document {report.id} was modified concurrently. ETag mismatch.");
    }
}
```

### Retry with Reload

```csharp
public async Task UpdateWithRetryAsync(
    string documentId,
    PartitionKey pk,
    Action<MerchantSalesReport> updateAction,
    CancellationToken ct,
    int maxRetries = 3)
{
    for (int attempt = 0; attempt < maxRetries; attempt++)
    {
        // Read latest version
        var response = await container.ReadItemAsync<MerchantSalesReport>(
            documentId, pk, cancellationToken: ct);
        var document = response.Resource;
        document.ETag = response.ETag;

        // Apply changes
        updateAction(document);

        try
        {
            await container.ReplaceItemAsync(
                document,
                documentId,
                pk,
                new ItemRequestOptions { IfMatchEtag = document.ETag },
                ct);
            return; // Success
        }
        catch (CosmosException ex) when (
            ex.StatusCode == HttpStatusCode.PreconditionFailed)
        {
            if (attempt == maxRetries - 1)
                throw;

            logger.LogWarning(
                "Cosmos concurrency conflict on {Id}, retrying ({Attempt}/{Max})",
                documentId, attempt + 1, maxRetries);
        }
    }
}
```

---

## Aggregate-Level Concurrency

The event store uses AggregateId + Sequence as a composite key, preventing duplicate events.

### Event Store Unique Constraint

```csharp
public class GenericEventConfiguration<T> : IEntityTypeConfiguration<Event<T>>
    where T : IEventData
{
    public void Configure(EntityTypeBuilder<Event<T>> builder)
    {
        // Composite key ensures no duplicate sequences per aggregate
        builder.HasKey(e => new { e.AggregateId, e.Sequence });
    }
}
```

### Handling Concurrent Aggregate Updates

```csharp
public sealed class UpdateOrderHandler(
    IEventStore<IOrderEventData> eventStore,
    ICommitEventService<IOrderEventData> commitService)
    : IRequestHandler<UpdateOrderCommand, OrderOutput>
{
    public async Task<OrderOutput> Handle(
        UpdateOrderCommand request, CancellationToken ct)
    {
        try
        {
            var events = await eventStore.GetEventsAsync(request.OrderId, ct);
            var order = new Order();
            order.LoadFromHistory(events);

            order.UpdateDetails(request.CustomerName, request.Total);

            await commitService.CommitAsync(
                order.Id, order.UncommittedEvents, ct);

            return new OrderOutput(order.Id, order.Sequence);
        }
        catch (DbUpdateException ex) when (IsDuplicateKeyException(ex))
        {
            // Another request already committed an event with this sequence
            throw new ConcurrencyException(
                $"Order {request.OrderId} was modified concurrently. " +
                "Please retry the operation.");
        }
    }

    private static bool IsDuplicateKeyException(DbUpdateException ex) =>
        ex.InnerException?.Message.Contains("duplicate key") == true ||
        ex.InnerException?.Message.Contains("unique constraint") == true;
}
```

---

## Message Deduplication

Service Bus provides built-in deduplication when `RequiresDuplicateDetection` is enabled on the topic.

### Topic Configuration

```json
{
  "Topics": {
    "{company}-order-commands": {
      "RequiresDuplicateDetection": true,
      "DuplicateDetectionHistoryTimeWindow": "PT10M"
    }
  }
}
```

### Application-Level Deduplication

For scenarios where Service Bus deduplication is not sufficient:

```csharp
public sealed class ProcessedMessageTracker(ApplicationDbContext db)
{
    public async Task<bool> IsAlreadyProcessedAsync(
        string messageId, CancellationToken ct)
    {
        return await db.ProcessedMessages
            .AnyAsync(m => m.MessageId == messageId, ct);
    }

    public async Task MarkAsProcessedAsync(
        string messageId, CancellationToken ct)
    {
        db.ProcessedMessages.Add(new ProcessedMessage
        {
            MessageId = messageId,
            ProcessedAt = DateTime.UtcNow
        });
        await db.SaveChangesAsync(ct);
    }
}
```

---

## Summary: Concurrency Strategy by Layer

| Layer           | Strategy                     | Mechanism                      |
|-----------------|------------------------------|--------------------------------|
| Command API     | Aggregate sequence           | Composite PK (AggregateId+Seq)|
| Query Handler   | Sequence-based idempotency   | Event sequence checking        |
| SQL Server      | Row version                  | `[Timestamp]` / `IsRowVersion`|
| Cosmos DB       | ETag                         | `IfMatchEtag` on operations   |
| Service Bus     | Message deduplication        | `MessageId` + dedup window    |
| REST API        | Client version check         | `Version` field in request    |

---

## Related Documents

- `knowledge/event-sourcing-flow.md` — Event flow with sequence tracking
- `knowledge/cosmos-patterns.md` — Cosmos ETag patterns
- `knowledge/dead-letter-reprocessing.md` — Retrying failed messages
