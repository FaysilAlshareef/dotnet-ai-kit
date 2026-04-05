---
name: minimal-api
description: >
  Minimal API endpoints, route groups, endpoint filters, TypedResults,
  and auto-discovery patterns.
  Trigger: minimal API, endpoints, MapGet, MapPost, route group, TypedResults.
metadata:
  category: api
  agent: api-designer
  when-to-use: "When creating minimal API endpoints, route groups, or endpoint filters"
---

# Minimal API Endpoints

## Core Principles

- Organize endpoints into groups using `IEndpointGroup` pattern
- Use `TypedResults` for compile-time-checked return types
- Apply endpoint filters for cross-cutting concerns
- Use `[AsParameters]` for complex query parameter binding
- Register OpenAPI metadata on every endpoint

## Patterns

### IEndpointGroup Interface and Auto-Discovery

```csharp
public interface IEndpointGroup
{
    void MapEndpoints(IEndpointRouteBuilder app);
}

// Auto-registration extension
public static class EndpointGroupExtensions
{
    public static void MapEndpointGroups(this WebApplication app)
    {
        var groups = typeof(Program).Assembly
            .GetTypes()
            .Where(t => t.IsAssignableTo(typeof(IEndpointGroup))
                && !t.IsInterface && !t.IsAbstract)
            .Select(Activator.CreateInstance)
            .Cast<IEndpointGroup>();

        foreach (var group in groups)
            group.MapEndpoints(app);
    }
}

// Program.cs
app.MapEndpointGroups();
```

### Endpoint Group with Route Prefix

```csharp
public sealed class OrderEndpoints : IEndpointGroup
{
    public void MapEndpoints(IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/orders")
            .WithTags("Orders")
            .RequireAuthorization();

        group.MapGet("/", GetOrders)
            .WithSummary("List orders with filtering");

        group.MapGet("/{id:guid}", GetOrder)
            .WithSummary("Get order by ID");

        group.MapPost("/", CreateOrder)
            .WithSummary("Create a new order");

        group.MapPut("/{id:guid}", UpdateOrder)
            .WithSummary("Update an existing order");

        group.MapDelete("/{id:guid}", DeleteOrder)
            .WithSummary("Delete an order");
    }

    private static async Task<Ok<PagedList<OrderResponse>>> GetOrders(
        [AsParameters] OrderFilter filter,
        ISender sender, CancellationToken ct)
    {
        var result = await sender.Send(
            new ListOrdersQuery(filter), ct);
        return TypedResults.Ok(result);
    }

    private static async Task<Results<Ok<OrderResponse>, NotFound>>
        GetOrder(Guid id, ISender sender, CancellationToken ct)
    {
        var result = await sender.Send(
            new GetOrderQuery(id), ct);
        return result is not null
            ? TypedResults.Ok(result)
            : TypedResults.NotFound();
    }

    private static async Task<Results<Created<OrderResponse>,
        BadRequest<ProblemDetails>>> CreateOrder(
        CreateOrderRequest request,
        ISender sender, CancellationToken ct)
    {
        var result = await sender.Send(
            new CreateOrderCommand(request.CustomerName), ct);
        return result.Match<Results<Created<OrderResponse>,
            BadRequest<ProblemDetails>>>(
            order => TypedResults.Created(
                $"/orders/{order.Id}", order),
            error => TypedResults.BadRequest(
                error.ToProblemDetails()));
    }
}
```

### Parameter Binding with [AsParameters]

```csharp
public sealed record OrderFilter(
    [FromQuery] string? CustomerName,
    [FromQuery] OrderStatus? Status,
    [FromQuery] int Page = 1,
    [FromQuery] int PageSize = 20);
```

### Endpoint Filters

```csharp
// Validation filter
public sealed class ValidationFilter<TRequest>(
    IValidator<TRequest> validator) : IEndpointFilter
{
    public async ValueTask<object?> InvokeAsync(
        EndpointFilterInvocationContext context,
        EndpointFilterDelegate next)
    {
        var request = context.Arguments
            .OfType<TRequest>().FirstOrDefault();

        if (request is null)
            return TypedResults.BadRequest("Request body is required");

        var result = await validator.ValidateAsync(request);
        if (!result.IsValid)
        {
            return TypedResults.ValidationProblem(
                result.ToDictionary());
        }

        return await next(context);
    }
}

// Apply filter to endpoint
group.MapPost("/", CreateOrder)
    .AddEndpointFilter<ValidationFilter<CreateOrderRequest>>();
```

### Global Exception Handler

```csharp
// Program.cs
app.UseExceptionHandler(error => error.Run(async context =>
{
    context.Response.ContentType = "application/problem+json";
    context.Response.StatusCode = StatusCodes.Status500InternalServerError;

    await context.Response.WriteAsJsonAsync(new ProblemDetails
    {
        Status = 500,
        Title = "Internal Server Error",
        Type = "https://tools.ietf.org/html/rfc9110#section-15.6.1"
    });
}));
```

## Anti-Patterns

- Defining all endpoints directly in `Program.cs` (use endpoint groups)
- Returning `IResult` without TypedResults (loses compile-time checking)
- Missing OpenAPI metadata (WithSummary, WithTags)
- Not propagating `CancellationToken` from endpoint to handler
- Inline business logic in endpoint delegates

## Detect Existing Patterns

1. Search for `MapGroup`, `MapGet`, `MapPost` in `Program.cs` or endpoint files
2. Look for `IEndpointGroup` or `IEndpointRouteBuilder` extension methods
3. Check for `TypedResults` usage
4. Look for `WithTags`, `WithSummary` metadata calls
5. Check for `AddEndpointFilter` calls

## Adding to Existing Project

1. **Create `IEndpointGroup` interface** and auto-discovery extension
2. **Group related endpoints** into classes per feature/entity
3. **Add `TypedResults`** for explicit return type contracts
4. **Add OpenAPI metadata** — `WithSummary`, `WithTags`, `WithDescription`
5. **Create endpoint filters** for validation and error handling
6. **Use `[AsParameters]`** for complex query parameter objects

## Decision Guide

| Scenario | Recommendation |
|----------|---------------|
| Simple CRUD API | Minimal API with endpoint groups |
| Complex model binding | Controllers may be easier |
| Real-time + REST | Minimal API + SignalR hubs |
| Need OpenAPI docs | Add `WithSummary`/`WithDescription` to every endpoint |

## References

- https://learn.microsoft.com/en-us/aspnet/core/fundamentals/minimal-apis
- https://learn.microsoft.com/en-us/aspnet/core/fundamentals/minimal-apis/min-api-filters
