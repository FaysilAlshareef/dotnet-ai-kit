---
name: dotnet-ai-polly-resilience
description: >
  Polly v8 resilience pipelines with Microsoft.Extensions.Http.Resilience.
  Retry, timeout, fallback, hedging, and composable strategies.
  Trigger: Polly, resilience, resilience pipeline, HTTP resilience, fault tolerance.
category: resilience
agent: api-designer
---

# Polly Resilience Pipelines

## Core Principles

- Use `Microsoft.Extensions.Http.Resilience` for HTTP client resilience (Polly v8)
- Start with `AddStandardResilienceHandler()` for sensible defaults
- Compose strategies: retry + circuit breaker + timeout in a single pipeline
- Use named pipelines for different downstream service requirements
- Integrate with telemetry for observability of resilience events

## Patterns

### Standard HTTP Resilience (Recommended Starting Point)

```csharp
// Applies retry + circuit breaker + total timeout out of the box
builder.Services.AddHttpClient("OrdersApi", client =>
{
    client.BaseAddress = new Uri("https://api.orders.{Company}.com");
})
.AddStandardResilienceHandler();
```

### Custom HTTP Resilience Pipeline

```csharp
builder.Services.AddHttpClient("PaymentGateway", client =>
{
    client.BaseAddress = new Uri("https://payments.example.com");
})
.AddResilienceHandler("payment-pipeline", pipeline =>
{
    // Retry with exponential backoff + jitter
    pipeline.AddRetry(new HttpRetryStrategyOptions
    {
        MaxRetryAttempts = 3,
        Delay = TimeSpan.FromMilliseconds(500),
        BackoffType = DelayBackoffType.Exponential,
        UseJitter = true,
        ShouldHandle = new PredicateBuilder<HttpResponseMessage>()
            .HandleResult(r =>
                r.StatusCode == HttpStatusCode.TooManyRequests ||
                r.StatusCode >= HttpStatusCode.InternalServerError)
    });

    // Circuit breaker
    pipeline.AddCircuitBreaker(new HttpCircuitBreakerStrategyOptions
    {
        FailureRatio = 0.5,
        SamplingDuration = TimeSpan.FromSeconds(30),
        MinimumThroughput = 10,
        BreakDuration = TimeSpan.FromSeconds(15)
    });

    // Timeout per attempt
    pipeline.AddTimeout(TimeSpan.FromSeconds(5));
});
```

### Non-HTTP Resilience Pipeline

```csharp
// For database, message queue, or other non-HTTP operations
builder.Services.AddResiliencePipeline("database-retry", pipeline =>
{
    pipeline
        .AddRetry(new RetryStrategyOptions
        {
            MaxRetryAttempts = 3,
            Delay = TimeSpan.FromSeconds(1),
            BackoffType = DelayBackoffType.Exponential,
            ShouldHandle = new PredicateBuilder()
                .Handle<SqlException>()
                .Handle<TimeoutException>()
        })
        .AddTimeout(TimeSpan.FromSeconds(30));
});

// Consuming via DI
public sealed class DataService(
    [FromKeyedServices("database-retry")] ResiliencePipeline pipeline,
    IDbConnectionFactory connectionFactory)
{
    public async Task<Order?> GetOrderAsync(
        Guid id, CancellationToken ct)
    {
        return await pipeline.ExecuteAsync(async token =>
        {
            using var conn = connectionFactory.CreateConnection();
            return await conn.QuerySingleOrDefaultAsync<Order>(
                "SELECT * FROM Orders WHERE Id = @Id",
                new { Id = id });
        }, ct);
    }
}
```

### Typed Resilience Pipeline

```csharp
// Pipeline with typed result
builder.Services.AddResiliencePipeline<string, HttpResponseMessage>(
    "external-api", pipeline =>
{
    pipeline
        .AddRetry(new RetryStrategyOptions<HttpResponseMessage>
        {
            MaxRetryAttempts = 2,
            ShouldHandle = new PredicateBuilder<HttpResponseMessage>()
                .HandleResult(r => !r.IsSuccessStatusCode)
        })
        .AddTimeout(TimeSpan.FromSeconds(10));
});
```

### Fallback Strategy

```csharp
builder.Services.AddResiliencePipeline<string, OrderResponse?>(
    "order-with-fallback", pipeline =>
{
    pipeline
        .AddFallback(new FallbackStrategyOptions<OrderResponse?>
        {
            FallbackAction = _ =>
                Outcome.FromResultAsValueTask<OrderResponse?>(null),
            ShouldHandle = new PredicateBuilder<OrderResponse?>()
                .Handle<HttpRequestException>()
                .Handle<TimeoutRejectedException>()
        })
        .AddRetry(new RetryStrategyOptions<OrderResponse?>
        {
            MaxRetryAttempts = 2
        })
        .AddTimeout(TimeSpan.FromSeconds(5));
});
```

### Hedging Strategy

```csharp
// Send parallel requests to reduce tail latency
builder.Services.AddHttpClient("search-api")
    .AddResilienceHandler("hedging", pipeline =>
    {
        pipeline.AddHedging(new HttpHedgingStrategyOptions
        {
            MaxHedgedAttempts = 2,
            Delay = TimeSpan.FromMilliseconds(200)
        });
    });
```

## Pipeline Execution Order

```
Request → Fallback → Retry → Circuit Breaker → Timeout → HTTP Call
                                                            ↓
                                                         Response
```

Strategies execute from outermost (first added) to innermost (last added).

## Anti-Patterns

- Retrying non-idempotent operations (POST without idempotency key)
- No jitter on retry delay (thundering herd problem)
- Infinite or very high retry counts
- Missing timeout (request hangs forever)
- Circuit breaker with too-low threshold (opens too easily)
- Using Polly v7 syntax with v8 packages

## Detect Existing Patterns

1. Search for `Microsoft.Extensions.Http.Resilience` package
2. Look for `AddStandardResilienceHandler` calls
3. Check for `AddResilienceHandler` or `AddResiliencePipeline` calls
4. Search for old `Polly` package (v7 — migration candidate)
5. Look for `ResiliencePipeline` injection

## Adding to Existing Project

1. **Install** `Microsoft.Extensions.Http.Resilience`
2. **Add standard resilience** to all HTTP clients as baseline
3. **Customize per client** with specific retry/timeout settings
4. **Add non-HTTP pipelines** for database and messaging operations
5. **Add fallback** for graceful degradation of non-critical services
6. **Monitor** resilience events through logging and OpenTelemetry

## Decision Guide

| Strategy | Use When |
|----------|----------|
| Standard resilience handler | Default for all HTTP clients |
| Custom retry | Specific error codes or delay requirements |
| Circuit breaker | Downstream service prone to cascading failure |
| Timeout | Preventing indefinite waits |
| Fallback | Returning cached/default data when service is down |
| Hedging | Latency-sensitive operations with redundant backends |

## References

- https://learn.microsoft.com/en-us/dotnet/core/resilience/
- https://www.pollydocs.org/
