---
name: async-patterns
description: >
  Async/await best practices, CancellationToken propagation, Task patterns,
  ValueTask usage, and common async pitfalls.
  Trigger: async, await, Task, CancellationToken, concurrency.
metadata:
  category: core
  agent: dotnet-architect
  alwaysApply: true
---

# Async/Await Best Practices

## Core Principles

- Always propagate `CancellationToken` through the call chain
- Use `async`/`await` throughout — do not mix blocking and async code
- Prefer `ValueTask<T>` for hot paths that often complete synchronously
- Use `ConfigureAwait(false)` in library code, not in ASP.NET Core app code
- Never use `async void` except for event handlers
- Avoid capturing context unnecessarily

## Patterns

### CancellationToken Propagation

```csharp
// Always accept and forward CancellationToken
public sealed class OrderService(
    IOrderRepository repository,
    ILogger<OrderService> logger)
{
    public async Task<Order?> GetOrderAsync(Guid id, CancellationToken ct)
    {
        logger.LogInformation("Fetching order {OrderId}", id);
        return await repository.FindAsync(id, ct);
    }

    public async Task<List<Order>> GetOrdersAsync(
        OrderFilter filter, CancellationToken ct)
    {
        var orders = await repository.ListAsync(filter, ct);
        return orders;
    }
}

// Controller / endpoint — ct comes from framework
app.MapGet("/orders/{id}", async (
    Guid id, ISender sender, CancellationToken ct) =>
{
    var result = await sender.Send(new GetOrderQuery(id), ct);
    return result is not null ? Results.Ok(result) : Results.NotFound();
});
```

### Parallel Operations with Task.WhenAll

```csharp
public async Task<DashboardData> GetDashboardAsync(CancellationToken ct)
{
    // Run independent queries in parallel
    var ordersTask = _orderRepository.GetRecentAsync(10, ct);
    var statsTask = _statsService.GetSummaryAsync(ct);
    var alertsTask = _alertService.GetActiveAsync(ct);

    await Task.WhenAll(ordersTask, statsTask, alertsTask);

    return new DashboardData(
        Orders: ordersTask.Result,
        Stats: statsTask.Result,
        Alerts: alertsTask.Result);
}
```

### ValueTask for Hot Paths

```csharp
// Use ValueTask when result is often cached / synchronous
public ValueTask<Product?> GetProductAsync(Guid id, CancellationToken ct)
{
    if (_cache.TryGetValue(id, out Product? cached))
        return ValueTask.FromResult(cached);

    return LoadFromDatabaseAsync(id, ct);
}

private async ValueTask<Product?> LoadFromDatabaseAsync(
    Guid id, CancellationToken ct)
{
    var product = await _repository.FindAsync(id, ct);
    if (product is not null)
        _cache.Set(id, product, TimeSpan.FromMinutes(5));
    return product;
}
```

### Async Enumerable for Streaming

```csharp
// IAsyncEnumerable for large datasets
public async IAsyncEnumerable<OrderResponse> StreamOrdersAsync(
    [EnumeratorCancellation] CancellationToken ct)
{
    await foreach (var order in _repository.StreamAllAsync(ct))
    {
        yield return order.ToResponse();
    }
}

// Consuming
await foreach (var order in service.StreamOrdersAsync(ct))
{
    await ProcessOrderAsync(order, ct);
}
```

### Async Initialization with SemaphoreSlim

```csharp
public sealed class ExpensiveResourceService : IAsyncDisposable
{
    private readonly SemaphoreSlim _initLock = new(1, 1);
    private ExpensiveResource? _resource;

    public async Task<ExpensiveResource> GetResourceAsync(CancellationToken ct)
    {
        if (_resource is not null)
            return _resource;

        await _initLock.WaitAsync(ct);
        try
        {
            // Double-check after acquiring lock
            _resource ??= await ExpensiveResource.CreateAsync(ct);
            return _resource;
        }
        finally
        {
            _initLock.Release();
        }
    }

    public async ValueTask DisposeAsync()
    {
        _initLock.Dispose();
        if (_resource is not null)
            await _resource.DisposeAsync();
    }
}
```

### Timeout with CancellationToken

```csharp
public async Task<Result<OrderResponse>> ProcessOrderAsync(
    Guid orderId, CancellationToken ct)
{
    // Create a linked token with timeout
    using var timeoutCts = CancellationTokenSource
        .CreateLinkedTokenSource(ct);
    timeoutCts.CancelAfter(TimeSpan.FromSeconds(30));

    try
    {
        var order = await _repository.FindAsync(orderId, timeoutCts.Token);
        if (order is null)
            return Result<OrderResponse>.Failure(
                Error.NotFound("Order.NotFound", "Order not found"));

        await _processor.ProcessAsync(order, timeoutCts.Token);
        return Result<OrderResponse>.Success(order.ToResponse());
    }
    catch (OperationCanceledException) when (!ct.IsCancellationRequested)
    {
        // Timeout occurred, not caller cancellation
        return Result<OrderResponse>.Failure(
            Error.Unexpected("Order.Timeout", "Order processing timed out"));
    }
}
```

### Background Service Scoped Work

```csharp
public sealed class OrderProcessorService(
    IServiceScopeFactory scopeFactory,
    ILogger<OrderProcessorService> logger) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                // Create a scope for each unit of work
                using var scope = scopeFactory.CreateScope();
                var processor = scope.ServiceProvider
                    .GetRequiredService<IOrderProcessor>();

                await processor.ProcessPendingOrdersAsync(stoppingToken);
            }
            catch (Exception ex) when (ex is not OperationCanceledException)
            {
                logger.LogError(ex, "Error processing orders");
            }

            await Task.Delay(TimeSpan.FromSeconds(30), stoppingToken);
        }
    }
}
```

### Channel for Producer/Consumer

```csharp
public sealed class OrderChannel
{
    private readonly Channel<OrderEvent> _channel =
        Channel.CreateBounded<OrderEvent>(new BoundedChannelOptions(1000)
        {
            FullMode = BoundedChannelFullMode.Wait,
            SingleReader = false,
            SingleWriter = false
        });

    public ChannelWriter<OrderEvent> Writer => _channel.Writer;
    public ChannelReader<OrderEvent> Reader => _channel.Reader;
}
```

## Anti-Patterns

```csharp
// BAD: async void — exceptions are unobservable
async void ProcessOrder(Order order) { }

// BAD: blocking on async code — can deadlock
var result = GetOrderAsync(id).Result;
var result2 = GetOrderAsync(id).GetAwaiter().GetResult();

// BAD: not propagating CancellationToken
public async Task<Order?> GetAsync(Guid id)
{
    return await _repository.FindAsync(id); // missing ct!
}

// BAD: unnecessary async state machine
public async Task<Order?> GetAsync(Guid id, CancellationToken ct)
{
    return await _repository.FindAsync(id, ct); // just return the Task
}

// GOOD: elide async when simply forwarding
public Task<Order?> GetAsync(Guid id, CancellationToken ct)
    => _repository.FindAsync(id, ct);

// BAD: Task.Run in ASP.NET Core (steals thread pool thread)
await Task.Run(() => ComputeExpensiveSync());
```

## Detect Existing Patterns

1. Search for `async Task` and `async ValueTask` method signatures
2. Check if `CancellationToken` is accepted and forwarded consistently
3. Look for `.Result` or `.GetAwaiter().GetResult()` blocking calls
4. Search for `async void` methods (should only be event handlers)
5. Check for `ConfigureAwait(false)` usage patterns (library vs app code)
6. Look for `Task.Run` usage in ASP.NET Core request handlers

## Adding to Existing Project

1. **Audit CancellationToken propagation** — add `ct` parameter to all async methods
2. **Replace blocking calls** — find `.Result` and `.Wait()` calls and convert to `await`
3. **Add cancellation to endpoints** — ensure all controller actions accept `CancellationToken`
4. **Review background services** — ensure proper scope creation with `IServiceScopeFactory`
5. **Check for fire-and-forget** — replace `_ = DoAsync()` with proper background processing

## Decision Guide

| Scenario | Recommendation |
|----------|---------------|
| Return type | `Task<T>` for most cases, `ValueTask<T>` for hot paths |
| Multiple independent calls | `Task.WhenAll` for parallel execution |
| Large result sets | `IAsyncEnumerable<T>` for streaming |
| Background work in web app | `BackgroundService` with `IServiceScopeFactory` |
| Thread-safe lazy init | `SemaphoreSlim` with double-check pattern |
| Producer/consumer queue | `System.Threading.Channels` |
| Timeout | `CancellationTokenSource.CreateLinkedTokenSource` + `CancelAfter` |

## References

- https://learn.microsoft.com/en-us/dotnet/csharp/asynchronous-programming/
- https://devblogs.microsoft.com/dotnet/configureawait-faq/
- https://learn.microsoft.com/en-us/dotnet/standard/asynchronous-programming-patterns/
