---
name: command-handler
description: >
  MediatR command handlers for event-sourced microservices. Covers IRequestHandler pattern,
  aggregate loading/creation via IUnitOfWork and ICommitEventService, command records with
  domain command interfaces, and gRPC service mapping.
  Trigger: command handler, MediatR, CQRS command, business logic.
metadata:
  category: microservice/command
  agent: command-architect
---

# Command Handler -- MediatR Command Pattern

## Core Principles

- Handlers implement `IRequestHandler<TCommand>` (void) or `IRequestHandler<TCommand, TResponse>` via MediatR
- The handler orchestrates: validate existence, load/create aggregate, call domain method, commit
- Inject `ICommitEventService` and `IUnitOfWork` (for event loading and saving)
- Some handlers also inject `IQueriesServices` for cross-service gRPC queries
- Commands are **records** implementing both `IRequest` (MediatR) and a domain command interface
- Custom exceptions implement `IProblemDetailsProvider` for gRPC error mapping
- Handlers do NOT return the aggregate -- return void or an output DTO

## Key Patterns

### Command Record

Commands are records that implement both `IRequest` (MediatR) and a domain command interface.

```csharp
using {Company}.{Domain}.Commands.Domain.Commands.Orders;
using MediatR;

namespace {Company}.{Domain}.Commands.Application.Features.Commands.Orders.CreateOrder;

public record CreateOrderCommand(
    Guid Id,
    Guid UserId,
    string CustomerName,
    decimal Total,
    List<Guid> Items,
    OrderStatus Status
) : ICreateOrderCommand, IRequest;
```

The domain command interface lives in the Domain layer:

```csharp
namespace {Company}.{Domain}.Commands.Domain.Commands.Orders;

public interface ICreateOrderCommand
{
    Guid Id { get; }
    Guid UserId { get; }
    string CustomerName { get; }
    decimal Total { get; }
    List<Guid> Items { get; }
    OrderStatus Status { get; }
}
```

### Create Handler (New Aggregate)

```csharp
using {Company}.{Domain}.Commands.Application.Contracts.Repositories;
using {Company}.{Domain}.Commands.Application.Contracts.Services.BaseServices;
using {Company}.{Domain}.Commands.Domain.Exceptions.Orders;
using MediatR;

namespace {Company}.{Domain}.Commands.Application.Features.Commands.Orders.CreateOrder;

public class CreateOrderHandler(IUnitOfWork unitOfWork, ICommitEventService commitEventsService)
    : IRequestHandler<CreateOrderCommand>
{
    private readonly IUnitOfWork _unitOfWork = unitOfWork;
    private readonly ICommitEventService _commitEventsService = commitEventsService;

    public async Task Handle(CreateOrderCommand request, CancellationToken cancellationToken)
    {
        var events = await _unitOfWork.Events
            .GetAllByAggregateIdAsync(request.Id, cancellationToken);

        if (events.Any())
            throw new OrderAlreadyExistException();

        var order = Order.Create(request);

        await _commitEventsService.CommitNewEventsAsync(order);
    }
}
```

Key details:
- Uses **primary constructor** for dependency injection
- Fields are explicitly declared: `private readonly IUnitOfWork _unitOfWork = unitOfWork;`
- First checks if aggregate already exists by loading events for the given Id
- If events exist, throws domain exception (idempotency guard)
- Creates aggregate via static factory method `Order.Create(request)`
- Commits via `_commitEventsService.CommitNewEventsAsync(order)` -- passes the aggregate, not the events
- Returns `Task` (void handler) -- no output DTO for simple creates

### Update Handler (Existing Aggregate)

```csharp
using {Company}.{Domain}.Commands.Application.Contracts.Repositories;
using {Company}.{Domain}.Commands.Application.Contracts.Services.BaseServices;
using {Company}.{Domain}.Commands.Domain.Exceptions.Orders;
using MediatR;

namespace {Company}.{Domain}.Commands.Application.Features.Commands.Orders.AddItems;

public class AddItemsHandler(ICommitEventService commitEventsService, IUnitOfWork _unitOfWork)
    : IRequestHandler<AddItemsToOrderCommand>
{
    private readonly ICommitEventService _commitEventsService = commitEventsService;

    public async Task Handle(AddItemsToOrderCommand command, CancellationToken cancellationToken)
    {
        var events = await _unitOfWork.Events
            .GetAllByAggregateIdAsync(command.OrderId, cancellationToken);

        if (!events.Any())
            throw new OrderNotFoundException(command.UserId);

        var order = Order.LoadFromHistory(events);

        order.AddItems(command);

        await _commitEventsService.CommitNewEventsAsync(order);
    }
}
```

Key details:
- Loads all events for the aggregate by ID
- If no events exist, throws `NotFoundException` (not found guard)
- Rebuilds aggregate from history via `Order.LoadFromHistory(events)` (static method)
- Calls domain business method on the aggregate
- Commits the new uncommitted events

### Handler with Output DTO

```csharp
namespace {Company}.{Domain}.Commands.Application.Features.Commands.Orders.RegisterOrder;

public class RegisterOrderHandler(
    ICommitEventService commitEventsService,
    IUnitOfWork _unitOfWork,
    IQueriesServices _queriesServices)
    : IRequestHandler<RegisterOrderCommand, RegisterOrderOutput>
{
    private readonly ICommitEventService _commitEventsService = commitEventsService;

    public async Task<RegisterOrderOutput> Handle(
        RegisterOrderCommand command, CancellationToken cancellationToken)
    {
        // Cross-service query for validation
        var customerInfo = await _queriesServices.GetCustomerInfoAsync(command.CustomerId);

        var events = await _unitOfWork.Events
            .GetAllByAggregateIdAsync(command.OrderId, cancellationToken);

        if (!events.Any())
            throw new OrderNotFoundException(command.UserId);

        var order = Order.LoadFromHistory(events);

        order.Register(command);

        await _commitEventsService.CommitNewEventsAsync(order);

        return new RegisterOrderOutput(order.Id, order.Sequence);
    }
}

public record RegisterOrderOutput(Guid Id, int Sequence);
```

### gRPC Service Mapping

The gRPC service layer maps protobuf requests to MediatR commands:

```csharp
public override async Task<CreateOrderResponse> CreateOrder(
    CreateOrderRequest request, ServerCallContext context)
{
    var userId = context.GetUserId(); // from metadata/claims

    var command = new CreateOrderCommand(
        Id: Guid.Parse(request.Id),
        UserId: userId,
        CustomerName: request.CustomerName,
        Total: request.Total,
        Items: request.Items.Select(Guid.Parse).ToList(),
        Status: (Domain.Enums.OrderStatus)request.Status
    );

    await _mediator.Send(command);

    return new CreateOrderResponse { Message = Phrases.OrderCreated };
}
```

### File Organization

Handlers follow a feature-folder structure:

```
Application/
  Features/
    Commands/
      Orders/
        CreateOrder/
          CreateOrderCommand.cs
          CreateOrderHandler.cs
        AddItems/
          AddItemsToOrderCommand.cs
          AddItemsHandler.cs
        UpdateOrder/
          UpdateOrderCommand.cs
          UpdateOrderHandler.cs
      Invoices/
        GenerateInvoice/
          GenerateInvoiceCommand.cs
          GenerateInvoiceHandler.cs
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Business logic in handler | Delegate to aggregate methods |
| `new Order()` in handler | Use `Order.Create(command)` or `Order.LoadFromHistory(events)` |
| Passing events list to commit | Pass the aggregate: `CommitNewEventsAsync(order)` |
| Returning aggregate from handler | Return void or output DTO only |
| Catching and swallowing exceptions | Let exceptions propagate to gRPC interceptor |
| Creating DbContext transactions in handler | CommitEventService handles SaveChangesAsync internally |
| Injecting ApplicationDbContext in handler | Use IUnitOfWork for data access |

## Detect Existing Patterns

```bash
# Find command handlers
grep -r "IRequestHandler<.*Command" --include="*.cs" src/Application/

# Find commit calls
grep -r "CommitNewEventsAsync" --include="*.cs" src/Application/

# Find aggregate creation in handlers
grep -r "\.Create(" --include="*.cs" src/Application/Features/

# Find LoadFromHistory in handlers
grep -r "LoadFromHistory" --include="*.cs" src/Application/Features/

# Find handler file structure
find src/Application/Features/Commands -name "*Handler.cs"
```

## Adding to Existing Project

1. **Create feature folder** under `Application/Features/Commands/{Entity}/{Action}/`
2. **Add command record** implementing `IRequest` and domain command interface
3. **Add handler class** with primary constructor injecting `ICommitEventService` and `IUnitOfWork`
4. **Follow the create/update pattern**: check existence, create or load aggregate, apply, commit
5. **Add gRPC mapping** in the appropriate gRPC service class
6. **Use resource strings** (`Phrases.xxx`) for response messages and exception messages
7. **Domain exceptions** implement `IProblemDetailsProvider` for automatic gRPC status code mapping
