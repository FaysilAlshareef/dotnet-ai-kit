---
name: pipeline-behaviors
description: >
  MediatR pipeline behaviors for validation, logging, performance monitoring,
  and transaction management.
  Trigger: pipeline behavior, IPipelineBehavior, validation behavior, logging behavior.
category: cqrs
agent: ef-specialist
---

# Pipeline Behaviors

## Core Principles

- Pipeline behaviors wrap every MediatR request like middleware
- Registration order matters: first registered = outermost in the pipeline
- Use open generic registration so behaviors apply to all requests
- Constrain behaviors with marker interfaces when needed
- Common behaviors: validation, logging, performance, transaction

## Patterns

### Validation Behavior

```csharp
public sealed class ValidationBehavior<TRequest, TResponse>(
    IEnumerable<IValidator<TRequest>> validators)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : notnull
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken ct)
    {
        if (!validators.Any())
            return await next();

        var context = new ValidationContext<TRequest>(request);

        var results = await Task.WhenAll(
            validators.Select(v => v.ValidateAsync(context, ct)));

        var failures = results
            .SelectMany(r => r.Errors)
            .Where(f => f is not null)
            .ToList();

        if (failures.Count != 0)
            throw new ValidationException(failures);

        return await next();
    }
}
```

### Logging Behavior

```csharp
public sealed class LoggingBehavior<TRequest, TResponse>(
    ILogger<LoggingBehavior<TRequest, TResponse>> logger)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : notnull
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken ct)
    {
        var requestName = typeof(TRequest).Name;

        logger.LogInformation(
            "Handling {RequestName}: {@Request}",
            requestName, request);

        var sw = Stopwatch.StartNew();
        var response = await next();
        sw.Stop();

        if (sw.ElapsedMilliseconds > 500)
        {
            logger.LogWarning(
                "Long-running request {RequestName}: {ElapsedMs}ms",
                requestName, sw.ElapsedMilliseconds);
        }
        else
        {
            logger.LogInformation(
                "Handled {RequestName} in {ElapsedMs}ms",
                requestName, sw.ElapsedMilliseconds);
        }

        return response;
    }
}
```

### Performance Behavior

```csharp
public sealed class PerformanceBehavior<TRequest, TResponse>(
    ILogger<PerformanceBehavior<TRequest, TResponse>> logger)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : notnull
{
    private const int ThresholdMs = 500;

    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken ct)
    {
        var sw = Stopwatch.StartNew();
        var response = await next();
        sw.Stop();

        if (sw.ElapsedMilliseconds > ThresholdMs)
        {
            logger.LogWarning(
                "Slow request detected: {RequestName} took {ElapsedMs}ms. " +
                "Request: {@Request}",
                typeof(TRequest).Name,
                sw.ElapsedMilliseconds,
                request);
        }

        return response;
    }
}
```

### Transaction Behavior

```csharp
// Marker interface for transactional commands
public interface ITransactionalRequest { }

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
        var strategy = db.Database.CreateExecutionStrategy();

        return await strategy.ExecuteAsync(async () =>
        {
            await using var transaction =
                await db.Database.BeginTransactionAsync(ct);

            logger.LogInformation(
                "Begin transaction for {RequestName}",
                typeof(TRequest).Name);

            var response = await next();
            await transaction.CommitAsync(ct);

            logger.LogInformation(
                "Committed transaction for {RequestName}",
                typeof(TRequest).Name);

            return response;
        });
    }
}
```

### Unhandled Exception Behavior

```csharp
public sealed class UnhandledExceptionBehavior<TRequest, TResponse>(
    ILogger<UnhandledExceptionBehavior<TRequest, TResponse>> logger)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : notnull
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken ct)
    {
        try
        {
            return await next();
        }
        catch (Exception ex)
        {
            logger.LogError(ex,
                "Unhandled exception for {RequestName}: {@Request}",
                typeof(TRequest).Name, request);
            throw;
        }
    }
}
```

### Registration (Order Matters)

```csharp
builder.Services.AddMediatR(cfg =>
{
    cfg.RegisterServicesFromAssembly(typeof(Program).Assembly);

    // Outermost → innermost
    cfg.AddBehavior(typeof(IPipelineBehavior<,>),
        typeof(UnhandledExceptionBehavior<,>));
    cfg.AddBehavior(typeof(IPipelineBehavior<,>),
        typeof(LoggingBehavior<,>));
    cfg.AddBehavior(typeof(IPipelineBehavior<,>),
        typeof(ValidationBehavior<,>));
    cfg.AddBehavior(typeof(IPipelineBehavior<,>),
        typeof(PerformanceBehavior<,>));
    cfg.AddBehavior(typeof(IPipelineBehavior<,>),
        typeof(TransactionBehavior<,>));
});

// Register validators
builder.Services.AddValidatorsFromAssembly(
    typeof(Program).Assembly);
```

### Pipeline Flow

```
Request arrives
  → UnhandledExceptionBehavior (catch + log)
    → LoggingBehavior (log entry/exit + timing)
      → ValidationBehavior (FluentValidation)
        → PerformanceBehavior (warn if slow)
          → TransactionBehavior (if ITransactionalRequest)
            → Handler (actual business logic)
```

## Anti-Patterns

- Registering behaviors in wrong order (logging should be before validation)
- Behavior that modifies the request (behaviors are for cross-cutting, not logic)
- Transaction behavior on all requests (use marker interface for opt-in)
- Swallowing exceptions in behaviors (always re-throw)
- Heavy computation in behaviors (keep them lightweight)

## Detect Existing Patterns

1. Search for `IPipelineBehavior<` implementations
2. Look for `AddBehavior` calls in MediatR registration
3. Check for `Behaviors/` folder in the project
4. Look for `ITransactionalRequest` or similar marker interfaces
5. Search for `ValidationBehavior` or `LoggingBehavior` classes

## Adding to Existing Project

1. **Create behaviors** — start with validation and logging
2. **Register in correct order** — exception → logging → validation → transaction
3. **Add marker interfaces** for opt-in behaviors (e.g., `ITransactionalRequest`)
4. **Install FluentValidation** for the validation behavior
5. **Test behavior ordering** — verify logging captures validation failures

## References

- https://github.com/jbogard/MediatR/wiki/Behaviors
- https://docs.fluentvalidation.net/en/latest/aspnet.html
