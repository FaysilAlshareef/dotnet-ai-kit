---
name: clean-architecture
description: >
  4-layer Clean Architecture pattern with dependency rules. Domain, Application,
  Infrastructure, and Presentation layers with dependency inversion.
  Trigger: clean architecture, layers, dependency inversion, use cases.
category: architecture
agent: dotnet-architect
---

# Clean Architecture

## Core Principles

- Dependencies point inward: outer layers depend on inner layers, never the reverse
- Domain layer has zero external dependencies — pure C#
- Application layer defines interfaces that Infrastructure implements
- Presentation layer is the composition root where DI wires everything together
- One use case per handler — Application layer orchestrates domain logic

## Layer Structure

```
src/
  {Company}.{Domain}.Domain/           # Entities, value objects, domain events, interfaces
  {Company}.{Domain}.Application/      # Commands, queries, handlers, DTOs, validators
  {Company}.{Domain}.Infrastructure/   # EF Core, external services, file system
  {Company}.{Domain}.WebApi/           # Endpoints, middleware, DI composition root
```

### Dependency Rules

```
WebApi → Infrastructure → Application → Domain
                                ↑
WebApi → Application → Domain
```

- `Domain` references nothing
- `Application` references `Domain`
- `Infrastructure` references `Application` + `Domain`
- `WebApi` references all layers (composition root)

## Patterns

### Domain Layer

```csharp
// Domain/Entities/Order.cs
namespace {Company}.{Domain}.Domain.Entities;

public sealed class Order : BaseEntity, IAggregateRoot
{
    public string CustomerName { get; private set; } = default!;
    public OrderStatus Status { get; private set; } = OrderStatus.Draft;
    public decimal Total { get; private set; }

    private readonly List<OrderItem> _items = [];
    public IReadOnlyList<OrderItem> Items => _items.AsReadOnly();

    private Order() { } // EF Core constructor

    public static Order Create(string customerName)
    {
        var order = new Order { CustomerName = customerName };
        order.AddDomainEvent(new OrderCreatedEvent(order.Id));
        return order;
    }

    public void AddItem(Guid productId, int quantity, decimal price)
    {
        Guard.Against.NegativeOrZero(quantity);
        _items.Add(new OrderItem(productId, quantity, price));
        Total = _items.Sum(i => i.Quantity * i.Price);
    }
}

// Domain/Interfaces/IOrderRepository.cs
public interface IOrderRepository
{
    Task<Order?> FindAsync(Guid id, CancellationToken ct = default);
    Task<List<Order>> ListAsync(CancellationToken ct = default);
    void Add(Order order);
}

// Domain/Interfaces/IUnitOfWork.cs
public interface IUnitOfWork
{
    Task<int> SaveChangesAsync(CancellationToken ct = default);
}
```

### Application Layer

```csharp
// Application/Orders/Commands/CreateOrder/CreateOrderCommand.cs
namespace {Company}.{Domain}.Application.Orders.Commands.CreateOrder;

public sealed record CreateOrderCommand(string CustomerName) : IRequest<Guid>;

// Application/Orders/Commands/CreateOrder/CreateOrderCommandHandler.cs
internal sealed class CreateOrderCommandHandler(
    IOrderRepository repository,
    IUnitOfWork unitOfWork) : IRequestHandler<CreateOrderCommand, Guid>
{
    public async Task<Guid> Handle(
        CreateOrderCommand request, CancellationToken ct)
    {
        var order = Order.Create(request.CustomerName);
        repository.Add(order);
        await unitOfWork.SaveChangesAsync(ct);
        return order.Id;
    }
}

// Application/Orders/Commands/CreateOrder/CreateOrderCommandValidator.cs
public sealed class CreateOrderCommandValidator
    : AbstractValidator<CreateOrderCommand>
{
    public CreateOrderCommandValidator()
    {
        RuleFor(x => x.CustomerName).NotEmpty().MaximumLength(200);
    }
}
```

### Infrastructure Layer

```csharp
// Infrastructure/Persistence/AppDbContext.cs
namespace {Company}.{Domain}.Infrastructure.Persistence;

internal sealed class AppDbContext(
    DbContextOptions<AppDbContext> options) : DbContext(options), IUnitOfWork
{
    public DbSet<Order> Orders => Set<Order>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(
            typeof(AppDbContext).Assembly);
    }
}

// Infrastructure/Persistence/Repositories/OrderRepository.cs
internal sealed class OrderRepository(AppDbContext db) : IOrderRepository
{
    public async Task<Order?> FindAsync(Guid id, CancellationToken ct)
        => await db.Orders
            .Include(o => o.Items)
            .FirstOrDefaultAsync(o => o.Id == id, ct);

    public async Task<List<Order>> ListAsync(CancellationToken ct)
        => await db.Orders.ToListAsync(ct);

    public void Add(Order order) => db.Orders.Add(order);
}

// Infrastructure/DependencyInjection.cs
public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services, IConfiguration configuration)
    {
        services.AddDbContext<AppDbContext>(options =>
            options.UseSqlServer(
                configuration.GetConnectionString("Default")));

        services.AddScoped<IUnitOfWork>(sp =>
            sp.GetRequiredService<AppDbContext>());
        services.AddScoped<IOrderRepository, OrderRepository>();

        return services;
    }
}
```

### WebApi Layer (Composition Root)

```csharp
// WebApi/Program.cs
var builder = WebApplication.CreateBuilder(args);

builder.Services
    .AddApplicationServices()
    .AddInfrastructure(builder.Configuration);

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddOpenApi();

var app = builder.Build();

app.MapOpenApi();
app.MapEndpointGroups();
app.Run();
```

## Anti-Patterns

- Domain layer referencing EF Core or any infrastructure package
- Application layer creating infrastructure objects (e.g., `new SqlConnection`)
- Business logic in controllers or endpoints
- Returning domain entities from API endpoints (use DTOs)
- Infrastructure interfaces defined in Infrastructure (should be in Application/Domain)
- Circular references between layers

## Detect Existing Patterns

1. Look for separate projects named `Domain`, `Application`, `Infrastructure`, `WebApi`/`Api`/`Presentation`
2. Check project references: Infrastructure should reference Application, not vice versa
3. Look for repository interfaces in Domain, implementations in Infrastructure
4. Check for `IUnitOfWork` interface in Domain or Application layer
5. Verify domain entities have no `using` statements for EF Core or infrastructure

## Adding to Existing Project

1. **Create the four projects** with correct naming: `{Company}.{Domain}.{Layer}`
2. **Move entities** to Domain — remove any infrastructure dependencies
3. **Extract interfaces** for repositories and external services into Domain/Application
4. **Move handlers** to Application — ensure they depend only on interfaces
5. **Move implementations** to Infrastructure — EF Core, repositories, external clients
6. **Set up composition root** in WebApi with DI registration extension methods
7. **Verify project references** follow the dependency rule

## Decision Guide

| Question | Answer |
|----------|--------|
| Where do entities go? | Domain |
| Where do repository interfaces go? | Domain (per aggregate root) |
| Where do DTOs go? | Application |
| Where do MediatR handlers go? | Application |
| Where does DbContext go? | Infrastructure |
| Where does DI registration go? | Each layer has its own + WebApi composes |
| Where does validation go? | Application (FluentValidation) |

## References

- https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures#clean-architecture
- https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
