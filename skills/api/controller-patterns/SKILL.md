---
name: controller-patterns
description: >
  Controller-based API design, action results, model binding, routing,
  and MediatR integration patterns.
  Trigger: controller, ControllerBase, ApiController, action result, REST.
metadata:
  category: api
  agent: api-designer
---

# Controller Patterns

## Core Principles

- Use `[ApiController]` for automatic model validation and binding behavior
- Follow RESTful route conventions with resource-based URLs
- Return `ActionResult<T>` with explicit `[ProducesResponseType]` attributes
- Delegate all logic to MediatR handlers — controllers are thin dispatchers
- Propagate `CancellationToken` from every action method

## Patterns

### Standard RESTful Controller

```csharp
[ApiController]
[Route("api/[controller]")]
[Produces("application/json")]
public sealed class OrdersController(ISender sender) : ControllerBase
{
    [HttpGet]
    [ProducesResponseType(typeof(PagedList<OrderResponse>),
        StatusCodes.Status200OK)]
    public async Task<ActionResult<PagedList<OrderResponse>>> GetOrders(
        [FromQuery] OrderFilter filter, CancellationToken ct)
    {
        var result = await sender.Send(new ListOrdersQuery(filter), ct);
        return Ok(result);
    }

    [HttpGet("{id:guid}")]
    [ProducesResponseType(typeof(OrderResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<OrderResponse>> GetOrder(
        Guid id, CancellationToken ct)
    {
        var result = await sender.Send(new GetOrderQuery(id), ct);
        return result is not null ? Ok(result) : NotFound();
    }

    [HttpPost]
    [ProducesResponseType(typeof(OrderResponse),
        StatusCodes.Status201Created)]
    [ProducesResponseType(typeof(ProblemDetails),
        StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<OrderResponse>> CreateOrder(
        CreateOrderRequest request, CancellationToken ct)
    {
        var result = await sender.Send(
            new CreateOrderCommand(request.CustomerName, request.Items), ct);
        return CreatedAtAction(
            nameof(GetOrder), new { id = result.Id }, result);
    }

    [HttpPut("{id:guid}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> UpdateOrder(
        Guid id, UpdateOrderRequest request, CancellationToken ct)
    {
        var result = await sender.Send(
            new UpdateOrderCommand(id, request.CustomerName), ct);
        return result.Match<IActionResult>(
            _ => NoContent(),
            error => error.Type == ErrorType.NotFound
                ? NotFound() : BadRequest(error.ToProblemDetails()));
    }

    [HttpDelete("{id:guid}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> DeleteOrder(
        Guid id, CancellationToken ct)
    {
        var result = await sender.Send(new DeleteOrderCommand(id), ct);
        return result.IsSuccess ? NoContent() : NotFound();
    }
}
```

### Nested Resource Controller

```csharp
[ApiController]
[Route("api/orders/{orderId:guid}/items")]
[Produces("application/json")]
public sealed class OrderItemsController(ISender sender) : ControllerBase
{
    [HttpGet]
    public async Task<ActionResult<List<OrderItemResponse>>> GetItems(
        Guid orderId, CancellationToken ct)
    {
        var result = await sender.Send(
            new ListOrderItemsQuery(orderId), ct);
        return Ok(result);
    }

    [HttpPost]
    [ProducesResponseType(StatusCodes.Status201Created)]
    public async Task<IActionResult> AddItem(
        Guid orderId, AddOrderItemRequest request, CancellationToken ct)
    {
        var result = await sender.Send(
            new AddOrderItemCommand(orderId, request.ProductId,
                request.Quantity), ct);
        return CreatedAtAction(nameof(GetItems), new { orderId }, result);
    }
}
```

### Controller Registration

```csharp
// Program.cs
builder.Services.AddControllers()
    .AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.Converters.Add(
            new JsonStringEnumConverter());
        options.JsonSerializerOptions.DefaultIgnoreCondition =
            JsonIgnoreCondition.WhenWritingNull;
    });

var app = builder.Build();

app.MapControllers();
```

### ProblemDetails Configuration

```csharp
builder.Services.AddProblemDetails(options =>
{
    options.CustomizeProblemDetails = context =>
    {
        context.ProblemDetails.Instance =
            context.HttpContext.Request.Path;
        context.ProblemDetails.Extensions["traceId"] =
            Activity.Current?.Id ??
            context.HttpContext.TraceIdentifier;
    };
});
```

### Model Binding

```csharp
// FromQuery — query string parameters
public async Task<IActionResult> Search(
    [FromQuery] string? name,
    [FromQuery] int page = 1) { }

// FromRoute — URL route parameters
[HttpGet("{id:guid}")]
public async Task<IActionResult> Get(
    [FromRoute] Guid id) { }

// FromBody — request body (default for complex types with [ApiController])
[HttpPost]
public async Task<IActionResult> Create(
    CreateOrderRequest request) { }

// FromHeader — custom headers
public async Task<IActionResult> Process(
    [FromHeader(Name = "X-Correlation-Id")] string? correlationId) { }
```

## Anti-Patterns

- Business logic in controller actions (use handlers)
- Returning domain entities directly (use DTOs)
- Missing `CancellationToken` parameter
- Missing `[ProducesResponseType]` attributes
- Fat controllers with many responsibilities
- Constructor injection of more than `ISender`/`IMediator`

## Detect Existing Patterns

1. Search for `: ControllerBase` or `: Controller` class inheritance
2. Look for `[ApiController]` attribute on classes
3. Check for `Controllers/` folder
4. Look for `services.AddControllers()` in `Program.cs`
5. Check for `[ProducesResponseType]` attributes on actions

## Adding to Existing Project

1. **Add `[ApiController]`** to all API controllers for automatic validation
2. **Add MediatR** and move logic from controller actions to handlers
3. **Add `[ProducesResponseType]`** to document response types for OpenAPI
4. **Add `CancellationToken`** parameter to all async action methods
5. **Configure ProblemDetails** for consistent error responses
6. **Use `CreatedAtAction`** for POST endpoints returning 201

## Decision Guide

| Scenario | Recommendation |
|----------|---------------|
| Complex model binding | Controllers handle this well |
| Need attribute routing | Controllers with `[Route]` |
| Rapid prototyping | Minimal API may be faster |
| Legacy migration | Keep controllers, modernize patterns |
| OpenAPI generation | Both work, controllers have richer attributes |

## References

- https://learn.microsoft.com/en-us/aspnet/core/web-api/
- https://learn.microsoft.com/en-us/aspnet/core/mvc/controllers/actions
