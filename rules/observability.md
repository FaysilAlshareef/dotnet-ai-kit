---
alwaysApply: true
description: Enforces structured logging, distributed tracing, health checks, and metrics conventions.
---

# Observability Rules

If you can't observe it, you can't debug it in production.

## Structured Logging

### MUST
- Use structured logging properties — never string interpolation in log templates
- Use `LogInformation("Processing order {OrderId}", orderId)` — not `$"Processing order {orderId}"`
- Include correlation context: `OrderId`, `UserId`, `RequestId` in log scopes
- Use two-stage Serilog bootstrap for startup error capture
- Log at appropriate levels: Debug (dev detail), Information (business events), Warning (recoverable), Error (failures)

### MUST NOT
- Never log sensitive data: passwords, tokens, connection strings, PII
- Never use `Console.WriteLine` — use `ILogger<T>`
- Never log inside tight loops — log summary after loop completion
- Never swallow exceptions without logging

## Health Checks

### MUST
- Register `/health/live` (liveness — is the process running?)
- Register `/health/ready` (readiness — can it serve traffic?)
- Include dependency checks: database, message bus, external APIs
- Return `Healthy`, `Degraded`, or `Unhealthy` — never throw from health checks

## Distributed Tracing

### MUST
- Use `Activity` / `ActivitySource` for custom spans in critical paths
- Propagate trace context across HTTP and messaging boundaries
- Register OpenTelemetry with ASP.NET Core, EF Core, and HttpClient instrumentation

## Detection Instructions

1. Search for `$"..."` inside log calls — replace with structured templates
2. Search for `Console.Write` — replace with `ILogger<T>`
3. Check for `/health` endpoint registration
4. Verify OpenTelemetry is registered if the project uses distributed services

## Related Skills
- `skills/observability/serilog-structured/SKILL.md` — Serilog patterns
- `skills/observability/opentelemetry/SKILL.md` — tracing and metrics
- `skills/observability/health-checks/SKILL.md` — health check patterns
