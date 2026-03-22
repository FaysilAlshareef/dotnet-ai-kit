---
name: dotnet-ai-db-transactions
description: >
  Database transaction management, isolation levels, EF Core transactions,
  and cross-context coordination patterns.
  Trigger: transaction, isolation level, SaveChanges, commit, rollback.
category: data
agent: ef-specialist
---

# Database Transactions

## Core Principles

- EF Core `SaveChanges` is already a transaction — one call saves atomically
- Use explicit transactions only when coordinating multiple SaveChanges or operations
- Choose isolation levels based on consistency vs performance tradeoffs
- Avoid distributed transactions — use eventual consistency patterns instead
- Pipeline behavior is the cleanest way to wrap handlers in transactions

## Patterns

### Implicit Transaction (Default)

```csharp
// SaveChangesAsync wraps all tracked changes in a single transaction
internal sealed class CreateOrderHandler(
    IOrderRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateOrderCommand, Result<Guid>>
{
    public async Task<Result<Guid>> Handle(
        CreateOrderCommand request, CancellationToken ct)
    {
        var order = Order.Create(request.CustomerName);
        repository.Add(order);

        // All changes saved atomically — no explicit transaction needed
        await unitOfWork.SaveChangesAsync(ct);
        return Result<Guid>.Success(order.Id);
    }
}
```

### Explicit Transaction (Multiple Operations)

```csharp
internal sealed class TransferOrderHandler(AppDbContext db)
    : IRequestHandler<TransferOrderCommand, Result>
{
    public async Task<Result> Handle(
        TransferOrderCommand request, CancellationToken ct)
    {
        await using var transaction =
            await db.Database.BeginTransactionAsync(ct);

        try
        {
            // Operation 1: debit source
            var source = await db.Accounts.FindAsync(
                [request.SourceId], ct);
            source!.Debit(request.Amount);
            await db.SaveChangesAsync(ct);

            // Operation 2: credit destination
            var destination = await db.Accounts.FindAsync(
                [request.DestinationId], ct);
            destination!.Credit(request.Amount);
            await db.SaveChangesAsync(ct);

            await transaction.CommitAsync(ct);
            return Result.Success();
        }
        catch
        {
            await transaction.RollbackAsync(ct);
            throw;
        }
    }
}
```

### Transaction Pipeline Behavior

```csharp
// Marker interface for commands needing transactions
public interface ITransactionalRequest { }

public sealed record TransferOrderCommand(
    Guid SourceId, Guid DestinationId, decimal Amount)
    : IRequest<Result>, ITransactionalRequest;

// Pipeline behavior
public sealed class TransactionBehavior<TRequest, TResponse>(
    AppDbContext db,
    ILogger<TransactionBehavior<TRequest, TResponse>> logger)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : ITransactionalRequest
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken ct)
    {
        var typeName = typeof(TRequest).Name;
        logger.LogInformation(
            "Begin transaction for {RequestName}", typeName);

        await using var transaction =
            await db.Database.BeginTransactionAsync(ct);

        try
        {
            var response = await next();
            await transaction.CommitAsync(ct);

            logger.LogInformation(
                "Committed transaction for {RequestName}", typeName);
            return response;
        }
        catch (Exception ex)
        {
            await transaction.RollbackAsync(ct);
            logger.LogError(ex,
                "Rolled back transaction for {RequestName}", typeName);
            throw;
        }
    }
}

// Registration
services.AddMediatR(cfg =>
{
    cfg.AddBehavior(typeof(IPipelineBehavior<,>),
        typeof(TransactionBehavior<,>));
});
```

### Isolation Levels

```csharp
// Read Committed (default) — good for most scenarios
await using var transaction = await db.Database
    .BeginTransactionAsync(IsolationLevel.ReadCommitted, ct);

// Serializable — strongest consistency, lowest concurrency
await using var transaction = await db.Database
    .BeginTransactionAsync(IsolationLevel.Serializable, ct);

// Snapshot — optimistic, no blocking reads (SQL Server)
await using var transaction = await db.Database
    .BeginTransactionAsync(IsolationLevel.Snapshot, ct);
```

### Concurrency with Row Version

```csharp
// Entity with row version
public sealed class Order
{
    public Guid Id { get; set; }
    public byte[] RowVersion { get; set; } = default!;
}

// Configuration
builder.Property(o => o.RowVersion).IsRowVersion();

// Handling concurrency conflict
try
{
    await db.SaveChangesAsync(ct);
}
catch (DbUpdateConcurrencyException ex)
{
    var entry = ex.Entries.Single();
    var dbValues = await entry.GetDatabaseValuesAsync(ct);

    if (dbValues is null)
        return Result.Failure(
            Error.Conflict("Order.Deleted",
                "Order was deleted by another user"));

    // Client wins: force overwrite
    entry.OriginalValues.SetValues(dbValues);
    await db.SaveChangesAsync(ct);

    // Or: Database wins: reload and return conflict
    // return Result.Failure(Error.Conflict(...));
}
```

### Execution Strategy with Manual Transaction

```csharp
// When using EnableRetryOnFailure, manual transactions need
// an execution strategy wrapper
var strategy = db.Database.CreateExecutionStrategy();

await strategy.ExecuteAsync(async () =>
{
    await using var transaction =
        await db.Database.BeginTransactionAsync(ct);

    // Operations...
    await db.SaveChangesAsync(ct);
    await transaction.CommitAsync(ct);
});
```

### Cross-Context Coordination

```csharp
// Share a connection for transactions across DbContexts
// (same database, different schemas / modules)
var connection = db1.Database.GetDbConnection();
await connection.OpenAsync(ct);

await using var transaction = await connection.BeginTransactionAsync(ct);

db1.Database.UseTransaction(transaction as DbTransaction);
db2.Database.UseTransaction(transaction as DbTransaction);

await db1.SaveChangesAsync(ct);
await db2.SaveChangesAsync(ct);
await transaction.CommitAsync(ct);
```

## Isolation Level Guide

| Level | Dirty Reads | Non-Repeatable | Phantoms | Use Case |
|-------|-------------|---------------|----------|----------|
| Read Uncommitted | Yes | Yes | Yes | Reporting only |
| Read Committed | No | Yes | Yes | Default, general use |
| Repeatable Read | No | No | Yes | Account balances |
| Snapshot | No | No | No | Read-heavy with consistency |
| Serializable | No | No | No | Financial transactions |

## Anti-Patterns

- Wrapping every handler in a transaction (SaveChanges is already atomic)
- Long-running transactions that hold locks
- Distributed transactions across services (use eventual consistency)
- Ignoring `DbUpdateConcurrencyException`
- Not using execution strategy wrapper with retry-on-failure

## Detect Existing Patterns

1. Search for `BeginTransactionAsync` usage
2. Look for `ITransactionalRequest` or similar marker interfaces
3. Check for `DbUpdateConcurrencyException` handling
4. Look for `IsRowVersion()` in entity configurations
5. Search for `CreateExecutionStrategy()` usage

## Adding to Existing Project

1. **Rely on implicit transactions** for single SaveChanges operations
2. **Add transaction behavior** for commands needing multi-step atomicity
3. **Add concurrency tokens** to entities with concurrent update risk
4. **Handle `DbUpdateConcurrencyException`** with retry or conflict response
5. **Wrap manual transactions** in execution strategy when using retry

## References

- https://learn.microsoft.com/en-us/ef/core/saving/transactions
- https://learn.microsoft.com/en-us/ef/core/saving/concurrency
