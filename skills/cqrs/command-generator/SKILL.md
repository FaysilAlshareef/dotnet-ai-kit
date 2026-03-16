---
name: cqrs-command-generator
description: >
  CQRS command pattern: command record + handler + validator using
  MediatR and FluentValidation. Three-section file organization.
category: cqrs
agent: ef-specialist
---

# CQRS Command Generator

## Command Record

```csharp
namespace {Company}.{Domain}.Application.Features.Orders.Commands.Create;

public sealed record CreateOrderCommand(
    string CustomerName,
    decimal Total,
    List<CreateOrderItemDto> Items) : IRequest<Result<Guid>>;

public sealed record CreateOrderItemDto(
    string ProductName,
    int Quantity,
    decimal UnitPrice);
```

## Validator

```csharp
namespace {Company}.{Domain}.Application.Features.Orders.Commands.Create;

internal sealed class CreateOrderCommandValidator
    : AbstractValidator<CreateOrderCommand>
{
    public CreateOrderCommandValidator()
    {
        RuleFor(x => x.CustomerName)
            .NotEmpty().WithMessage("Customer name is required")
            .MaximumLength(200);

        RuleFor(x => x.Total)
            .GreaterThan(0).WithMessage("Total must be positive");

        RuleFor(x => x.Items)
            .NotEmpty().WithMessage("At least one item is required");

        RuleForEach(x => x.Items).ChildRules(item =>
        {
            item.RuleFor(i => i.ProductName).NotEmpty();
            item.RuleFor(i => i.Quantity).GreaterThan(0);
            item.RuleFor(i => i.UnitPrice).GreaterThan(0);
        });
    }
}
```

## Handler

```csharp
namespace {Company}.{Domain}.Application.Features.Orders.Commands.Create;

internal sealed class CreateOrderCommandHandler(
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateOrderCommand, Result<Guid>>
{
    public async Task<Result<Guid>> Handle(
        CreateOrderCommand request, CancellationToken cancellationToken)
    {
        var order = Order.Create(
            request.CustomerName,
            request.Total,
            request.Items.Select(i => new OrderItem(
                i.ProductName, i.Quantity, i.UnitPrice)).ToList());

        await unitOfWork.Orders.AddAsync(order, cancellationToken);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return Result<Guid>.Success(order.Id);
    }
}
```

## Update Command Pattern

```csharp
public sealed record UpdateOrderCommand(
    Guid Id,
    string CustomerName,
    decimal Total) : IRequest<Result>;

internal sealed class UpdateOrderCommandHandler(
    IUnitOfWork unitOfWork)
    : IRequestHandler<UpdateOrderCommand, Result>
{
    public async Task<Result> Handle(
        UpdateOrderCommand request, CancellationToken cancellationToken)
    {
        var order = await unitOfWork.Orders.FindAsync(
            request.Id, cancellationToken);

        if (order is null)
            return Result.Failure("Order not found");

        order.Update(request.CustomerName, request.Total);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return Result.Success();
    }
}
```

## Delete Command Pattern

```csharp
public sealed record DeleteOrderCommand(Guid Id) : IRequest<Result>;

internal sealed class DeleteOrderCommandHandler(
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeleteOrderCommand, Result>
{
    public async Task<Result> Handle(
        DeleteOrderCommand request, CancellationToken cancellationToken)
    {
        var order = await unitOfWork.Orders.FindAsync(
            request.Id, cancellationToken);

        if (order is null)
            return Result.Failure("Order not found");

        unitOfWork.Orders.Remove(order);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return Result.Success();
    }
}
```

## File Structure (Feature Folder)

```
Application/Features/Orders/Commands/
├── Create/
│   ├── CreateOrderCommand.cs
│   ├── CreateOrderCommandValidator.cs
│   └── CreateOrderCommandHandler.cs
├── Update/
│   ├── UpdateOrderCommand.cs
│   ├── UpdateOrderCommandValidator.cs
│   └── UpdateOrderCommandHandler.cs
└── Delete/
    ├── DeleteOrderCommand.cs
    └── DeleteOrderCommandHandler.cs
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Command with mutable properties | Use `sealed record` (immutable) |
| Validation in handler | Use FluentValidation + pipeline behavior |
| Returning domain entity from handler | Return `Result<T>` with ID or DTO |
| Handler accessing DbContext directly | Use IUnitOfWork or IRepository |

## Detect Existing Patterns

```bash
grep -r "IRequest<\|IRequestHandler<" --include="*.cs"
grep -r "AbstractValidator<" --include="*.cs"
```

## Adding to Existing Project

1. Add MediatR and FluentValidation NuGet packages
2. Register with `AddMediatR` and `AddValidatorsFromAssembly`
3. Add `ValidationBehavior<,>` pipeline behavior
4. Create feature folder per aggregate/entity
