---
name: circuit-breaker
description: >
  Use when adding circuit breaker protection against cascading failures.
metadata:
  category: resilience
  agent: api-designer
  when-to-use: "When implementing circuit breaker pattern to prevent cascading failures"
---

# Circuit Breaker Pattern

## Core Principles

- Circuit breaker prevents sending requests to a failing downstream service
- Three states: Closed (normal), Open (blocking), Half-Open (testing recovery)
- Protects the calling system and gives the failing system time to recover
- Configure failure thresholds based on observed service behavior
- Combine with retry and timeout for comprehensive resilience

## Circuit Breaker States

```
Closed (Normal)
  ↓ failure ratio exceeds threshold
Open (Blocking) — all requests fail immediately with BrokenCircuitException
  ↓ break duration expires
Half-Open (Testing) — allows one probe request through
  ↓ probe succeeds → Closed
  ↓ probe fails → Open (reset break timer)
```

## Patterns

### HTTP Client Circuit Breaker

```csharp
builder.Services.AddHttpClient("PaymentService", client =>
{
    client.BaseAddress = new Uri("https://payments.{Company}.com");
})
.AddResilienceHandler("payment-resilience", pipeline =>
{
    // Retry first (innermost)
    pipeline.AddRetry(new HttpRetryStrategyOptions
    {
        MaxRetryAttempts = 2,
        Delay = TimeSpan.FromMilliseconds(500),
        BackoffType = DelayBackoffType.Exponential,
        UseJitter = true
    });

    // Circuit breaker wraps retry (opens when retries keep failing)
    pipeline.AddCircuitBreaker(new HttpCircuitBreakerStrategyOptions
    {
        // Open when 50% of requests fail
        FailureRatio = 0.5,
        // Over this time window
        SamplingDuration = TimeSpan.FromSeconds(30),
        // Minimum requests before evaluating
        MinimumThroughput = 10,
        // Stay open for this duration before half-open
        BreakDuration = TimeSpan.FromSeconds(30)
    });

    // Timeout per request
    pipeline.AddTimeout(TimeSpan.FromSeconds(5));
});
```

### Custom Circuit Breaker with Events

```csharp
builder.Services.AddResiliencePipeline("external-service", pipeline =>
{
    pipeline.AddCircuitBreaker(new CircuitBreakerStrategyOptions
    {
        FailureRatio = 0.3,
        SamplingDuration = TimeSpan.FromSeconds(60),
        MinimumThroughput = 5,
        BreakDuration = TimeSpan.FromSeconds(30),
        ShouldHandle = new PredicateBuilder()
            .Handle<HttpRequestException>()
            .Handle<TimeoutRejectedException>(),
        OnOpened = args =>
        {
            // Log when circuit opens
            var logger = args.Context
                .Properties.GetValue(
                    new ResiliencePropertyKey<ILogger>("logger"),
                    null!);
            logger?.LogWarning(
                "Circuit opened for {Duration}. " +
                "Reason: {Outcome}",
                args.BreakDuration,
                args.Outcome?.Exception?.Message);
            return ValueTask.CompletedTask;
        },
        OnClosed = args =>
        {
            var logger = args.Context
                .Properties.GetValue(
                    new ResiliencePropertyKey<ILogger>("logger"),
                    null!);
            logger?.LogInformation("Circuit closed — service recovered");
            return ValueTask.CompletedTask;
        },
        OnHalfOpened = args =>
        {
            var logger = args.Context
                .Properties.GetValue(
                    new ResiliencePropertyKey<ILogger>("logger"),
                    null!);
            logger?.LogInformation(
                "Circuit half-open — testing recovery");
            return ValueTask.CompletedTask;
        }
    });
});
```

### Handling BrokenCircuitException

```csharp
public sealed class PaymentService(
    IHttpClientFactory httpClientFactory,
    ILogger<PaymentService> logger)
{
    public async Task<Result<PaymentResponse>> ChargeAsync(
        Guid orderId, decimal amount, CancellationToken ct)
    {
        try
        {
            var client = httpClientFactory.CreateClient("PaymentService");
            var response = await client.PostAsJsonAsync(
                "/charges",
                new { orderId, amount },
                ct);

            response.EnsureSuccessStatusCode();
            var result = await response
                .Content.ReadFromJsonAsync<PaymentResponse>(ct);
            return Result<PaymentResponse>.Success(result!);
        }
        catch (BrokenCircuitException)
        {
            logger.LogWarning(
                "Payment service circuit is open. " +
                "Order {OrderId} payment deferred", orderId);
            return Result<PaymentResponse>.Failure(
                Error.ServiceUnavailable("Payment.Unavailable",
                    "Payment service is temporarily unavailable"));
        }
    }
}
```

### Circuit Breaker with Health Check Integration

```csharp
// Custom health check that reflects circuit state
public sealed class PaymentServiceHealthCheck(
    ResiliencePipelineProvider<string> pipelineProvider)
    : IHealthCheck
{
    public Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context, CancellationToken ct = default)
    {
        // The circuit breaker state indicates downstream health
        // If the circuit is open, report degraded
        try
        {
            var pipeline = pipelineProvider
                .GetPipeline("external-service");
            // If we can get the pipeline, the circuit state is managed
            return Task.FromResult(
                HealthCheckResult.Healthy("Payment service reachable"));
        }
        catch
        {
            return Task.FromResult(
                HealthCheckResult.Degraded("Payment service circuit open"));
        }
    }
}
```

### Configuration-Driven Circuit Breaker

```csharp
// appsettings.json
{
  "Resilience": {
    "PaymentService": {
      "FailureRatio": 0.5,
      "SamplingDurationSeconds": 30,
      "MinimumThroughput": 10,
      "BreakDurationSeconds": 30
    }
  }
}

// Options class
public sealed class CircuitBreakerOptions
{
    public double FailureRatio { get; init; } = 0.5;
    public int SamplingDurationSeconds { get; init; } = 30;
    public int MinimumThroughput { get; init; } = 10;
    public int BreakDurationSeconds { get; init; } = 30;
}

// Usage
var cbOptions = builder.Configuration
    .GetSection("Resilience:PaymentService")
    .Get<CircuitBreakerOptions>()!;

pipeline.AddCircuitBreaker(new HttpCircuitBreakerStrategyOptions
{
    FailureRatio = cbOptions.FailureRatio,
    SamplingDuration = TimeSpan.FromSeconds(
        cbOptions.SamplingDurationSeconds),
    MinimumThroughput = cbOptions.MinimumThroughput,
    BreakDuration = TimeSpan.FromSeconds(
        cbOptions.BreakDurationSeconds)
});
```

## Anti-Patterns

- Circuit breaker without retry inside (retries should happen first)
- Too-low minimum throughput (circuit flaps on small traffic)
- Too-short break duration (doesn't give downstream time to recover)
- Not handling `BrokenCircuitException` in calling code
- Circuit breaker on idempotent reads where a fallback would be better

## Detect Existing Patterns

1. Search for `AddCircuitBreaker` or `CircuitBreakerStrategyOptions`
2. Look for `BrokenCircuitException` handling
3. Check for Polly v7 `CircuitBreakerPolicy` (migration candidate)
4. Look for manual circuit breaker implementations
5. Check health check endpoints for downstream service monitoring

## Adding to Existing Project

1. **Add circuit breaker** to HTTP clients calling external services
2. **Configure thresholds** based on observed failure patterns
3. **Handle `BrokenCircuitException`** with fallback or graceful degradation
4. **Log state transitions** for operational visibility
5. **Add health checks** that reflect circuit breaker state
6. **Externalize configuration** to appsettings for runtime tuning

## Decision Guide

| Parameter | Conservative | Balanced | Aggressive |
|-----------|-------------|----------|------------|
| Failure ratio | 0.7 | 0.5 | 0.3 |
| Sampling duration | 60s | 30s | 15s |
| Min throughput | 20 | 10 | 5 |
| Break duration | 60s | 30s | 15s |

## References

- https://learn.microsoft.com/en-us/dotnet/core/resilience/
- https://www.pollydocs.org/strategies/circuit-breaker
- https://martinfowler.com/bliki/CircuitBreaker.html
