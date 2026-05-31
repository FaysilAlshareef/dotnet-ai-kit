---
name: endpoint-filters
description: "Implements ASP.NET Core IEndpointFilter to apply cross-cutting concerns — logging, auth checks, header enforcement, short-circuiting — to Minimal API endpoints and route groups. Use when adding behaviour that wraps endpoint execution without polluting handlers. Do NOT use for request body/model validation specifically (use minimal-api-validation) or for authoring the endpoints themselves (use minimal-api-patterns)."
metadata:
  category: "api"
  agent: "api-designer"
---
# Endpoint Filters

`IEndpointFilter` wraps a Minimal API handler the way middleware wraps the pipeline, but scoped to one endpoint or `MapGroup`. Use it to keep handlers thin: the filter does the cross-cutting work, then calls `next` (or short-circuits with a result).

## Conventions
- Implement `IEndpointFilter.InvokeAsync(EndpointFilterInvocationContext ctx, EndpointFilterDelegate next)`; return `await next(ctx)` to continue or a `TypedResults`/`Results` value to short-circuit.
- Read handler arguments by type via `ctx.GetArgument<T>(index)` or `ctx.Arguments.OfType<T>()`; never re-parse the request.
- Apply with `.AddEndpointFilter<T>()` on a single endpoint or once on a `MapGroup` to cover all routes in the group.
- Filters run in registration order (outermost first); group filters run before endpoint-specific ones.
- Make filters DI-friendly — inject services through the constructor; the factory overload resolves them per request.
- Use `.AddEndpointFilterFactory(...)` only when you need compile-time metadata about the endpoint (e.g. generic-argument inspection).

## Example
```csharp
public sealed class RequestLoggingFilter(ILogger<RequestLoggingFilter> log)
    : IEndpointFilter
{
    public async ValueTask<object?> InvokeAsync(
        EndpointFilterInvocationContext ctx, EndpointFilterDelegate next)
    {
        var path = ctx.HttpContext.Request.Path;
        log.LogInformation("Handling {Path}", path);

        // Short-circuit example: enforce a required header
        if (!ctx.HttpContext.Request.Headers.ContainsKey("X-Tenant-Id"))
            return TypedResults.BadRequest("X-Tenant-Id header is required");

        var result = await next(ctx);          // run the handler
        log.LogInformation("Handled {Path}", path);
        return result;
    }
}

// Apply to a whole group
app.MapGroup("/orders")
   .AddEndpointFilter<RequestLoggingFilter>();
```

## Anti-Patterns
- Putting cross-cutting logic inline in every handler instead of a shared filter.
- Using `IEndpointFilter` for app-wide concerns that belong in middleware (CORS, auth scheme).
- Forgetting to return `next(ctx)`, silently dropping the handler's result.
- Hand-coding validation in a filter when source-generated validation exists.

## References
- https://learn.microsoft.com/en-us/aspnet/core/fundamentals/minimal-apis/min-api-filters
