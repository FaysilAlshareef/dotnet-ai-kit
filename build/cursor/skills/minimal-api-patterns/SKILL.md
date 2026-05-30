---
name: minimal-api-patterns
description: "Generates ASP.NET Core Minimal API endpoints with typed results, route groups, and endpoint filters. Use when adding HTTP endpoints to a Minimal API project on .NET 8+. Do NOT use for MVC controllers (use controller-patterns) or gRPC services (use grpc-service)."
---
# Minimal API Patterns

Generate Minimal API endpoints that are testable, typed, and grouped.

## Conventions
- Group related routes with `MapGroup` and apply shared filters/auth once.
- Return `Results<Ok<T>, NotFound, ValidationProblem>` typed unions, not bare objects.
- Keep handlers thin: validate → delegate to an application use-case → map to a typed result.
- Bind request bodies to records; validate with source-generated `AddValidation` (.NET 10).

## Example
```csharp
var group = app.MapGroup("/orders").WithTags("Orders").RequireAuthorization();
group.MapGet("/{id:guid}", async (Guid id, IOrderQueries q, CancellationToken ct)
    => await q.FindAsync(id, ct) is { } o ? Results.Ok(o) : Results.NotFound());
```

Substitution token: namespace root is `${Company}.${Domain}`.
