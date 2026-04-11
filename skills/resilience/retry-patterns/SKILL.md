---
name: retry-patterns
description: >
  Use when implementing retry logic with exponential backoff and jitter.
metadata:
  category: resilience
  agent: api-designer
  when-to-use: "When implementing retry patterns with exponential backoff and jitter"
---

# Retry Patterns

## Core Principles

- Retry only transient failures — not business errors or 4xx responses
- Always use exponential backoff to avoid overwhelming recovering services
- Add jitter to prevent thundering herd when multiple clients retry simultaneously
- Set a maximum retry count to avoid infinite loops
- Only retry idempotent operations safely; non-idempotent requires idempotency keys

## Patterns

### HTTP Retry with Exponential Backoff + Jitter

```csharp
builder.Services.AddHttpClient("OrdersApi", client =>
{
    client.BaseAddress = new Uri("https://api.orders.{Company}.com");
})
.AddResilienceHandler("retry-pipeline", pipeline =>
{
    pipeline.AddRetry(new HttpRetryStrategyOptions
    {
        MaxRetryAttempts = 3,
        Delay = TimeSpan.FromMilliseconds(500),
        BackoffType = DelayBackoffType.Exponential,
        UseJitter = true,  // Adds randomness to prevent thundering herd
        ShouldHandle = new PredicateBuilder<HttpResponseMessage>()
            .HandleResult(r =>
                r.StatusCode == HttpStatusCode.TooManyRequests ||
                r.StatusCode == HttpStatusCode.ServiceUnavailable ||
                r.StatusCode >= HttpStatusCode.InternalServerError)
            .Handle<HttpRequestException>()
            .Handle<TimeoutRejectedException>()
    });
});
```

### Retry with Respect for Retry-After Header

```csharp
pipeline.AddRetry(new HttpRetryStrategyOptions
{
    MaxRetryAttempts = 3,
    DelayGenerator = args =>
    {
        // Respect Retry-After header from server
        if (args.Outcome.Result?.Headers.RetryAfter is { } retryAfter)
        {
            var delay = retryAfter.Delta
                ?? (retryAfter.Date.HasValue
                    ? retryAfter.Date.Value - DateTimeOffset.UtcNow
                    : TimeSpan.FromSeconds(1));

            return ValueTask.FromResult<TimeSpan?>(delay);
        }

        // Default exponential backoff
        return ValueTask.FromResult<TimeSpan?>(
            TimeSpan.FromSeconds(Math.Pow(2, args.AttemptNumber)));
    },
    ShouldHandle = new PredicateBuilder<HttpResponseMessage>()
        .HandleResult(r =>
            r.StatusCode == HttpStatusCode.TooManyRequests ||
            r.StatusCode >= HttpStatusCode.InternalServerError)
});
```

### Database Retry

```csharp
// EF Core built-in retry
options.UseSqlServer(connectionString, sql =>
{
    sql.EnableRetryOnFailure(
        maxRetryCount: 3,
        maxRetryDelay: TimeSpan.FromSeconds(5),
        errorNumbersToAdd: null); // null = retry all transient errors
});

// Custom retry with Polly for non-EF operations
builder.Services.AddResiliencePipeline("db-operation", pipeline =>
{
    pipeline.AddRetry(new RetryStrategyOptions
    {
        MaxRetryAttempts = 3,
        Delay = TimeSpan.FromMilliseconds(200),
        BackoffType = DelayBackoffType.Exponential,
        UseJitter = true,
        ShouldHandle = new PredicateBuilder()
            .Handle<SqlException>(ex => ex.IsTransient)
            .Handle<TimeoutException>()
    });
});
```

### Retry with Logging

```csharp
pipeline.AddRetry(new HttpRetryStrategyOptions
{
    MaxRetryAttempts = 3,
    Delay = TimeSpan.FromMilliseconds(500),
    BackoffType = DelayBackoffType.Exponential,
    UseJitter = true,
    OnRetry = args =>
    {
        var logger = args.Context.Properties.GetValue(
            new ResiliencePropertyKey<ILogger>("logger"), null!);

        logger?.LogWarning(
            "Retry attempt {AttemptNumber} after {Delay}ms. " +
            "Reason: {Reason}",
            args.AttemptNumber,
            args.RetryDelay.TotalMilliseconds,
            args.Outcome.Exception?.Message ??
                args.Outcome.Result?.StatusCode.ToString());

        return ValueTask.CompletedTask;
    }
});
```

### Non-HTTP Retry (Generic)

```csharp
builder.Services.AddResiliencePipeline("message-queue", pipeline =>
{
    pipeline.AddRetry(new RetryStrategyOptions
    {
        MaxRetryAttempts = 5,
        Delay = TimeSpan.FromSeconds(1),
        BackoffType = DelayBackoffType.Exponential,
        UseJitter = true,
        MaxDelay = TimeSpan.FromSeconds(30), // cap max delay
        ShouldHandle = new PredicateBuilder()
            .Handle<MessageQueueException>()
            .Handle<TimeoutException>()
    });
});

// Usage
public sealed class MessagePublisher(
    [FromKeyedServices("message-queue")] ResiliencePipeline pipeline,
    IMessageBus messageBus)
{
    public async Task PublishAsync<T>(T message, CancellationToken ct)
    {
        await pipeline.ExecuteAsync(
            async token => await messageBus.SendAsync(message, token),
            ct);
    }
}
```

### Idempotency Key for Non-Idempotent Retries

```csharp
// For POST/PUT operations that create resources
public sealed class PaymentClient(HttpClient httpClient)
{
    public async Task<PaymentResult> ChargeAsync(
        ChargeRequest request, CancellationToken ct)
    {
        // Include idempotency key so retries don't duplicate charges
        var idempotencyKey = Guid.NewGuid().ToString();

        var httpRequest = new HttpRequestMessage(
            HttpMethod.Post, "/charges")
        {
            Content = JsonContent.Create(request)
        };
        httpRequest.Headers.Add(
            "Idempotency-Key", idempotencyKey);

        var response = await httpClient.SendAsync(httpRequest, ct);
        response.EnsureSuccessStatusCode();

        return await response.Content
            .ReadFromJsonAsync<PaymentResult>(ct)
            ?? throw new InvalidOperationException(
                "Empty response from payment service");
    }
}
```

## Backoff Strategy Comparison

```
Constant:     [1s] [1s] [1s] [1s]
Linear:       [1s] [2s] [3s] [4s]
Exponential:  [1s] [2s] [4s] [8s]
Exp + Jitter: [0.8s] [2.3s] [3.7s] [8.1s]  ← Recommended
```

## Anti-Patterns

- Retrying business errors (400 Bad Request, 404 Not Found)
- Retrying without backoff (constant delay hammers the service)
- No jitter on backoff (all clients retry at the same time)
- Retrying non-idempotent POST without idempotency key
- No maximum retry count (infinite retries)
- Retrying auth failures (401/403) — these won't resolve with retry

## Detect Existing Patterns

1. Search for `AddRetry` or `RetryStrategyOptions` usage
2. Look for old Polly v7 `WaitAndRetryAsync` (migration candidate)
3. Check for `EnableRetryOnFailure` in EF Core configuration
4. Search for manual retry loops (`while` / `for` with `try-catch`)
5. Look for `Idempotency-Key` header usage

## Adding to Existing Project

1. **Replace manual retry loops** with Polly resilience pipelines
2. **Add exponential backoff + jitter** to all retry strategies
3. **Configure per-client** retry based on downstream SLAs
4. **Add logging** to retry events for observability
5. **Add idempotency keys** for non-idempotent POST operations
6. **Respect Retry-After** headers from rate-limited APIs

## Decision Guide

| Scenario | Max Retries | Base Delay | Backoff |
|----------|-------------|-----------|---------|
| HTTP API call | 3 | 500ms | Exponential + jitter |
| Database connection | 3 | 200ms | Exponential + jitter |
| Message queue publish | 5 | 1s | Exponential + jitter |
| File upload | 2 | 1s | Exponential |
| Payment processing | 1-2 | 1s | Exponential (with idempotency key) |

## References

- https://learn.microsoft.com/en-us/dotnet/core/resilience/
- https://www.pollydocs.org/strategies/retry
- https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/
