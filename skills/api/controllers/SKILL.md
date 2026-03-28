---
name: controllers
description: >
  RESTful API controllers with MediatR integration, action results,
  model binding, authorization, and ProblemDetails error handling.
metadata:
  category: api
  agent: api-designer
---

# Controller Patterns

## Base Controller

```csharp
namespace {Company}.{Domain}.Api.Controllers;

[ApiController]
[Route("api/v1/[controller]")]
[Produces("application/json")]
public abstract class BaseController : ControllerBase
{
    private ISender? _mediator;
    protected ISender Mediator =>
        _mediator ??= HttpContext.RequestServices.GetRequiredService<ISender>();
}
```

## CRUD Controller

```csharp
namespace {Company}.{Domain}.Api.Controllers;

[Authorize]
public sealed class OrdersController : BaseController
{
    /// <summary>Get paginated orders.</summary>
    [HttpGet]
    [ProducesResponseType(typeof(PaginatedList<OrderOutput>), 200)]
    public async Task<IActionResult> GetAll(
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20,
        [FromQuery] string? search = null,
        CancellationToken ct = default)
    {
        var query = new GetOrdersQuery(page, pageSize, search);
        var result = await Mediator.Send(query, ct);
        return result.IsSuccess
            ? Ok(result.Value)
            : Problem(result.Error);
    }

    /// <summary>Get order by ID.</summary>
    [HttpGet("{id:guid}")]
    [ProducesResponseType(typeof(OrderOutput), 200)]
    [ProducesResponseType(404)]
    public async Task<IActionResult> GetById(Guid id, CancellationToken ct)
    {
        var result = await Mediator.Send(new GetOrderByIdQuery(id), ct);
        return result.IsSuccess
            ? Ok(result.Value)
            : NotFound();
    }

    /// <summary>Create a new order.</summary>
    [HttpPost]
    [ProducesResponseType(typeof(Guid), 201)]
    [ProducesResponseType(typeof(ValidationProblemDetails), 400)]
    public async Task<IActionResult> Create(
        [FromBody] CreateOrderCommand command, CancellationToken ct)
    {
        var result = await Mediator.Send(command, ct);
        return result.IsSuccess
            ? CreatedAtAction(nameof(GetById), new { id = result.Value }, result.Value)
            : BadRequest(result.Error);
    }

    /// <summary>Update an existing order.</summary>
    [HttpPut("{id:guid}")]
    [ProducesResponseType(204)]
    [ProducesResponseType(404)]
    public async Task<IActionResult> Update(
        Guid id, [FromBody] UpdateOrderCommand command, CancellationToken ct)
    {
        if (id != command.Id)
            return BadRequest("Route ID does not match body ID.");

        var result = await Mediator.Send(command, ct);
        return result.IsSuccess ? NoContent() : NotFound();
    }

    /// <summary>Delete an order.</summary>
    [HttpDelete("{id:guid}")]
    [ProducesResponseType(204)]
    [ProducesResponseType(404)]
    public async Task<IActionResult> Delete(Guid id, CancellationToken ct)
    {
        var result = await Mediator.Send(new DeleteOrderCommand(id), ct);
        return result.IsSuccess ? NoContent() : NotFound();
    }
}
```

## Global Exception Handler

```csharp
namespace {Company}.{Domain}.Api.Middleware;

public sealed class GlobalExceptionHandler(ILogger<GlobalExceptionHandler> logger)
    : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(
        HttpContext context, Exception exception, CancellationToken ct)
    {
        logger.LogError(exception, "Unhandled exception");

        var problem = exception switch
        {
            ValidationException ve => new ProblemDetails
            {
                Status = 400, Title = "Validation Failed",
                Detail = string.Join("; ", ve.Errors.Select(e => e.ErrorMessage))
            },
            NotFoundException => new ProblemDetails
            {
                Status = 404, Title = "Not Found"
            },
            _ => new ProblemDetails
            {
                Status = 500, Title = "Internal Server Error"
            }
        };

        context.Response.StatusCode = problem.Status!.Value;
        await context.Response.WriteAsJsonAsync(problem, ct);
        return true;
    }
}
```

## Registration

```csharp
// Program.cs
builder.Services.AddControllers();
builder.Services.AddExceptionHandler<GlobalExceptionHandler>();
builder.Services.AddProblemDetails();

var app = builder.Build();
app.UseExceptionHandler();
app.MapControllers();
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Business logic in controllers | Delegate to MediatR handlers |
| Returning domain entities directly | Map to output DTOs |
| Manual model validation | Use FluentValidation + pipeline behavior |
| Catching exceptions per action | Use global exception handler |

## Detect Existing Patterns

```bash
grep -r "ControllerBase\|ApiController" --include="*.cs"
grep -r "IMediator\|ISender" --include="*.cs"
```

## Adding to Existing Project

1. Check if project uses Minimal API or Controllers (don't mix)
2. Follow existing controller structure and naming
3. Use same base controller if one exists
