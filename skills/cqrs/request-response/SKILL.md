---
name: request-response
description: >
  CQRS request/response patterns, FluentValidation integration, Result types,
  and response DTO design.
  Trigger: request response, FluentValidation, validator, DTO, Result.
category: cqrs
agent: ef-specialist
---

# Request/Response Patterns

## Core Principles

- Requests are immutable records with all required data for the operation
- Responses are DTOs — no domain logic, no entity references
- Validate all commands with FluentValidation before handler execution
- Use Result<T> pattern for operations that can fail in expected ways
- Keep request/response types co-located with their handlers

## Patterns

### Command Request with Nested Types

```csharp
public sealed record CreateOrderCommand(
    string CustomerName,
    string ShippingEmail,
    List<CreateOrderCommand.LineItem> Items)
    : IRequest<Result<CreateOrderCommand.Response>>
{
    public sealed record LineItem(
        Guid ProductId,
        int Quantity,
        decimal UnitPrice);

    public sealed record Response(
        Guid OrderId,
        decimal Total,
        DateTimeOffset CreatedAt);
}
```

### FluentValidation Validator

```csharp
public sealed class CreateOrderCommandValidator
    : AbstractValidator<CreateOrderCommand>
{
    public CreateOrderCommandValidator()
    {
        RuleFor(x => x.CustomerName)
            .NotEmpty()
            .MaximumLength(200)
            .WithMessage("Customer name is required (max 200 chars)");

        RuleFor(x => x.ShippingEmail)
            .NotEmpty()
            .EmailAddress()
            .WithMessage("Valid shipping email is required");

        RuleFor(x => x.Items)
            .NotEmpty()
            .WithMessage("Order must contain at least one item");

        RuleForEach(x => x.Items).ChildRules(item =>
        {
            item.RuleFor(x => x.ProductId)
                .NotEmpty();
            item.RuleFor(x => x.Quantity)
                .GreaterThan(0)
                .LessThanOrEqualTo(1000);
            item.RuleFor(x => x.UnitPrice)
                .GreaterThan(0);
        });
    }
}
```

### Async Validation with Database Checks

```csharp
public sealed class CreateOrderCommandValidator
    : AbstractValidator<CreateOrderCommand>
{
    public CreateOrderCommandValidator(AppDbContext db)
    {
        RuleFor(x => x.CustomerName)
            .NotEmpty()
            .MustAsync(async (name, ct) =>
                await db.Customers.AnyAsync(
                    c => c.Name == name, ct))
            .WithMessage("Customer not found");

        RuleForEach(x => x.Items).ChildRules(item =>
        {
            item.RuleFor(x => x.ProductId)
                .MustAsync(async (id, ct) =>
                    await db.Products.AnyAsync(
                        p => p.Id == id && p.IsActive, ct))
                .WithMessage("Product not found or inactive");
        });
    }
}
```

### Query Request with Filter

```csharp
public sealed record ListOrdersQuery(
    string? CustomerName = null,
    OrderStatus? Status = null,
    DateTime? FromDate = null,
    DateTime? ToDate = null,
    string? SortBy = "CreatedAt",
    bool SortDescending = true,
    int Page = 1,
    int PageSize = 20) : IRequest<PagedList<OrderSummaryResponse>>;
```

### Response DTO Design

```csharp
// Simple response
public sealed record OrderResponse(
    Guid Id,
    string CustomerName,
    decimal Total,
    string Status,
    DateTimeOffset CreatedAt,
    List<OrderItemResponse> Items);

public sealed record OrderItemResponse(
    Guid ProductId,
    string ProductName,
    int Quantity,
    decimal UnitPrice,
    decimal LineTotal);

// Paged response
public sealed record PagedList<T>(
    List<T> Items,
    int TotalCount,
    int Page,
    int PageSize)
{
    public int TotalPages =>
        (int)Math.Ceiling(TotalCount / (double)PageSize);
    public bool HasNext => Page < TotalPages;
    public bool HasPrevious => Page > 1;
}

// Summary response (for list views)
public sealed record OrderSummaryResponse(
    Guid Id,
    string CustomerName,
    decimal Total,
    string Status,
    DateTimeOffset CreatedAt);
```

### Result Pattern Integration

```csharp
// Result type
public sealed class Result<T>
{
    private Result(T value) { Value = value; IsSuccess = true; }
    private Result(Error error) { Error = error; IsSuccess = false; }

    public bool IsSuccess { get; }
    public T Value { get; } = default!;
    public Error Error { get; } = default!;

    public static Result<T> Success(T value) => new(value);
    public static Result<T> Failure(Error error) => new(error);

    public TResult Match<TResult>(
        Func<T, TResult> onSuccess,
        Func<Error, TResult> onFailure)
        => IsSuccess ? onSuccess(Value) : onFailure(Error);
}

// Handler returning Result
internal sealed class GetOrderHandler(IOrderRepository repo)
    : IRequestHandler<GetOrderQuery, Result<OrderResponse>>
{
    public async Task<Result<OrderResponse>> Handle(
        GetOrderQuery request, CancellationToken ct)
    {
        var order = await repo.FindAsync(request.OrderId, ct);
        if (order is null)
            return Result<OrderResponse>.Failure(
                Error.NotFound("Order.NotFound",
                    $"Order {request.OrderId} not found"));

        return Result<OrderResponse>.Success(order.ToResponse());
    }
}

// Endpoint consuming Result
app.MapGet("/orders/{id}", async (Guid id, ISender sender) =>
{
    var result = await sender.Send(new GetOrderQuery(id));
    return result.Match(
        value => Results.Ok(value),
        error => error.Type switch
        {
            ErrorType.NotFound => Results.NotFound(
                error.ToProblemDetails()),
            _ => Results.BadRequest(error.ToProblemDetails())
        });
});
```

### Validation Registration

```csharp
// Register all validators from assembly
builder.Services.AddValidatorsFromAssembly(
    typeof(CreateOrderCommandValidator).Assembly);

// FluentValidation runs automatically via ValidationBehavior
```

## Anti-Patterns

- Mutable request objects (always use `record` or `readonly`)
- Domain entities in response DTOs (use dedicated response records)
- Validation logic in handlers (use FluentValidation + behavior)
- Missing validation for commands (queries may skip validation)
- Returning `null` instead of `Result.Failure` for expected failures

## Detect Existing Patterns

1. Search for `AbstractValidator<` implementations
2. Look for `Result<T>` or `ErrorOr<T>` types
3. Check for request/response records with `IRequest<>`
4. Look for `RuleFor`, `RuleForEach` validation rules
5. Check for `FluentValidation` package reference

## Adding to Existing Project

1. **Install FluentValidation** — `dotnet add package FluentValidation.DependencyInjectionExtensions`
2. **Create validators** for all command types
3. **Register validators** with `AddValidatorsFromAssembly`
4. **Add ValidationBehavior** as a pipeline behavior
5. **Define response DTOs** for all handler return types
6. **Adopt Result pattern** for operations with expected failure modes

## References

- https://docs.fluentvalidation.net/
- https://github.com/jbogard/MediatR/wiki
