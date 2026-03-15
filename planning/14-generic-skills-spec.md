# dotnet-ai-kit - Generic .NET Skills Specification

## Overview

This document specifies the code patterns and content for each generic .NET skill (Categories 1-8, 32 skills).
These skills apply to BOTH microservice and generic .NET projects.

Each actual skill file will be a `SKILL.md` (max 400 lines) with YAML frontmatter, following the format in `02-skills-inventory.md`.
This spec provides the patterns and code examples that each skill must teach.

---

## CATEGORY 1: Core Language & Style (4 skills)

---

### `core/modern-csharp` — Modern C# Features

**Purpose**: Teach C# 12/13/14 language features that AI tools should prefer when generating code.
Covers primary constructors, collection expressions, pattern matching, records, raw string literals,
and the `field` keyword. Version-gated so .NET 8 projects don't get .NET 10-only syntax.

**Packages**: None (language features only)

**Key Patterns**:
- Primary constructors on classes and structs (.NET 8+/C# 12)
- Collection expressions `[1, 2, 3]` and spread `[..existing, newItem]` (C# 12)
- Records and record structs for DTOs and value objects
- Raw string literals `"""` for multi-line strings and JSON
- Pattern matching: list patterns `[first, .., last]`, property patterns, switch expressions
- `required` modifier on properties (C# 11+)
- `field` keyword in property accessors (C# 14 / .NET 10 preview)
- `using` aliases for generic types: `using UserList = System.Collections.Generic.List<User>;` (C# 12)
- Extension types (C# 14 / .NET 10 preview)

**Code Example**:
```csharp
// Primary constructor (.NET 8+ / C# 12)
public sealed class OrderService(IOrderRepository repository, ILogger<OrderService> logger)
{
    public async Task<Order?> GetAsync(Guid id)
    {
        logger.LogInformation("Fetching order {OrderId}", id);
        return await repository.FindAsync(id);
    }
}

// Collection expressions (C# 12)
int[] numbers = [1, 2, 3];
List<string> merged = [..existing, ..additional, "extra"];

// Record for immutable DTOs
public sealed record OrderResponse(Guid Id, string CustomerName, decimal Total);

// Pattern matching with switch expression
string status = order.State switch
{
    OrderState.Pending when order.Total > 1000 => "Requires approval",
    OrderState.Pending => "Awaiting processing",
    OrderState.Shipped => "In transit",
    OrderState.Delivered => "Complete",
    _ => "Unknown"
};

// field keyword (C# 14 / .NET 10)
public string Name
{
    get => field;
    set => field = value?.Trim() ?? throw new ArgumentNullException(nameof(value));
}
```

**Detection**: How to detect if existing project uses this pattern
- Check `<LangVersion>` in `.csproj` or `Directory.Build.props`
- Check `<TargetFramework>` for `net8.0`, `net9.0`, `net10.0`
- Scan for existing primary constructor usage in `.cs` files
- Look for `record` keyword usage in models/DTOs

**Reference**: https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/

---

### `core/coding-conventions` — .NET Coding Conventions

**Purpose**: Define company-agnostic coding conventions for consistent .NET code generation.
Covers naming, formatting, accessibility modifiers, sealed classes, expression bodies,
and file-scoped namespaces. AI tools use this to match existing project style.

**Packages**: None

**Key Patterns**:
- File-scoped namespaces (`namespace X;` not `namespace X { }`)
- `sealed` on classes that are not designed for inheritance
- `readonly` on fields and structs where appropriate
- Expression-bodied members for single-line methods/properties
- Naming: `PascalCase` types/methods/properties, `camelCase` parameters/locals, `_camelCase` private fields
- Constants: `PascalCase` (not `UPPER_SNAKE`)
- Async suffix on async methods (`GetOrderAsync`, not `GetOrder`)
- Use `var` when the type is apparent from the right-hand side
- Prefer `is null` / `is not null` over `== null` / `!= null`
- One class per file, file name matches class name
- Organize usings: `System.*` first, then third-party, then project

**Code Example**:
```csharp
namespace MyApp.Features.Orders;

public sealed class OrderService(
    IOrderRepository _repository,
    ILogger<OrderService> _logger)
{
    private const string DefaultCurrency = "USD";

    public async Task<OrderResponse?> GetOrderAsync(Guid orderId)
    {
        var order = await _repository.FindAsync(orderId);
        return order is null ? null : MapToResponse(order);
    }

    private static OrderResponse MapToResponse(Order order) => new(
        Id: order.Id,
        CustomerName: order.CustomerName,
        Total: order.Total);
}
```

**Detection**: How to detect if existing project uses this pattern
- Check `.editorconfig` for style rules
- Scan existing files for naming conventions (private field prefix `_` vs none)
- Check if `sealed` is used on non-abstract classes
- Check for file-scoped vs block-scoped namespaces

**Reference**: https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/coding-style/coding-conventions

---

### `core/dependency-injection` — Dependency Injection

**Purpose**: Teach the built-in Microsoft DI container patterns including service lifetimes,
keyed services (.NET 8+), decorator pattern, factory delegates, and registration organization.
Covers anti-patterns like captive dependencies and service locator.

**Packages**:
- `Microsoft.Extensions.DependencyInjection` (built-in with ASP.NET Core)

**Key Patterns**:
- Lifetime selection: Singleton vs Scoped vs Transient decision guide
- Keyed services with `[FromKeyedServices("key")]` (.NET 8+)
- Service registration extension methods (`AddApplicationServices()`)
- Decorator pattern using `Decorate<TInterface, TDecorator>()`
- Factory delegates for complex construction
- `IServiceScopeFactory` for background service scoping
- Open generic registration (`AddScoped(typeof(IRepository<>), typeof(Repository<>))`)
- Anti-patterns: captive dependency, service locator, resolving in constructor

**Code Example**:
```csharp
// Registration extension method
public static class DependencyInjection
{
    public static IServiceCollection AddApplicationServices(this IServiceCollection services)
    {
        // Standard registrations
        services.AddScoped<IOrderService, OrderService>();

        // Open generics
        services.AddScoped(typeof(IRepository<>), typeof(EfRepository<>));

        // Keyed services (.NET 8+)
        services.AddKeyedSingleton<IPaymentGateway, StripeGateway>("stripe");
        services.AddKeyedSingleton<IPaymentGateway, PayPalGateway>("paypal");

        // Factory delegate
        services.AddScoped<IReportGenerator>(sp =>
        {
            var config = sp.GetRequiredService<IOptions<ReportOptions>>().Value;
            return config.Format switch
            {
                "pdf" => new PdfReportGenerator(sp.GetRequiredService<ILogger<PdfReportGenerator>>()),
                "csv" => new CsvReportGenerator(),
                _ => throw new InvalidOperationException($"Unknown format: {config.Format}")
            };
        });

        return services;
    }
}

// Consuming keyed service
public sealed class CheckoutService(
    [FromKeyedServices("stripe")] IPaymentGateway gateway)
{
    public Task ChargeAsync(decimal amount) => gateway.ChargeAsync(amount);
}

// Decorator pattern
services.AddScoped<IOrderService, OrderService>();
services.Decorate<IOrderService, CachedOrderService>();
services.Decorate<IOrderService, LoggingOrderService>();
```

**Detection**: How to detect if existing project uses this pattern
- Search for `builder.Services.Add` calls in `Program.cs`
- Look for `IServiceCollection` extension methods
- Check for `[FromKeyedServices]` usage (indicates .NET 8+ keyed DI)
- Search for `AddScoped`, `AddTransient`, `AddSingleton` patterns

**Reference**: https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection

---

### `core/configuration` — Configuration & Options Pattern

**Purpose**: Teach the Options pattern for strongly-typed configuration, including `IOptions<T>`,
`IOptionsSnapshot<T>`, `IOptionsMonitor<T>`, validation with `ValidateOnStart`, secrets
management, and environment-specific configuration files.

**Packages**:
- `Microsoft.Extensions.Options` (built-in)
- `Microsoft.Extensions.Options.DataAnnotations` (built-in)

**Key Patterns**:
- Options classes with `[Required]`, `[Range]`, `[Url]` data annotations
- `ValidateDataAnnotations().ValidateOnStart()` for fail-fast
- `IOptions<T>` (singleton), `IOptionsSnapshot<T>` (scoped, reloads), `IOptionsMonitor<T>` (singleton, change notification)
- `IValidateOptions<T>` for complex validation logic
- `appsettings.json` → `appsettings.{Environment}.json` layering
- User secrets for development (`dotnet user-secrets`)
- Environment variables and `__` separator convention
- Configuration sections binding

**Code Example**:
```csharp
// Options class
public sealed class DatabaseOptions
{
    public const string SectionName = "Database";

    [Required]
    public required string ConnectionString { get; init; }

    [Range(1, 100)]
    public int MaxRetryCount { get; init; } = 3;

    [Range(1, 3600)]
    public int CommandTimeoutSeconds { get; init; } = 30;
}

// Registration with validation
services.AddOptions<DatabaseOptions>()
    .BindConfiguration(DatabaseOptions.SectionName)
    .ValidateDataAnnotations()
    .ValidateOnStart();

// Complex validation
public sealed class DatabaseOptionsValidator : IValidateOptions<DatabaseOptions>
{
    public ValidateOptionsResult Validate(string? name, DatabaseOptions options)
    {
        if (options.ConnectionString.Contains("password=", StringComparison.OrdinalIgnoreCase)
            && !options.ConnectionString.Contains("Encrypt=true", StringComparison.OrdinalIgnoreCase))
        {
            return ValidateOptionsResult.Fail("Connections with passwords must use encryption.");
        }
        return ValidateOptionsResult.Success;
    }
}

// Consuming options
public sealed class DataService(IOptions<DatabaseOptions> options)
{
    private readonly DatabaseOptions _options = options.Value;
}
```

**Detection**: How to detect if existing project uses this pattern
- Search for `IOptions<`, `IOptionsSnapshot<`, `IOptionsMonitor<` in constructors
- Check for `BindConfiguration` or `Bind` calls in `Program.cs`
- Look for `ValidateOnStart` or `ValidateDataAnnotations` calls
- Check `appsettings.json` for configuration sections

**Reference**: https://learn.microsoft.com/en-us/dotnet/core/extensions/options

---

## CATEGORY 2: Architecture (5 skills)

---

### `architecture/advisor` — Architecture Advisor

**Purpose**: Interactive questionnaire that recommends the right architecture based on project needs.
Evaluates team size, complexity, deployment model, scalability needs, and domain complexity
to recommend VSA, Clean Architecture, DDD, Modular Monolith, or Microservices.

**Packages**: None (decision framework, not code)

**Key Patterns**:
- Decision matrix: complexity vs team size vs deployment needs
- VSA: small team, single deployment, moderate complexity, rapid iteration
- Clean Architecture: medium team, clear domain logic, testability priority
- DDD: complex domain, multiple bounded contexts, domain experts available
- Modular Monolith: medium team, future microservice migration path, shared database
- Microservices: large team, independent deployment, high scalability, event-driven
- Questions to ask: team size, domain complexity, deployment requirements, integration count, scalability needs
- Red flags: premature microservices, over-abstracted monolith, DDD without domain experts

**Code Example**:
```
Decision Flow:

1. Team size?
   ≤3 devs → lean toward VSA
   4-8 devs → Clean Arch or Modular Monolith
   8+ devs with separate teams → Microservices candidate

2. Domain complexity?
   CRUD-heavy → VSA
   Moderate business rules → Clean Architecture
   Complex domain with invariants → DDD + Clean Arch
   Multiple bounded contexts → DDD + Modular Monolith or Microservices

3. Deployment requirements?
   Single unit OK → Monolith (VSA, Clean Arch, Modular Monolith)
   Independent scaling/deployment needed → Microservices

4. Expected lifespan?
   Prototype / <1 year → VSA
   Long-lived product → Clean Arch or DDD
   Platform with evolving teams → Modular Monolith → Microservices
```

**Detection**: How to detect if existing project uses this pattern
- Scan solution structure for layer folders (`Domain`, `Application`, `Infrastructure`, `Presentation`)
- Check for `Features/` folder structure (VSA)
- Look for `Modules/` folder structure (Modular Monolith)
- Check for multiple `.sln` files or separate repos (Microservices)

**Reference**: https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/

---

### `architecture/vertical-slice` — Vertical Slice Architecture

**Purpose**: Teach feature-folder organization where each feature is self-contained with its own
request, handler, validator, and response. Minimal ceremony, no layer abstractions.
Uses MediatR for handler dispatch and keeps all feature code in one place.

**Packages**:
- `MediatR` (13.x)
- `FluentValidation.DependencyInjectionExtensions` (11.x)

**Key Patterns**:
- Feature folder structure: `Features/{Feature}/{Operation}.cs`
- Single file per operation containing: Request, Response, Handler, Validator
- MediatR `IRequest<T>` and `IRequestHandler<TRequest, TResult>`
- No repository abstraction — handler talks to DbContext directly
- Endpoint maps directly to handler
- Shared kernel for cross-cutting: `Common/`, `Shared/`
- When to break the pattern: shared query logic → extract to extension method

**Code Example**:
```csharp
// Features/Orders/CreateOrder.cs — everything in one file
namespace MyApp.Features.Orders;

public static class CreateOrder
{
    public sealed record Command(string CustomerName, List<LineItem> Items) : IRequest<Result>;
    public sealed record LineItem(Guid ProductId, int Quantity);
    public sealed record Result(Guid OrderId);

    public sealed class Validator : AbstractValidator<Command>
    {
        public Validator()
        {
            RuleFor(x => x.CustomerName).NotEmpty().MaximumLength(200);
            RuleFor(x => x.Items).NotEmpty();
            RuleForEach(x => x.Items).ChildRules(item =>
            {
                item.RuleFor(x => x.Quantity).GreaterThan(0);
            });
        }
    }

    internal sealed class Handler(AppDbContext db) : IRequestHandler<Command, Result>
    {
        public async Task<Result> Handle(Command request, CancellationToken ct)
        {
            var order = new Order
            {
                CustomerName = request.CustomerName,
                Items = request.Items.Select(i => new OrderItem
                {
                    ProductId = i.ProductId, Quantity = i.Quantity
                }).ToList()
            };

            db.Orders.Add(order);
            await db.SaveChangesAsync(ct);
            return new Result(order.Id);
        }
    }
}

// Endpoint registration
app.MapPost("/orders", async (CreateOrder.Command cmd, ISender sender) =>
{
    var result = await sender.Send(cmd);
    return TypedResults.Created($"/orders/{result.OrderId}", result);
});
```

**Detection**: How to detect if existing project uses this pattern
- Check for `Features/` folder structure with operation-named files
- Look for static classes containing nested `Command`, `Query`, `Handler`
- Verify MediatR usage without repository abstractions
- Check if handlers reference `DbContext` directly

**Reference**: https://www.jimmybogard.com/vertical-slice-architecture/

---

### `architecture/clean-architecture` — Clean Architecture

**Purpose**: Teach the 4-layer Clean Architecture pattern with proper dependency inversion.
Domain at the center, Application layer for use cases, Infrastructure for external concerns,
and Presentation (API) as the entry point. All dependencies point inward.

**Packages**:
- `MediatR` (13.x)
- `FluentValidation.DependencyInjectionExtensions` (11.x)
- `Microsoft.EntityFrameworkCore` (infrastructure layer)

**Key Patterns**:
- 4 projects: `Domain`, `Application`, `Infrastructure`, `WebApi`
- Domain: entities, value objects, domain events, repository interfaces, domain exceptions
- Application: commands, queries, handlers, DTOs, validators, interfaces (`IUnitOfWork`)
- Infrastructure: EF Core DbContext, repository implementations, external service clients
- WebApi: controllers/endpoints, middleware, DI composition root
- Dependency rule: inner layers never reference outer layers
- `Application` references only `Domain`; `Infrastructure` references `Application`+`Domain`

**Code Example**:
```csharp
// Domain/Entities/Order.cs
public sealed class Order : BaseEntity, IAggregateRoot
{
    public string CustomerName { get; private set; } = default!;
    private readonly List<OrderItem> _items = [];
    public IReadOnlyList<OrderItem> Items => _items.AsReadOnly();

    public static Order Create(string customerName)
    {
        var order = new Order { CustomerName = customerName };
        order.AddDomainEvent(new OrderCreatedEvent(order.Id));
        return order;
    }

    public void AddItem(Guid productId, int quantity, decimal price)
    {
        _items.Add(new OrderItem(productId, quantity, price));
    }
}

// Domain/Interfaces/IOrderRepository.cs
public interface IOrderRepository
{
    Task<Order?> FindAsync(Guid id, CancellationToken ct = default);
    void Add(Order order);
}

// Application/Orders/Commands/CreateOrder/CreateOrderCommand.cs
public sealed record CreateOrderCommand(string CustomerName) : IRequest<Guid>;

// Application/Orders/Commands/CreateOrder/CreateOrderCommandHandler.cs
internal sealed class CreateOrderCommandHandler(
    IOrderRepository repository,
    IUnitOfWork unitOfWork) : IRequestHandler<CreateOrderCommand, Guid>
{
    public async Task<Guid> Handle(CreateOrderCommand request, CancellationToken ct)
    {
        var order = Order.Create(request.CustomerName);
        repository.Add(order);
        await unitOfWork.SaveChangesAsync(ct);
        return order.Id;
    }
}

// Infrastructure/Repositories/OrderRepository.cs
internal sealed class OrderRepository(AppDbContext db) : IOrderRepository
{
    public async Task<Order?> FindAsync(Guid id, CancellationToken ct)
        => await db.Orders.Include(o => o.Items).FirstOrDefaultAsync(o => o.Id == id, ct);

    public void Add(Order order) => db.Orders.Add(order);
}
```

**Detection**: How to detect if existing project uses this pattern
- Look for separate projects named `Domain`, `Application`, `Infrastructure`, `WebApi`/`Api`/`Presentation`
- Check project references: Infrastructure should reference Application, not vice versa
- Look for repository interfaces in Domain, implementations in Infrastructure
- Check for `IUnitOfWork` interface in Application layer

**Reference**: https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures#clean-architecture

---

### `architecture/ddd` — Domain-Driven Design

**Purpose**: Teach tactical DDD patterns for .NET including aggregates, entities, value objects,
domain events, strongly-typed IDs, and rich domain models. Focuses on enforcing invariants
within aggregate boundaries and using domain events for cross-aggregate communication.

**Packages**:
- `MediatR` (for domain event dispatch)
- `StronglyTypedId` (optional, for source-generated typed IDs)

**Key Patterns**:
- Aggregate roots as consistency boundaries
- Entities with identity, value objects without
- Strongly-typed IDs (`OrderId` instead of `Guid`)
- Rich domain model: behavior on entities, not anemic CRUD
- Domain events raised within aggregates, dispatched on save
- Private setters, factory methods, guard clauses
- Value objects with `record` or `ValueObject` base class
- Repository per aggregate root (not per entity)

**Code Example**:
```csharp
// Strongly-typed ID
public readonly record struct OrderId(Guid Value)
{
    public static OrderId New() => new(Guid.NewGuid());
}

// Value Object
public sealed record Money(decimal Amount, string Currency)
{
    public static Money Zero(string currency) => new(0, currency);
    public Money Add(Money other)
    {
        if (Currency != other.Currency)
            throw new DomainException("Cannot add different currencies");
        return this with { Amount = Amount + other.Amount };
    }
}

// Aggregate Root
public sealed class Order : AggregateRoot<OrderId>
{
    public CustomerId CustomerId { get; private set; }
    public Money Total { get; private set; } = Money.Zero("USD");
    public OrderStatus Status { get; private set; } = OrderStatus.Draft;
    private readonly List<OrderLine> _lines = [];
    public IReadOnlyList<OrderLine> Lines => _lines.AsReadOnly();

    private Order() { } // EF Core

    public static Order Create(CustomerId customerId)
    {
        var order = new Order
        {
            Id = OrderId.New(),
            CustomerId = customerId
        };
        order.RaiseDomainEvent(new OrderCreatedEvent(order.Id));
        return order;
    }

    public void AddLine(ProductId productId, int quantity, Money unitPrice)
    {
        Guard.Against.NegativeOrZero(quantity);
        var line = new OrderLine(productId, quantity, unitPrice);
        _lines.Add(line);
        Total = _lines.Aggregate(Money.Zero("USD"), (sum, l) => sum.Add(l.LineTotal));
    }

    public void Submit()
    {
        if (Status != OrderStatus.Draft)
            throw new DomainException("Only draft orders can be submitted");
        if (_lines.Count == 0)
            throw new DomainException("Cannot submit empty order");
        Status = OrderStatus.Submitted;
        RaiseDomainEvent(new OrderSubmittedEvent(Id, Total));
    }
}

// Base class
public abstract class AggregateRoot<TId> where TId : struct
{
    public TId Id { get; protected set; }
    private readonly List<IDomainEvent> _domainEvents = [];
    public IReadOnlyList<IDomainEvent> DomainEvents => _domainEvents.AsReadOnly();

    protected void RaiseDomainEvent(IDomainEvent domainEvent) => _domainEvents.Add(domainEvent);
    public void ClearDomainEvents() => _domainEvents.Clear();
}
```

**Detection**: How to detect if existing project uses this pattern
- Look for `AggregateRoot`, `Entity`, `ValueObject` base classes
- Check for strongly-typed IDs (record structs wrapping `Guid`)
- Look for `DomainEvent` or `IDomainEvent` types
- Check for rich entities with behavior methods (not just properties)
- Look for private setters and factory methods (`Create`, `Register`)

**Reference**: https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/

---

### `architecture/project-structure` — Project Structure & Solution Organization

**Purpose**: Teach modern .NET solution organization including `.slnx` format, `Directory.Build.props`,
`Directory.Packages.props` (central package management), consistent project layout, and
shared build configuration across projects.

**Packages**: None (MSBuild/SDK features)

**Key Patterns**:
- `.slnx` solution format (.NET 9+) — XML-based, merge-friendly
- `Directory.Build.props` at solution root for shared properties
- `Directory.Packages.props` for central package management (CPM)
- `<ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>`
- Shared `<LangVersion>`, `<Nullable>enable</Nullable>`, `<ImplicitUsings>enable</ImplicitUsings>`
- `global.json` for SDK version pinning
- `nuget.config` for package source configuration
- Standard folder layout: `src/`, `tests/`, `docs/`

**Code Example**:
```xml
<!-- Directory.Build.props (solution root) -->
<Project>
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <LangVersion>latest</LangVersion>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>
  </PropertyGroup>
</Project>

<!-- Directory.Packages.props (central package management) -->
<Project>
  <PropertyGroup>
    <ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>
  </PropertyGroup>
  <ItemGroup>
    <PackageVersion Include="MediatR" Version="12.4.1" />
    <PackageVersion Include="FluentValidation.DependencyInjectionExtensions" Version="11.11.0" />
    <PackageVersion Include="Microsoft.EntityFrameworkCore" Version="9.0.1" />
    <PackageVersion Include="Serilog.AspNetCore" Version="9.0.0" />
  </ItemGroup>
</Project>

<!-- Individual .csproj uses PackageReference without Version -->
<ItemGroup>
  <PackageReference Include="MediatR" />
  <PackageReference Include="FluentValidation.DependencyInjectionExtensions" />
</ItemGroup>
```

```json
// global.json
{
  "sdk": {
    "version": "10.0.100",
    "rollForward": "latestFeature"
  }
}
```

**Detection**: How to detect if existing project uses this pattern
- Check for `Directory.Build.props` at solution root
- Check for `Directory.Packages.props` (central package management)
- Look at `.sln` vs `.slnx` format
- Check for `global.json`
- Scan `.csproj` files for `PackageReference` with/without `Version` attribute

**Reference**: https://learn.microsoft.com/en-us/dotnet/core/project-sdk/overview

---

## CATEGORY 3: Web API (5 skills)

---

### `api/minimal-api` — Minimal API Endpoints

**Purpose**: Teach the minimal API pattern with organized endpoint groups, typed results,
endpoint filters, and OpenAPI metadata. Covers the `IEndpointRouteBuilder` extension pattern
for auto-discovering and registering endpoint groups.

**Packages**:
- `Microsoft.AspNetCore.OpenApi` (built-in with .NET 9+)

**Key Patterns**:
- `IEndpointGroup` interface with `MapEndpoints(IEndpointRouteBuilder)` method
- Auto-discovery via reflection to register all endpoint groups
- `TypedResults` for compile-time-checked return types
- Endpoint filters for cross-cutting concerns (validation, logging)
- Route groups with shared prefix, filters, metadata
- Parameter binding: `[AsParameters]` for complex query objects
- `Results<Ok<T>, NotFound, BadRequest<ProblemDetails>>` union return types

**Code Example**:
```csharp
// IEndpointGroup interface
public interface IEndpointGroup
{
    void MapEndpoints(IEndpointRouteBuilder app);
}

// Auto-registration in Program.cs
app.MapEndpointGroups();

public static class EndpointGroupExtensions
{
    public static void MapEndpointGroups(this WebApplication app)
    {
        var groups = typeof(Program).Assembly
            .GetTypes()
            .Where(t => t.IsAssignableTo(typeof(IEndpointGroup)) && !t.IsInterface)
            .Select(Activator.CreateInstance)
            .Cast<IEndpointGroup>();

        foreach (var group in groups)
            group.MapEndpoints(app);
    }
}

// Endpoint group
public sealed class OrderEndpoints : IEndpointGroup
{
    public void MapEndpoints(IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/orders")
            .WithTags("Orders")
            .RequireAuthorization();

        group.MapGet("/", GetOrders).WithSummary("List orders with filtering");
        group.MapGet("/{id:guid}", GetOrder).WithSummary("Get order by ID");
        group.MapPost("/", CreateOrder).WithSummary("Create new order");
    }

    private static async Task<Ok<PagedList<OrderResponse>>> GetOrders(
        [AsParameters] OrderFilter filter,
        ISender sender)
    {
        var result = await sender.Send(new GetOrdersQuery(filter));
        return TypedResults.Ok(result);
    }

    private static async Task<Results<Ok<OrderResponse>, NotFound>> GetOrder(
        Guid id, ISender sender)
    {
        var result = await sender.Send(new GetOrderQuery(id));
        return result is not null
            ? TypedResults.Ok(result)
            : TypedResults.NotFound();
    }
}
```

**Detection**: How to detect if existing project uses this pattern
- Search for `MapGroup`, `MapGet`, `MapPost` in `Program.cs` or endpoint files
- Look for `IEndpointGroup` or `IEndpointRouteBuilder` extension methods
- Check for `TypedResults` usage
- Look for `WithTags`, `WithSummary`, `WithDescription` metadata calls

**Reference**: https://learn.microsoft.com/en-us/aspnet/core/fundamentals/minimal-apis

---

### `api/controllers` — RESTful Controllers

**Purpose**: Teach the controller-based API pattern with proper routing, HTTP method semantics,
MediatR integration, model binding, and response conventions. Covers both traditional
and modern controller patterns with `[ApiController]` attribute.

**Packages**:
- `MediatR` (13.x)
- `Microsoft.AspNetCore.Mvc.Versioning` (if combining with versioning)

**Key Patterns**:
- `[ApiController]` attribute for automatic model validation and binding
- RESTful route conventions: `[Route("api/[controller]")]`
- HTTP method attributes: `[HttpGet]`, `[HttpPost]`, `[HttpPut]`, `[HttpPatch]`, `[HttpDelete]`
- `ActionResult<T>` return types with `[ProducesResponseType]`
- MediatR integration: Send command/query from controller
- `CreatedAtAction` for 201 responses
- `ProblemDetails` for error responses (RFC 9457)
- Cancellation token propagation

**Code Example**:
```csharp
[ApiController]
[Route("api/[controller]")]
[Produces("application/json")]
public sealed class OrdersController(ISender sender) : ControllerBase
{
    [HttpGet]
    [ProducesResponseType(typeof(PagedList<OrderResponse>), StatusCodes.Status200OK)]
    public async Task<ActionResult<PagedList<OrderResponse>>> GetOrders(
        [FromQuery] OrderFilter filter,
        CancellationToken ct)
    {
        var result = await sender.Send(new GetOrdersQuery(filter), ct);
        return Ok(result);
    }

    [HttpGet("{id:guid}")]
    [ProducesResponseType(typeof(OrderResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<OrderResponse>> GetOrder(Guid id, CancellationToken ct)
    {
        var result = await sender.Send(new GetOrderQuery(id), ct);
        return result is not null ? Ok(result) : NotFound();
    }

    [HttpPost]
    [ProducesResponseType(typeof(OrderResponse), StatusCodes.Status201Created)]
    [ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<OrderResponse>> CreateOrder(
        CreateOrderRequest request,
        CancellationToken ct)
    {
        var result = await sender.Send(new CreateOrderCommand(request.CustomerName), ct);
        return CreatedAtAction(nameof(GetOrder), new { id = result.Id }, result);
    }
}
```

**Detection**: How to detect if existing project uses this pattern
- Search for `: ControllerBase` or `: Controller` class inheritance
- Look for `[ApiController]` attribute
- Check for `Controllers/` folder
- Look for `services.AddControllers()` in `Program.cs`

**Reference**: https://learn.microsoft.com/en-us/aspnet/core/web-api/

---

### `api/versioning` — API Versioning

**Purpose**: Teach API versioning strategies using the `Asp.Versioning` library. Covers URL segment,
query string, and header-based versioning with proper sunset policies and version negotiation.

**Packages**:
- `Asp.Versioning.Http` (for minimal APIs)
- `Asp.Versioning.Mvc.ApiExplorer` (for controllers + OpenAPI)

**Key Patterns**:
- URL segment versioning: `/api/v1/orders` (most common, recommended)
- Query string versioning: `/api/orders?api-version=1.0`
- Header versioning: `X-Api-Version: 1.0`
- Version sets and groups for minimal APIs
- `[ApiVersion("1.0")]`, `[MapToApiVersion("2.0")]` attributes for controllers
- Sunset policies for deprecated versions
- OpenAPI document per version
- Default version and version-neutral endpoints

**Code Example**:
```csharp
// Program.cs registration
builder.Services.AddApiVersioning(options =>
{
    options.DefaultApiVersion = new ApiVersion(1, 0);
    options.AssumeDefaultVersionWhenUnspecified = true;
    options.ReportApiVersions = true;
    options.ApiVersionReader = new UrlSegmentApiVersionReader();
})
.AddApiExplorer(options =>
{
    options.GroupNameFormat = "'v'VVV";
    options.SubstituteApiVersionInUrl = true;
});

// Controller versioning
[ApiController]
[Route("api/v{version:apiVersion}/orders")]
[ApiVersion("1.0")]
[ApiVersion("2.0")]
public sealed class OrdersController(ISender sender) : ControllerBase
{
    [HttpGet]
    [MapToApiVersion("1.0")]
    public async Task<ActionResult<List<OrderV1Response>>> GetOrdersV1() { /* ... */ }

    [HttpGet]
    [MapToApiVersion("2.0")]
    public async Task<ActionResult<PagedList<OrderV2Response>>> GetOrdersV2(
        [FromQuery] OrderFilter filter) { /* ... */ }
}

// Minimal API versioning
var versionSet = app.NewApiVersionSet()
    .HasApiVersion(new ApiVersion(1, 0))
    .HasApiVersion(new ApiVersion(2, 0))
    .ReportApiVersions()
    .Build();

app.MapGet("/api/v{version:apiVersion}/orders", GetOrders)
    .WithApiVersionSet(versionSet)
    .MapToApiVersion(new ApiVersion(1, 0));
```

**Detection**: How to detect if existing project uses this pattern
- Search for `Asp.Versioning` package reference in `.csproj`
- Look for `AddApiVersioning` in `Program.cs`
- Check for `[ApiVersion]` attributes on controllers
- Look for `v{version:apiVersion}` in route templates

**Reference**: https://github.com/dotnet/aspnet-api-versioning

---

### `api/openapi` — OpenAPI / Swagger Specification

**Purpose**: Teach native OpenAPI support in .NET 9+ including document generation, schema transformers,
operation transformers, security scheme definitions, and XML comment integration.
Replaces Swashbuckle with built-in `Microsoft.AspNetCore.OpenApi`.

**Packages**:
- `Microsoft.AspNetCore.OpenApi` (built-in .NET 9+)
- `Microsoft.Extensions.ApiDescription.Server` (for build-time generation)

**Key Patterns**:
- `builder.Services.AddOpenApi()` with document customization
- Schema transformers for custom type mapping
- Operation transformers for adding security requirements
- Document transformers for global metadata (title, version, servers)
- `[EndpointSummary]`, `[EndpointDescription]` attributes
- XML doc comment integration via `<GenerateDocumentationFile>true</GenerateDocumentationFile>`
- Multiple OpenAPI documents (per version, per audience)
- Build-time document generation for CI

**Code Example**:
```csharp
// Program.cs
builder.Services.AddOpenApi("v1", options =>
{
    options.AddDocumentTransformer((document, context, ct) =>
    {
        document.Info = new OpenApiInfo
        {
            Title = "Order Management API",
            Version = "v1",
            Description = "API for managing customer orders"
        };
        return Task.CompletedTask;
    });

    // Add JWT security scheme
    options.AddDocumentTransformer<BearerSecuritySchemeTransformer>();
});

// Security scheme transformer
internal sealed class BearerSecuritySchemeTransformer(
    IAuthenticationSchemeProvider schemeProvider) : IOpenApiDocumentTransformer
{
    public async Task TransformAsync(OpenApiDocument document,
        OpenApiDocumentTransformerContext context, CancellationToken ct)
    {
        var schemes = await schemeProvider.GetAllSchemesAsync();
        if (schemes.Any(s => s.Name == JwtBearerDefaults.AuthenticationScheme))
        {
            document.Components ??= new OpenApiComponents();
            document.Components.SecuritySchemes["Bearer"] = new OpenApiSecurityScheme
            {
                Type = SecuritySchemeType.Http,
                Scheme = "bearer",
                BearerFormat = "JWT"
            };
        }
    }
}

// Map the document
app.MapOpenApi(); // serves at /openapi/v1.json
```

**Detection**: How to detect if existing project uses this pattern
- Search for `AddOpenApi` in `Program.cs` (native .NET 9+)
- Search for `AddSwaggerGen` (Swashbuckle, legacy)
- Check for `Microsoft.AspNetCore.OpenApi` package
- Look for `MapOpenApi()` endpoint mapping

**Reference**: https://learn.microsoft.com/en-us/aspnet/core/fundamentals/openapi/overview

---

### `api/scalar` — Scalar API Documentation UI

**Purpose**: Teach Scalar setup as the modern replacement for Swagger UI. Covers theme configuration,
authentication prefill, proxy for OpenAPI spec, and integration with .NET's native OpenAPI support.

**Packages**:
- `Scalar.AspNetCore` (latest)
- `Microsoft.AspNetCore.OpenApi` (required for spec generation)

**Key Patterns**:
- `app.MapScalarApiReference()` for UI endpoint
- Theme selection (`BluePlanet`, `Mars`, `Saturn`, etc.)
- Authentication prefill (Bearer token, API key)
- Custom CSS and branding
- Proxy configuration for CORS
- Separate Scalar instances per OpenAPI document (versioned APIs)
- Restrict access in production (basic auth middleware)

**Code Example**:
```csharp
// Program.cs
builder.Services.AddOpenApi();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
    app.MapScalarApiReference(options =>
    {
        options
            .WithTitle("Order Management API")
            .WithTheme(ScalarTheme.BluePlanet)
            .WithDefaultHttpClient(ScalarTarget.CSharp, ScalarClient.HttpClient)
            .WithPreferredScheme("Bearer")
            .WithHttpBearerAuthentication(bearer =>
            {
                bearer.Token = "your-dev-token-here";
            });
    });
}

// Production with basic auth protection
if (!app.Environment.IsDevelopment())
{
    app.MapOpenApi().RequireAuthorization("ApiDocAccess");
    app.MapScalarApiReference().RequireAuthorization("ApiDocAccess");
}
```

**Detection**: How to detect if existing project uses this pattern
- Search for `Scalar.AspNetCore` package in `.csproj`
- Look for `MapScalarApiReference` in `Program.cs`
- Check for `ScalarTheme` configuration
- Check for `MapSwagger` (legacy, suggests migration candidate)

**Reference**: https://github.com/scalar/scalar/tree/main/integrations/aspnetcore

---

## CATEGORY 4: Data Access (5 skills)

---

### `data/ef-core` — Entity Framework Core

**Purpose**: Teach comprehensive EF Core patterns including DbContext configuration, migrations,
interceptors, compiled queries, value converters, concurrency tokens, and performance best
practices. Covers both SQL Server and PostgreSQL providers.

**Packages**:
- `Microsoft.EntityFrameworkCore` (9.x / 10.x)
- `Microsoft.EntityFrameworkCore.SqlServer` or `Npgsql.EntityFrameworkCore.PostgreSQL`
- `Microsoft.EntityFrameworkCore.Tools` (migrations CLI)

**Key Patterns**:
- `DbContext` with `IDesignTimeDbContextFactory` for migrations
- `IEntityTypeConfiguration<T>` for fluent configuration (separate files)
- Shadow properties for audit fields
- Value converters for strongly-typed IDs and enums
- Row version / concurrency tokens (`[Timestamp]` or `.IsRowVersion()`)
- `SaveChangesInterceptor` for domain event dispatch and audit trails
- Compiled queries for hot paths (`EF.CompileAsyncQuery`)
- Split queries for N+1 prevention
- Global query filters for soft delete
- Connection resiliency with `EnableRetryOnFailure`

**Code Example**:
```csharp
// DbContext
public sealed class AppDbContext(DbContextOptions<AppDbContext> options)
    : DbContext(options)
{
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<Product> Products => Set<Product>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(AppDbContext).Assembly);
    }
}

// Entity configuration
internal sealed class OrderConfiguration : IEntityTypeConfiguration<Order>
{
    public void Configure(EntityTypeBuilder<Order> builder)
    {
        builder.HasKey(o => o.Id);
        builder.Property(o => o.Id)
            .HasConversion(id => id.Value, value => new OrderId(value));
        builder.Property(o => o.CustomerName).HasMaxLength(200).IsRequired();
        builder.Property(o => o.RowVersion).IsRowVersion();
        builder.HasMany(o => o.Items).WithOne().HasForeignKey(i => i.OrderId);
        builder.HasQueryFilter(o => !o.IsDeleted); // soft delete
    }
}

// Registration with interceptors
builder.Services.AddDbContext<AppDbContext>((sp, options) =>
{
    options.UseSqlServer(connectionString, sql =>
    {
        sql.EnableRetryOnFailure(3);
        sql.CommandTimeout(30);
    });
    options.AddInterceptors(
        sp.GetRequiredService<DomainEventInterceptor>(),
        sp.GetRequiredService<AuditableInterceptor>());
});

// Domain event dispatch interceptor
public sealed class DomainEventInterceptor(IPublisher publisher) : SaveChangesInterceptor
{
    public override async ValueTask<int> SavedChangesAsync(
        SaveChangesCompletedEventData eventData, int result, CancellationToken ct = default)
    {
        var context = eventData.Context!;
        var entities = context.ChangeTracker.Entries<AggregateRoot<object>>()
            .Where(e => e.Entity.DomainEvents.Count != 0)
            .Select(e => e.Entity)
            .ToList();

        foreach (var entity in entities)
        {
            foreach (var domainEvent in entity.DomainEvents)
                await publisher.Publish(domainEvent, ct);
            entity.ClearDomainEvents();
        }
        return result;
    }
}
```

**Detection**: How to detect if existing project uses this pattern
- Search for `: DbContext` class inheritance
- Look for `UseSqlServer` or `UseNpgsql` in `Program.cs`
- Check for `Migrations/` folder
- Look for `IEntityTypeConfiguration<T>` implementations

**Reference**: https://learn.microsoft.com/en-us/ef/core/

---

### `data/repository-pattern` — Repository Pattern

**Purpose**: Teach the repository pattern with generic and specialized repositories, unit of work,
and proper EF Core integration. Repositories abstract data access per aggregate root, while
the unit of work coordinates transaction boundaries.

**Packages**:
- `Microsoft.EntityFrameworkCore` (underlying implementation)

**Key Patterns**:
- `IRepository<T>` generic interface with CRUD operations
- `IReadRepository<T>` for read-only access (CQRS read side)
- `IUnitOfWork` with `SaveChangesAsync` for transaction coordination
- Specialized repository interfaces per aggregate root
- EF Core implementation of generic repository
- Repository should return domain entities, not DTOs
- Anti-pattern: generic repository that exposes `IQueryable` (leaky abstraction)

**Code Example**:
```csharp
// Generic interfaces
public interface IRepository<T> where T : class, IAggregateRoot
{
    Task<T?> FindAsync(Guid id, CancellationToken ct = default);
    Task<List<T>> ListAsync(CancellationToken ct = default);
    void Add(T entity);
    void Update(T entity);
    void Remove(T entity);
}

public interface IUnitOfWork
{
    Task<int> SaveChangesAsync(CancellationToken ct = default);
}

// Specialized repository
public interface IOrderRepository : IRepository<Order>
{
    Task<Order?> FindWithItemsAsync(Guid id, CancellationToken ct = default);
    Task<List<Order>> FindByCustomerAsync(Guid customerId, CancellationToken ct = default);
}

// EF Core implementation
internal sealed class EfRepository<T>(AppDbContext db) : IRepository<T>
    where T : class, IAggregateRoot
{
    private readonly DbSet<T> _set = db.Set<T>();

    public async Task<T?> FindAsync(Guid id, CancellationToken ct)
        => await _set.FindAsync([id], ct);

    public async Task<List<T>> ListAsync(CancellationToken ct)
        => await _set.ToListAsync(ct);

    public void Add(T entity) => _set.Add(entity);
    public void Update(T entity) => _set.Update(entity);
    public void Remove(T entity) => _set.Remove(entity);
}

// UnitOfWork (DbContext IS the unit of work)
internal sealed class UnitOfWork(AppDbContext db) : IUnitOfWork
{
    public Task<int> SaveChangesAsync(CancellationToken ct) => db.SaveChangesAsync(ct);
}

// Specialized implementation
internal sealed class OrderRepository(AppDbContext db) : EfRepository<Order>(db), IOrderRepository
{
    public async Task<Order?> FindWithItemsAsync(Guid id, CancellationToken ct)
        => await db.Orders.Include(o => o.Items).FirstOrDefaultAsync(o => o.Id == id, ct);

    public async Task<List<Order>> FindByCustomerAsync(Guid customerId, CancellationToken ct)
        => await db.Orders.Where(o => o.CustomerId == customerId).ToListAsync(ct);
}
```

**Detection**: How to detect if existing project uses this pattern
- Search for `IRepository<` interface definitions
- Look for `IUnitOfWork` interface
- Check for `Repositories/` folder in Infrastructure project
- Look for repository injection in command/query handlers

**Reference**: https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/infrastructure-persistence-layer-design

---

### `data/dapper` — Dapper for Read-Optimized Queries

**Purpose**: Teach Dapper for high-performance read queries, multi-mapping, dynamic filtering,
pagination, and CTEs. Used alongside EF Core — EF for writes, Dapper for complex reads.

**Packages**:
- `Dapper` (2.x)
- `Microsoft.Data.SqlClient` or `Npgsql`

**Key Patterns**:
- `IDbConnectionFactory` for connection management
- Multi-mapping for joined queries (`splitOn`)
- `DynamicParameters` for optional filters
- Pagination with `OFFSET/FETCH` or `ROW_NUMBER()`
- Common Table Expressions (CTEs) for hierarchical queries
- Stored procedure execution
- Query objects that build SQL dynamically
- Transaction support with `IDbTransaction`

**Code Example**:
```csharp
// Connection factory
public interface IDbConnectionFactory
{
    IDbConnection CreateConnection();
}

internal sealed class SqlConnectionFactory(IOptions<DatabaseOptions> options)
    : IDbConnectionFactory
{
    public IDbConnection CreateConnection()
        => new SqlConnection(options.Value.ConnectionString);
}

// Query with multi-mapping and pagination
internal sealed class GetOrdersQueryHandler(IDbConnectionFactory connectionFactory)
    : IRequestHandler<GetOrdersQuery, PagedList<OrderResponse>>
{
    public async Task<PagedList<OrderResponse>> Handle(
        GetOrdersQuery request, CancellationToken ct)
    {
        using var connection = connectionFactory.CreateConnection();

        var parameters = new DynamicParameters();
        var whereClauses = new List<string>();

        if (!string.IsNullOrEmpty(request.CustomerName))
        {
            whereClauses.Add("o.CustomerName LIKE @CustomerName");
            parameters.Add("CustomerName", $"%{request.CustomerName}%");
        }

        if (request.MinTotal.HasValue)
        {
            whereClauses.Add("o.Total >= @MinTotal");
            parameters.Add("MinTotal", request.MinTotal.Value);
        }

        var where = whereClauses.Count > 0
            ? "WHERE " + string.Join(" AND ", whereClauses)
            : "";

        // Count query
        var countSql = $"SELECT COUNT(*) FROM Orders o {where}";
        var totalCount = await connection.ExecuteScalarAsync<int>(countSql, parameters);

        // Data query with pagination
        var dataSql = $"""
            SELECT o.Id, o.CustomerName, o.Total, o.CreatedAt,
                   i.Id, i.ProductName, i.Quantity, i.UnitPrice
            FROM Orders o
            LEFT JOIN OrderItems i ON o.Id = i.OrderId
            {where}
            ORDER BY o.CreatedAt DESC
            OFFSET @Offset ROWS FETCH NEXT @PageSize ROWS ONLY
            """;

        parameters.Add("Offset", (request.Page - 1) * request.PageSize);
        parameters.Add("PageSize", request.PageSize);

        var orderDict = new Dictionary<Guid, OrderResponse>();
        await connection.QueryAsync<OrderResponse, OrderItemResponse, OrderResponse>(
            dataSql,
            (order, item) =>
            {
                if (!orderDict.TryGetValue(order.Id, out var existing))
                {
                    existing = order;
                    orderDict[order.Id] = existing;
                }
                if (item is not null) existing.Items.Add(item);
                return existing;
            },
            parameters,
            splitOn: "Id");

        return new PagedList<OrderResponse>(orderDict.Values.ToList(), totalCount, request.Page, request.PageSize);
    }
}
```

**Detection**: How to detect if existing project uses this pattern
- Search for `Dapper` package in `.csproj`
- Look for `IDbConnection`, `SqlConnection`, or `NpgsqlConnection` usage
- Check for `QueryAsync`, `ExecuteAsync` method calls
- Look for raw SQL strings in handler files

**Reference**: https://github.com/DapperLib/Dapper

---

### `data/specification-pattern` — Specification Pattern

**Purpose**: Teach composable query specifications for reusable, testable query criteria. Specifications
encapsulate filtering, ordering, includes, and pagination into objects that can be combined and tested
independently of the database.

**Packages**:
- `Ardalis.Specification` (8.x) or custom implementation
- `Ardalis.Specification.EntityFrameworkCore` (8.x)

**Key Patterns**:
- `Specification<T>` base class with `Query` fluent builder
- Criteria (Where), Includes, OrderBy, Pagination in one object
- `IRepositoryBase<T>` that accepts specifications
- Composable specifications via inheritance or combination
- `SingleResultSpecification<T>` for single-entity queries
- Projection specifications (`Specification<T, TResult>`)

**Code Example**:
```csharp
// Specification definitions
public sealed class OrdersByCustomerSpec : Specification<Order>
{
    public OrdersByCustomerSpec(Guid customerId, int page, int pageSize)
    {
        Query
            .Where(o => o.CustomerId == customerId)
            .Include(o => o.Items)
            .OrderByDescending(o => o.CreatedAt)
            .Skip((page - 1) * pageSize)
            .Take(pageSize);
    }
}

public sealed class OrderByIdSpec : SingleResultSpecification<Order>
{
    public OrderByIdSpec(Guid orderId)
    {
        Query
            .Where(o => o.Id == orderId)
            .Include(o => o.Items)
            .AsSplitQuery();
    }
}

// Projection specification
public sealed class OrderSummarySpec : Specification<Order, OrderSummaryDto>
{
    public OrderSummarySpec(DateTime fromDate)
    {
        Query
            .Where(o => o.CreatedAt >= fromDate)
            .OrderByDescending(o => o.Total)
            .Select(o => new OrderSummaryDto(o.Id, o.CustomerName, o.Total));
    }
}

// Repository accepting specifications
public interface IReadRepository<T> where T : class
{
    Task<T?> FirstOrDefaultAsync(ISpecification<T> spec, CancellationToken ct = default);
    Task<List<T>> ListAsync(ISpecification<T> spec, CancellationToken ct = default);
    Task<int> CountAsync(ISpecification<T> spec, CancellationToken ct = default);
    Task<List<TResult>> ListAsync<TResult>(ISpecification<T, TResult> spec, CancellationToken ct = default);
}

// Usage in handler
internal sealed class GetOrdersHandler(IReadRepository<Order> repository)
    : IRequestHandler<GetOrdersQuery, PagedList<OrderSummaryDto>>
{
    public async Task<PagedList<OrderSummaryDto>> Handle(
        GetOrdersQuery request, CancellationToken ct)
    {
        var spec = new OrderSummarySpec(request.FromDate);
        var items = await repository.ListAsync(spec, ct);
        var count = await repository.CountAsync(spec, ct);
        return new PagedList<OrderSummaryDto>(items, count, request.Page, request.PageSize);
    }
}
```

**Detection**: How to detect if existing project uses this pattern
- Search for `Ardalis.Specification` package in `.csproj`
- Look for classes inheriting `Specification<T>`
- Check for `Specifications/` folder
- Look for `ISpecification<T>` usage in repositories

**Reference**: https://specification.ardalis.com/

---

### `data/audit-trail` — Audit Trail with EF Core Interceptors

**Purpose**: Teach automatic audit trail implementation using EF Core interceptors. Automatically
populates `CreatedAt`, `CreatedBy`, `UpdatedAt`, `UpdatedBy` on entities implementing `IAuditable`.
Optionally logs all changes to a separate audit table.

**Packages**:
- `Microsoft.EntityFrameworkCore` (built-in interceptors)

**Key Patterns**:
- `IAuditable` marker interface with audit properties
- `SaveChangesInterceptor` to auto-populate audit fields
- `ICurrentUserService` to resolve the current user
- Optional: `AuditLog` table recording field-level changes
- UTC timestamps, consistent across all entities
- Shadow properties as alternative to interface approach

**Code Example**:
```csharp
// Auditable interface
public interface IAuditable
{
    DateTimeOffset CreatedAt { get; }
    string? CreatedBy { get; }
    DateTimeOffset? UpdatedAt { get; }
    string? UpdatedBy { get; }
}

// Base entity implementing IAuditable
public abstract class AuditableEntity : IAuditable
{
    public DateTimeOffset CreatedAt { get; set; }
    public string? CreatedBy { get; set; }
    public DateTimeOffset? UpdatedAt { get; set; }
    public string? UpdatedBy { get; set; }
}

// Current user service
public interface ICurrentUserService
{
    string? UserId { get; }
}

internal sealed class CurrentUserService(IHttpContextAccessor httpContextAccessor)
    : ICurrentUserService
{
    public string? UserId => httpContextAccessor.HttpContext?.User?.FindFirstValue(ClaimTypes.NameIdentifier);
}

// Interceptor
public sealed class AuditableInterceptor(ICurrentUserService currentUserService)
    : SaveChangesInterceptor
{
    public override ValueTask<InterceptionResult<int>> SavingChangesAsync(
        DbContextEventData eventData, InterceptionResult<int> result, CancellationToken ct = default)
    {
        var context = eventData.Context!;
        var now = DateTimeOffset.UtcNow;
        var userId = currentUserService.UserId;

        foreach (var entry in context.ChangeTracker.Entries<IAuditable>())
        {
            switch (entry.State)
            {
                case EntityState.Added:
                    entry.Entity.CreatedAt = now;
                    entry.Entity.CreatedBy = userId;
                    break;
                case EntityState.Modified:
                    entry.Entity.UpdatedAt = now;
                    entry.Entity.UpdatedBy = userId;
                    break;
            }
        }

        return base.SavingChangesAsync(eventData, result, ct);
    }
}

// Registration
builder.Services.AddScoped<ICurrentUserService, CurrentUserService>();
builder.Services.AddScoped<AuditableInterceptor>();
builder.Services.AddDbContext<AppDbContext>((sp, options) =>
{
    options.AddInterceptors(sp.GetRequiredService<AuditableInterceptor>());
});
```

**Detection**: How to detect if existing project uses this pattern
- Search for `IAuditable` or `AuditableEntity` in the codebase
- Look for `SaveChangesInterceptor` implementations
- Check for `CreatedAt`, `UpdatedAt` properties on entities
- Look for `ICurrentUserService` or similar user context abstraction

**Reference**: https://learn.microsoft.com/en-us/ef/core/logging-events-diagnostics/interceptors

---

## CATEGORY 5: CQRS & Messaging - Generic (4 skills)

---

### `cqrs/command-generator` — CQRS Command Pattern

**Purpose**: Teach the generic CQRS command pattern with MediatR. Commands represent intent to change state,
paired with handlers that execute the change and validators that enforce business rules.
This is the generic version — not event-sourced.

**Packages**:
- `MediatR` (13.x)
- `FluentValidation.DependencyInjectionExtensions` (11.x)

**Key Patterns**:
- `IRequest<TResponse>` for commands with return values
- `IRequest` for void commands (fire-and-forget)
- `IRequestHandler<TCommand, TResponse>` for command handlers
- `AbstractValidator<TCommand>` for input validation
- Command naming: `{Verb}{Noun}Command` (e.g., `CreateOrderCommand`)
- Response pattern: return ID for create, `Result<T>` for operations with possible failure
- One command, one handler, one validator per operation
- Commands are immutable records

**Code Example**:
```csharp
// Command (immutable record)
public sealed record CreateOrderCommand(
    string CustomerName,
    List<CreateOrderCommand.OrderItem> Items) : IRequest<Result<Guid>>
{
    public sealed record OrderItem(Guid ProductId, int Quantity);
}

// Validator
public sealed class CreateOrderCommandValidator : AbstractValidator<CreateOrderCommand>
{
    public CreateOrderCommandValidator()
    {
        RuleFor(x => x.CustomerName)
            .NotEmpty()
            .MaximumLength(200);

        RuleFor(x => x.Items)
            .NotEmpty()
            .WithMessage("Order must contain at least one item");

        RuleForEach(x => x.Items).ChildRules(item =>
        {
            item.RuleFor(x => x.ProductId).NotEmpty();
            item.RuleFor(x => x.Quantity).GreaterThan(0);
        });
    }
}

// Handler
internal sealed class CreateOrderCommandHandler(
    IOrderRepository repository,
    IUnitOfWork unitOfWork,
    ILogger<CreateOrderCommandHandler> logger) : IRequestHandler<CreateOrderCommand, Result<Guid>>
{
    public async Task<Result<Guid>> Handle(CreateOrderCommand request, CancellationToken ct)
    {
        var order = Order.Create(request.CustomerName);

        foreach (var item in request.Items)
            order.AddItem(item.ProductId, item.Quantity);

        repository.Add(order);
        await unitOfWork.SaveChangesAsync(ct);

        logger.LogInformation("Order {OrderId} created for {Customer}", order.Id, request.CustomerName);
        return Result<Guid>.Success(order.Id);
    }
}

// MediatR registration
services.AddMediatR(cfg => cfg.RegisterServicesFromAssembly(typeof(CreateOrderCommand).Assembly));
services.AddValidatorsFromAssembly(typeof(CreateOrderCommandValidator).Assembly);
```

**Detection**: How to detect if existing project uses this pattern
- Search for `IRequest<` and `IRequestHandler<` implementations
- Look for `Command` suffix in class names
- Check for `MediatR` package reference
- Look for `Commands/` folder structure
- Search for `AbstractValidator<` for command validators

**Reference**: https://github.com/jbogard/MediatR

---

### `cqrs/query-generator` — CQRS Query Pattern

**Purpose**: Teach the generic CQRS query pattern with MediatR. Queries represent requests for data,
paired with handlers that retrieve and project data into response DTOs. Queries never modify state.

**Packages**:
- `MediatR` (13.x)
- `Dapper` (optional, for complex read queries)

**Key Patterns**:
- `IRequest<TResponse>` for queries with response DTOs
- Query naming: `Get{Noun}Query` or `List{Noun}Query`
- Response DTOs as records (immutable, no domain logic)
- Pagination: `PagedList<T>` as response type
- Filter objects with `[AsParameters]` for query strings
- Queries can use EF Core, Dapper, or both
- Read-only DbContext or `AsNoTracking()` for query handlers
- Projection: `Select()` to DTO at the database level

**Code Example**:
```csharp
// Query
public sealed record GetOrderQuery(Guid OrderId) : IRequest<OrderResponse?>;

public sealed record ListOrdersQuery(
    string? CustomerName,
    DateTime? FromDate,
    int Page = 1,
    int PageSize = 20) : IRequest<PagedList<OrderSummaryResponse>>;

// Response DTOs
public sealed record OrderResponse(
    Guid Id,
    string CustomerName,
    decimal Total,
    DateTimeOffset CreatedAt,
    List<OrderItemResponse> Items);

public sealed record OrderSummaryResponse(Guid Id, string CustomerName, decimal Total);

public sealed record OrderItemResponse(Guid ProductId, string ProductName, int Quantity, decimal UnitPrice);

// Paged list
public sealed record PagedList<T>(
    List<T> Items,
    int TotalCount,
    int Page,
    int PageSize)
{
    public int TotalPages => (int)Math.Ceiling(TotalCount / (double)PageSize);
    public bool HasNext => Page < TotalPages;
    public bool HasPrevious => Page > 1;
}

// Query handler (EF Core with projection)
internal sealed class ListOrdersQueryHandler(AppDbContext db)
    : IRequestHandler<ListOrdersQuery, PagedList<OrderSummaryResponse>>
{
    public async Task<PagedList<OrderSummaryResponse>> Handle(
        ListOrdersQuery request, CancellationToken ct)
    {
        var query = db.Orders.AsNoTracking();

        if (!string.IsNullOrEmpty(request.CustomerName))
            query = query.Where(o => o.CustomerName.Contains(request.CustomerName));

        if (request.FromDate.HasValue)
            query = query.Where(o => o.CreatedAt >= request.FromDate.Value);

        var totalCount = await query.CountAsync(ct);

        var items = await query
            .OrderByDescending(o => o.CreatedAt)
            .Skip((request.Page - 1) * request.PageSize)
            .Take(request.PageSize)
            .Select(o => new OrderSummaryResponse(o.Id, o.CustomerName, o.Total))
            .ToListAsync(ct);

        return new PagedList<OrderSummaryResponse>(items, totalCount, request.Page, request.PageSize);
    }
}
```

**Detection**: How to detect if existing project uses this pattern
- Search for classes ending in `Query` implementing `IRequest<`
- Look for `Queries/` folder structure
- Check for `PagedList<T>` or `PaginatedList<T>` types
- Look for `AsNoTracking()` in query handlers

**Reference**: https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/cqrs-microservice-reads

---

### `cqrs/pipeline-behaviors` — MediatR Pipeline Behaviors

**Purpose**: Teach MediatR pipeline behaviors for cross-cutting concerns: validation, logging,
transaction management, and caching. Behaviors form a pipeline around every request, similar
to ASP.NET middleware but for MediatR handlers.

**Packages**:
- `MediatR` (13.x)
- `FluentValidation` (for validation behavior)

**Key Patterns**:
- `IPipelineBehavior<TRequest, TResponse>` interface
- Registration order matters (first registered = outermost)
- Validation behavior: run FluentValidation before handler
- Logging behavior: log request entry/exit with timing
- Transaction behavior: wrap handler in DB transaction
- Performance behavior: warn on slow requests
- Unhandled exception behavior: log and re-throw with context
- Open generic registration for behaviors

**Code Example**:
```csharp
// Validation behavior
public sealed class ValidationBehavior<TRequest, TResponse>(
    IEnumerable<IValidator<TRequest>> validators)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : notnull
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken ct)
    {
        if (!validators.Any())
            return await next();

        var context = new ValidationContext<TRequest>(request);
        var results = await Task.WhenAll(
            validators.Select(v => v.ValidateAsync(context, ct)));

        var failures = results
            .SelectMany(r => r.Errors)
            .Where(f => f is not null)
            .ToList();

        if (failures.Count != 0)
            throw new ValidationException(failures);

        return await next();
    }
}

// Logging behavior
public sealed class LoggingBehavior<TRequest, TResponse>(
    ILogger<LoggingBehavior<TRequest, TResponse>> logger)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : notnull
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken ct)
    {
        var requestName = typeof(TRequest).Name;
        logger.LogInformation("Handling {RequestName}: {@Request}", requestName, request);

        var sw = Stopwatch.StartNew();
        var response = await next();
        sw.Stop();

        if (sw.ElapsedMilliseconds > 500)
            logger.LogWarning("Long-running request {RequestName}: {ElapsedMs}ms", requestName, sw.ElapsedMilliseconds);
        else
            logger.LogInformation("Handled {RequestName} in {ElapsedMs}ms", requestName, sw.ElapsedMilliseconds);

        return response;
    }
}

// Transaction behavior
public sealed class TransactionBehavior<TRequest, TResponse>(
    AppDbContext db) : IPipelineBehavior<TRequest, TResponse>
    where TRequest : ITransactionalRequest
{
    public async Task<TResponse> Handle(
        TRequest request, RequestHandlerDelegate<TResponse> next, CancellationToken ct)
    {
        await using var transaction = await db.Database.BeginTransactionAsync(ct);
        var response = await next();
        await db.SaveChangesAsync(ct);
        await transaction.CommitAsync(ct);
        return response;
    }
}

// Registration (order matters)
services.AddMediatR(cfg =>
{
    cfg.RegisterServicesFromAssembly(typeof(Program).Assembly);
    cfg.AddBehavior(typeof(IPipelineBehavior<,>), typeof(LoggingBehavior<,>));
    cfg.AddBehavior(typeof(IPipelineBehavior<,>), typeof(ValidationBehavior<,>));
    cfg.AddBehavior(typeof(IPipelineBehavior<,>), typeof(TransactionBehavior<,>));
});
```

**Detection**: How to detect if existing project uses this pattern
- Search for `IPipelineBehavior<` implementations
- Look for `AddBehavior` calls in MediatR registration
- Check for `Behaviors/` folder
- Look for validation, logging, or transaction behaviors

**Reference**: https://github.com/jbogard/MediatR/wiki/Behaviors

---

### `cqrs/domain-events` — Domain Events (Generic)

**Purpose**: Teach the generic domain event pattern for decoupled cross-aggregate communication
within a single process. Domain events are raised by aggregates and dispatched after successful
persistence. This is the in-process version — not the microservice event bus version.

**Packages**:
- `MediatR` (for `INotification`-based dispatch)

**Key Patterns**:
- `IDomainEvent : INotification` marker interface
- Events raised within aggregate methods, stored in a collection
- Dispatch after `SaveChanges` via interceptor (not before)
- Multiple handlers per event (loosely coupled side effects)
- Event naming: `{Entity}{PastTenseVerb}Event` (e.g., `OrderSubmittedEvent`)
- Handlers for: sending emails, updating read models, triggering workflows
- Optional: outbox pattern for reliable event processing (generic, no service bus)
- Idempotent handlers for at-least-once delivery

**Code Example**:
```csharp
// Domain event interface
public interface IDomainEvent : INotification
{
    DateTimeOffset OccurredAt { get; }
}

// Base implementation
public abstract record DomainEvent : IDomainEvent
{
    public DateTimeOffset OccurredAt { get; } = DateTimeOffset.UtcNow;
}

// Concrete event
public sealed record OrderSubmittedEvent(Guid OrderId, decimal Total) : DomainEvent;

// Raising events from aggregate
public sealed class Order : AggregateRoot
{
    public void Submit()
    {
        if (Status != OrderStatus.Draft) throw new DomainException("Cannot submit");
        Status = OrderStatus.Submitted;
        RaiseDomainEvent(new OrderSubmittedEvent(Id, Total));
    }
}

// Event handlers (multiple handlers per event)
internal sealed class SendOrderConfirmationEmail(IEmailService emailService)
    : INotificationHandler<OrderSubmittedEvent>
{
    public async Task Handle(OrderSubmittedEvent notification, CancellationToken ct)
    {
        await emailService.SendOrderConfirmationAsync(notification.OrderId, ct);
    }
}

internal sealed class UpdateOrderDashboard(AppDbContext db)
    : INotificationHandler<OrderSubmittedEvent>
{
    public async Task Handle(OrderSubmittedEvent notification, CancellationToken ct)
    {
        var dashboard = await db.DashboardStats.SingleAsync(ct);
        dashboard.IncrementOrderCount(notification.Total);
        await db.SaveChangesAsync(ct);
    }
}

// Dispatch via EF Core interceptor (fires AFTER SaveChanges)
public sealed class DomainEventDispatcher(IPublisher publisher) : SaveChangesInterceptor
{
    public override async ValueTask<int> SavedChangesAsync(
        SaveChangesCompletedEventData eventData, int result, CancellationToken ct = default)
    {
        var aggregates = eventData.Context!.ChangeTracker
            .Entries<AggregateRoot>()
            .Select(e => e.Entity)
            .Where(e => e.DomainEvents.Count > 0)
            .ToList();

        var events = aggregates.SelectMany(a => a.DomainEvents).ToList();
        aggregates.ForEach(a => a.ClearDomainEvents());

        foreach (var domainEvent in events)
            await publisher.Publish(domainEvent, ct);

        return result;
    }
}
```

**Detection**: How to detect if existing project uses this pattern
- Search for `IDomainEvent` or `DomainEvent` types
- Look for `INotification` implementations representing events
- Check for `INotificationHandler<` implementations
- Look for `RaiseDomainEvent` or `AddDomainEvent` methods on entities
- Check for `SaveChangesInterceptor` that dispatches events

**Reference**: https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/domain-events-design-implementation

---

## CATEGORY 6: Error Handling & Resilience (3 skills)

---

### `resilience/result-pattern` — Result Pattern & ProblemDetails

**Purpose**: Teach the Result pattern for explicit error handling without exceptions for control flow.
Covers `Result<T>` type with typed errors, mapping to `ProblemDetails` (RFC 9457) for HTTP APIs,
and integration with MediatR handlers and endpoint responses.

**Packages**:
- Custom `Result<T>` implementation (no external package required)
- Or `FluentResults` (3.x) / `ErrorOr` (2.x) as alternatives

**Key Patterns**:
- `Result<T>` with `IsSuccess`, `Value`, `Error` properties
- Typed error objects with code, message, and type
- `Error.NotFound()`, `Error.Validation()`, `Error.Conflict()` factory methods
- Mapping `Result<T>` to `ProblemDetails` in endpoints
- `ProblemDetails` with `type`, `title`, `status`, `detail`, `errors` (RFC 9457)
- Extension methods for endpoint result mapping
- Anti-pattern: throwing exceptions for expected business failures

**Code Example**:
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

    public TResult Match<TResult>(Func<T, TResult> onSuccess, Func<Error, TResult> onFailure)
        => IsSuccess ? onSuccess(Value) : onFailure(Error);
}

// Error type
public sealed record Error(string Code, string Message, ErrorType Type)
{
    public static Error NotFound(string code, string message)
        => new(code, message, ErrorType.NotFound);
    public static Error Validation(string code, string message)
        => new(code, message, ErrorType.Validation);
    public static Error Conflict(string code, string message)
        => new(code, message, ErrorType.Conflict);
}

public enum ErrorType { Validation, NotFound, Conflict, Unauthorized, Unexpected }

// Usage in handler
internal sealed class GetOrderHandler(IOrderRepository repo)
    : IRequestHandler<GetOrderQuery, Result<OrderResponse>>
{
    public async Task<Result<OrderResponse>> Handle(GetOrderQuery request, CancellationToken ct)
    {
        var order = await repo.FindAsync(request.Id, ct);
        if (order is null)
            return Result<OrderResponse>.Failure(
                Error.NotFound("Order.NotFound", $"Order {request.Id} not found"));

        return Result<OrderResponse>.Success(order.ToResponse());
    }
}

// Endpoint mapping
app.MapGet("/orders/{id}", async (Guid id, ISender sender) =>
{
    var result = await sender.Send(new GetOrderQuery(id));
    return result.Match(
        onSuccess: value => Results.Ok(value),
        onFailure: error => error.Type switch
        {
            ErrorType.NotFound => Results.NotFound(error.ToProblemDetails()),
            ErrorType.Validation => Results.BadRequest(error.ToProblemDetails()),
            ErrorType.Conflict => Results.Conflict(error.ToProblemDetails()),
            _ => Results.StatusCode(500)
        });
});

// ProblemDetails extension
public static ProblemDetails ToProblemDetails(this Error error) => new()
{
    Type = $"https://tools.ietf.org/html/rfc9110#section-15.5",
    Title = error.Code,
    Detail = error.Message,
    Status = error.Type switch
    {
        ErrorType.NotFound => StatusCodes.Status404NotFound,
        ErrorType.Validation => StatusCodes.Status400BadRequest,
        ErrorType.Conflict => StatusCodes.Status409Conflict,
        _ => StatusCodes.Status500InternalServerError
    }
};
```

**Detection**: How to detect if existing project uses this pattern
- Search for `Result<T>` or `Result` class definitions
- Look for `FluentResults` or `ErrorOr` package references
- Check for `ProblemDetails` mapping in endpoints
- Look for `Error` types with factory methods
- Search for `Match` or `Switch` methods on result types

**Reference**: https://learn.microsoft.com/en-us/aspnet/core/web-api/handle-errors

---

### `resilience/polly` — Polly Resilience Strategies

**Purpose**: Teach resilience patterns using Microsoft.Extensions.Http.Resilience (Polly v8 integration).
Covers retry, circuit breaker, timeout, fallback, hedging, and rate limiting as composable
resilience pipelines for HTTP clients and custom operations.

**Packages**:
- `Microsoft.Extensions.Http.Resilience` (9.x — includes Polly v8)
- `Microsoft.Extensions.Resilience` (for non-HTTP scenarios)

**Key Patterns**:
- `AddStandardResilienceHandler()` for default HTTP resilience (retry + circuit breaker + timeout)
- Custom resilience pipeline with `AddResiliencePipeline`
- Retry: exponential backoff with jitter, handle specific exceptions/status codes
- Circuit breaker: failure threshold, break duration, half-open state
- Timeout: per-attempt and total timeout
- Hedging: parallel requests to reduce tail latency
- Named pipelines for different downstream services
- Logging and telemetry integration

**Code Example**:
```csharp
// Standard resilience for HTTP clients (recommended starting point)
builder.Services.AddHttpClient("OrdersApi", client =>
{
    client.BaseAddress = new Uri("https://api.orders.com");
})
.AddStandardResilienceHandler();

// Custom resilience pipeline
builder.Services.AddHttpClient("PaymentGateway", client =>
{
    client.BaseAddress = new Uri("https://payments.example.com");
})
.AddResilienceHandler("payment-pipeline", pipeline =>
{
    // Retry with exponential backoff
    pipeline.AddRetry(new HttpRetryStrategyOptions
    {
        MaxRetryAttempts = 3,
        Delay = TimeSpan.FromMilliseconds(500),
        BackoffType = DelayBackoffType.Exponential,
        UseJitter = true,
        ShouldHandle = new PredicateBuilder<HttpResponseMessage>()
            .HandleResult(r => r.StatusCode == HttpStatusCode.TooManyRequests
                            || r.StatusCode >= HttpStatusCode.InternalServerError)
    });

    // Circuit breaker
    pipeline.AddCircuitBreaker(new HttpCircuitBreakerStrategyOptions
    {
        FailureRatio = 0.5,
        SamplingDuration = TimeSpan.FromSeconds(30),
        MinimumThroughput = 10,
        BreakDuration = TimeSpan.FromSeconds(15)
    });

    // Timeout per attempt
    pipeline.AddTimeout(TimeSpan.FromSeconds(5));
});

// Non-HTTP resilience pipeline
builder.Services.AddResiliencePipeline("database-retry", pipeline =>
{
    pipeline
        .AddRetry(new RetryStrategyOptions
        {
            MaxRetryAttempts = 3,
            Delay = TimeSpan.FromSeconds(1),
            BackoffType = DelayBackoffType.Exponential,
            ShouldHandle = new PredicateBuilder().Handle<SqlException>()
        })
        .AddTimeout(TimeSpan.FromSeconds(30));
});

// Consuming non-HTTP pipeline
public sealed class DataService(
    [FromKeyedServices("database-retry")] ResiliencePipeline pipeline,
    IDbConnectionFactory connectionFactory)
{
    public async Task<Order?> GetOrderAsync(Guid id, CancellationToken ct)
    {
        return await pipeline.ExecuteAsync(async token =>
        {
            using var conn = connectionFactory.CreateConnection();
            return await conn.QuerySingleOrDefaultAsync<Order>(
                "SELECT * FROM Orders WHERE Id = @Id", new { Id = id });
        }, ct);
    }
}
```

**Detection**: How to detect if existing project uses this pattern
- Search for `Microsoft.Extensions.Http.Resilience` package
- Look for `AddStandardResilienceHandler` or `AddResilienceHandler` calls
- Check for `Polly` package references (v7 legacy)
- Search for `AddResiliencePipeline` in service registration
- Look for retry/circuit breaker configuration in `Program.cs`

**Reference**: https://learn.microsoft.com/en-us/dotnet/core/resilience/

---

### `resilience/caching` — Caching Strategies

**Purpose**: Teach caching patterns including HybridCache (.NET 9+), output caching, distributed cache,
and in-memory cache. Covers cache invalidation strategies, stampede protection, and when to use
which caching approach.

**Packages**:
- `Microsoft.Extensions.Caching.Hybrid` (HybridCache, .NET 9+)
- `Microsoft.Extensions.Caching.StackExchangeRedis` (distributed)
- Built-in: `IMemoryCache`, `IDistributedCache`, output caching

**Key Patterns**:
- `HybridCache` (.NET 9+): L1 in-memory + L2 distributed, stampede protection built-in
- `IMemoryCache` for simple single-server caching
- `IDistributedCache` for multi-server caching (Redis, SQL Server)
- Output caching middleware for HTTP response caching
- Cache-aside pattern: check cache → miss → load from source → store in cache
- Cache invalidation: time-based (TTL), event-based, tag-based
- Cache stampede prevention: `HybridCache` handles automatically; for `IMemoryCache` use `SemaphoreSlim`
- Cache key conventions and namespacing

**Code Example**:
```csharp
// HybridCache (.NET 9+ — preferred approach)
builder.Services.AddHybridCache(options =>
{
    options.DefaultEntryOptions = new HybridCacheEntryOptions
    {
        Expiration = TimeSpan.FromMinutes(5),
        LocalCacheExpiration = TimeSpan.FromMinutes(1)
    };
});
builder.Services.AddStackExchangeRedisCache(options =>
{
    options.Configuration = builder.Configuration.GetConnectionString("Redis");
});

// Usage with HybridCache
public sealed class OrderService(HybridCache cache, IOrderRepository repository)
{
    public async Task<OrderResponse?> GetOrderAsync(Guid id, CancellationToken ct)
    {
        return await cache.GetOrCreateAsync(
            $"orders:{id}",
            async token => await repository.FindAsync(id, token) is { } order
                ? order.ToResponse()
                : null,
            new HybridCacheEntryOptions { Expiration = TimeSpan.FromMinutes(10) },
            cancellationToken: ct);
    }

    public async Task InvalidateOrderCacheAsync(Guid id, CancellationToken ct)
    {
        await cache.RemoveAsync($"orders:{id}", ct);
    }
}

// Output caching for HTTP responses
builder.Services.AddOutputCache(options =>
{
    options.AddBasePolicy(builder => builder.Expire(TimeSpan.FromSeconds(60)));
    options.AddPolicy("OrderList", builder =>
        builder.Expire(TimeSpan.FromMinutes(5))
               .Tag("orders")
               .SetVaryByQuery("page", "pageSize", "status"));
});

app.UseOutputCache();

app.MapGet("/orders", GetOrders).CacheOutput("OrderList");

// Cache invalidation after write
app.MapPost("/orders", async (CreateOrderCommand cmd, ISender sender,
    IOutputCacheStore cacheStore, CancellationToken ct) =>
{
    var result = await sender.Send(cmd, ct);
    await cacheStore.EvictByTagAsync("orders", ct);
    return TypedResults.Created($"/orders/{result.Id}", result);
});
```

**Detection**: How to detect if existing project uses this pattern
- Search for `HybridCache`, `IMemoryCache`, or `IDistributedCache` usage
- Look for `AddHybridCache`, `AddStackExchangeRedisCache`, `AddMemoryCache` in `Program.cs`
- Check for `AddOutputCache` and `CacheOutput` middleware
- Look for cache key patterns (string interpolation with prefixes)

**Reference**: https://learn.microsoft.com/en-us/aspnet/core/performance/caching/hybrid

---

## CATEGORY 7: Security (3 skills)

---

### `security/jwt-authentication` — JWT Authentication

**Purpose**: Teach JWT Bearer authentication setup, token generation with claims, refresh token flow,
and token validation configuration. Covers both issuing tokens (auth service) and consuming tokens
(API service) with proper security practices.

**Packages**:
- `Microsoft.AspNetCore.Authentication.JwtBearer` (built-in)
- `System.IdentityModel.Tokens.Jwt`

**Key Patterns**:
- `AddAuthentication().AddJwtBearer()` configuration
- Token generation with `JwtSecurityTokenHandler` or `JsonWebTokenHandler`
- Claims: `sub`, `email`, `role`, custom claims
- Refresh token: secure storage, rotation, revocation
- Token validation parameters: issuer, audience, clock skew, signing key
- HTTPS-only token transmission
- Token expiry: short-lived access tokens (15-60 min), longer refresh tokens
- `.NET 10`: prefer `JsonWebTokenHandler` over `JwtSecurityTokenHandler`

**Code Example**:
```csharp
// JWT configuration
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer = builder.Configuration["Jwt:Issuer"],
            ValidAudience = builder.Configuration["Jwt:Audience"],
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(builder.Configuration["Jwt:Key"]!)),
            ClockSkew = TimeSpan.FromSeconds(30)
        };
    });

// Token generation service
public sealed class TokenService(IOptions<JwtOptions> options) : ITokenService
{
    public TokenResponse GenerateToken(User user, IEnumerable<string> permissions)
    {
        var claims = new List<Claim>
        {
            new(JwtRegisteredClaimNames.Sub, user.Id.ToString()),
            new(JwtRegisteredClaimNames.Email, user.Email),
            new(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString()),
            new("permissions", string.Join(",", permissions))
        };

        foreach (var role in user.Roles)
            claims.Add(new Claim(ClaimTypes.Role, role));

        var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(options.Value.Key));
        var credentials = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);
        var expiry = DateTime.UtcNow.AddMinutes(options.Value.ExpiryMinutes);

        var token = new JwtSecurityToken(
            issuer: options.Value.Issuer,
            audience: options.Value.Audience,
            claims: claims,
            expires: expiry,
            signingCredentials: credentials);

        return new TokenResponse(
            AccessToken: new JwtSecurityTokenHandler().WriteToken(token),
            ExpiresAt: expiry,
            RefreshToken: GenerateRefreshToken());
    }

    private static string GenerateRefreshToken()
        => Convert.ToBase64String(RandomNumberGenerator.GetBytes(64));
}

// Refresh token flow
public sealed class RefreshTokenHandler(
    ITokenService tokenService,
    IRefreshTokenRepository refreshTokenRepo,
    IUserRepository userRepo) : IRequestHandler<RefreshTokenCommand, Result<TokenResponse>>
{
    public async Task<Result<TokenResponse>> Handle(
        RefreshTokenCommand request, CancellationToken ct)
    {
        var stored = await refreshTokenRepo.FindAsync(request.RefreshToken, ct);
        if (stored is null || stored.IsExpired || stored.IsRevoked)
            return Result<TokenResponse>.Failure(Error.Unauthorized("InvalidToken", "Invalid refresh token"));

        stored.Revoke(); // rotate: revoke old token
        var user = await userRepo.FindAsync(stored.UserId, ct);
        var newToken = tokenService.GenerateToken(user!, user!.Permissions);

        await refreshTokenRepo.StoreAsync(new RefreshToken(user.Id, newToken.RefreshToken), ct);
        return Result<TokenResponse>.Success(newToken);
    }
}
```

**Detection**: How to detect if existing project uses this pattern
- Search for `AddJwtBearer` in `Program.cs`
- Look for `JwtSecurityTokenHandler` or `JsonWebTokenHandler` usage
- Check for `TokenValidationParameters` configuration
- Look for `ITokenService` or similar token generation abstraction
- Check for `[Authorize]` attributes on controllers/endpoints

**Reference**: https://learn.microsoft.com/en-us/aspnet/core/security/authentication/jwt

---

### `security/permission-authorization` — Permission-Based Authorization

**Purpose**: Teach fine-grained permission-based authorization using custom policies, requirement handlers,
and attribute-based access control. Goes beyond role-based auth to support individual permissions
that can be assigned to users or roles.

**Packages**:
- `Microsoft.AspNetCore.Authorization` (built-in)

**Key Patterns**:
- `HasPermissionAttribute` custom authorize attribute
- `PermissionAuthorizationPolicyProvider` to dynamically create policies
- `PermissionAuthorizationHandler` to check user permissions from claims
- Permission constants class for type-safe permission names
- Permissions stored in JWT claims or loaded from database
- Combine with role-based auth: roles define permission sets
- Resource-based authorization with `IAuthorizationService`

**Code Example**:
```csharp
// Permission constants
public static class Permissions
{
    public const string OrdersRead = "orders:read";
    public const string OrdersCreate = "orders:create";
    public const string OrdersUpdate = "orders:update";
    public const string OrdersDelete = "orders:delete";
    public const string ReportsView = "reports:view";
    public const string UsersManage = "users:manage";
}

// Custom attribute
[AttributeUsage(AttributeTargets.Class | AttributeTargets.Method)]
public sealed class HasPermissionAttribute(string permission) : AuthorizeAttribute(permission)
{
    public string Permission { get; } = permission;
}

// Requirement
public sealed class PermissionRequirement(string permission) : IAuthorizationRequirement
{
    public string Permission { get; } = permission;
}

// Policy provider (creates policies on-the-fly from permission strings)
public sealed class PermissionAuthorizationPolicyProvider(
    IOptions<AuthorizationOptions> options) : DefaultAuthorizationPolicyProvider(options)
{
    public override async Task<AuthorizationPolicy?> GetPolicyAsync(string policyName)
    {
        var policy = await base.GetPolicyAsync(policyName);
        if (policy is not null) return policy;

        // Dynamic policy creation for permission strings
        return new AuthorizationPolicyBuilder()
            .AddRequirements(new PermissionRequirement(policyName))
            .Build();
    }
}

// Handler (checks claims for permission)
public sealed class PermissionAuthorizationHandler
    : AuthorizationHandler<PermissionRequirement>
{
    protected override Task HandleRequirementAsync(
        AuthorizationHandlerContext context, PermissionRequirement requirement)
    {
        var permissions = context.User.FindFirstValue("permissions")?.Split(',') ?? [];

        if (permissions.Contains(requirement.Permission))
            context.Succeed(requirement);

        return Task.CompletedTask;
    }
}

// Registration
builder.Services.AddSingleton<IAuthorizationPolicyProvider, PermissionAuthorizationPolicyProvider>();
builder.Services.AddSingleton<IAuthorizationHandler, PermissionAuthorizationHandler>();

// Usage
[HasPermission(Permissions.OrdersCreate)]
app.MapPost("/orders", CreateOrder);

// Controller usage
[ApiController]
[Route("api/orders")]
public sealed class OrdersController : ControllerBase
{
    [HttpDelete("{id}")]
    [HasPermission(Permissions.OrdersDelete)]
    public async Task<IActionResult> Delete(Guid id) { /* ... */ }
}
```

**Detection**: How to detect if existing project uses this pattern
- Search for custom `AuthorizeAttribute` subclasses
- Look for `IAuthorizationPolicyProvider` implementations
- Check for `IAuthorizationHandler` custom implementations
- Search for `"permissions"` claim in token generation
- Look for permission constants classes

**Reference**: https://learn.microsoft.com/en-us/aspnet/core/security/authorization/policies

---

### `security/security-scan` — Security Scanning & Audit

**Purpose**: Teach security scanning patterns for .NET projects: detecting known CVEs in dependencies,
finding secrets in code, checking OWASP top 10 patterns, and auditing authentication/authorization
configuration. This is a checklist and process skill, not a code generation skill.

**Packages**:
- `dotnet list package --vulnerable` (built-in CLI)
- `Microsoft.CodeAnalysis.NetAnalyzers` (built-in security analyzers)
- `Roslynator.Analyzers` (additional code analysis)

**Key Patterns**:
- Dependency vulnerability scan: `dotnet list package --vulnerable --include-transitive`
- Secrets detection: scan for hardcoded connection strings, API keys, tokens
- OWASP patterns: SQL injection, XSS, CSRF, insecure deserialization
- Auth audit: verify JWT validation parameters, HTTPS enforcement, CORS policy
- Security headers: HSTS, CSP, X-Frame-Options, X-Content-Type-Options
- `.editorconfig` security rules from `Microsoft.CodeAnalysis.NetAnalyzers`
- GitHub Dependabot / NuGet audit integration

**Code Example**:
```bash
# Dependency vulnerability scan
dotnet list package --vulnerable --include-transitive

# NuGet audit in .csproj (enabled by default in .NET 8+)
# <NuGetAudit>true</NuGetAudit>
# <NuGetAuditLevel>moderate</NuGetAuditLevel>
```

```csharp
// Security headers middleware
app.UseHsts();
app.Use(async (context, next) =>
{
    context.Response.Headers.Append("X-Content-Type-Options", "nosniff");
    context.Response.Headers.Append("X-Frame-Options", "DENY");
    context.Response.Headers.Append("X-XSS-Protection", "0"); // modern browsers
    context.Response.Headers.Append("Referrer-Policy", "strict-origin-when-cross-origin");
    context.Response.Headers.Append("Permissions-Policy",
        "camera=(), microphone=(), geolocation=()");
    await next();
});

// HTTPS redirection
app.UseHttpsRedirection();

// Checklist items to verify:
// 1. TokenValidationParameters: ValidateIssuer, ValidateAudience, ValidateLifetime = true
// 2. ClockSkew set to minimal value (not default 5 min)
// 3. No secrets in appsettings.json (use user-secrets or Key Vault)
// 4. CORS: not AllowAnyOrigin with AllowCredentials
// 5. Anti-forgery tokens for form submissions
// 6. Rate limiting on auth endpoints
// 7. Parameterized queries (EF Core does this by default)
```

**Detection**: How to detect if existing project uses this pattern
- Check for `<NuGetAudit>` in `.csproj` or `Directory.Build.props`
- Look for security header middleware
- Check for `UseHttpsRedirection` in `Program.cs`
- Run `dotnet list package --vulnerable` for active vulnerabilities
- Check `.editorconfig` for security analyzer rules

**Reference**: https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-list-package#list-vulnerable-packages

---

## CATEGORY 8: Observability (3 skills)

---

### `observability/serilog` — Structured Logging with Serilog

**Purpose**: Teach two-stage Serilog bootstrap, structured logging best practices, enrichment,
Seq sink integration, and distributed tracing correlation. Covers proper logger setup that
captures startup errors and integrates with ASP.NET Core's logging pipeline.

**Packages**:
- `Serilog.AspNetCore` (9.x)
- `Serilog.Sinks.Seq` (for Seq)
- `Serilog.Sinks.Console`
- `Serilog.Enrichers.Environment`
- `Serilog.Enrichers.Thread`

**Key Patterns**:
- Two-stage bootstrap: initial logger → builder → final logger
- `UseSerilog()` on the host builder
- Structured logging: use `{PropertyName}` not string interpolation
- Enrichment: `MachineName`, `ThreadId`, `CorrelationId`, custom enrichers
- Seq sink for centralized log aggregation
- Log levels per namespace in `appsettings.json`
- `RequestLoggingMiddleware` for HTTP request/response logging
- Distributed tracing correlation with `Activity.Current.TraceId`

**Code Example**:
```csharp
// Program.cs — two-stage bootstrap
Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Override("Microsoft", LogEventLevel.Information)
    .Enrich.FromLogContext()
    .WriteTo.Console()
    .CreateBootstrapLogger();

try
{
    var builder = WebApplication.CreateBuilder(args);

    builder.Host.UseSerilog((context, services, configuration) => configuration
        .ReadFrom.Configuration(context.Configuration)
        .ReadFrom.Services(services)
        .Enrich.FromLogContext()
        .Enrich.WithMachineName()
        .Enrich.WithProperty("Application", "OrderService")
        .WriteTo.Console(outputTemplate:
            "[{Timestamp:HH:mm:ss} {Level:u3}] {Message:lj} {Properties:j}{NewLine}{Exception}")
        .WriteTo.Seq(context.Configuration["Seq:Url"] ?? "http://localhost:5341"));

    // ... configure services ...

    var app = builder.Build();

    app.UseSerilogRequestLogging(options =>
    {
        options.EnrichDiagnosticContext = (diagnosticContext, httpContext) =>
        {
            diagnosticContext.Set("UserId",
                httpContext.User.FindFirstValue(ClaimTypes.NameIdentifier) ?? "anonymous");
        };
    });

    app.Run();
}
catch (Exception ex)
{
    Log.Fatal(ex, "Application terminated unexpectedly");
}
finally
{
    Log.CloseAndFlush();
}
```

```json
// appsettings.json Serilog section
{
  "Serilog": {
    "MinimumLevel": {
      "Default": "Information",
      "Override": {
        "Microsoft.AspNetCore": "Warning",
        "Microsoft.EntityFrameworkCore.Database.Command": "Warning",
        "System": "Warning"
      }
    }
  },
  "Seq": {
    "Url": "http://localhost:5341"
  }
}
```

```csharp
// Structured logging best practices
// GOOD: structured properties
logger.LogInformation("Order {OrderId} created for customer {CustomerId}", orderId, customerId);

// BAD: string interpolation (loses structure)
logger.LogInformation($"Order {orderId} created for customer {customerId}");

// Scoped logging with LogContext
using (LogContext.PushProperty("OrderId", orderId))
using (LogContext.PushProperty("CorrelationId", Activity.Current?.TraceId.ToString()))
{
    logger.LogInformation("Processing order");
    // All logs within this scope include OrderId and CorrelationId
}
```

**Detection**: How to detect if existing project uses this pattern
- Search for `Serilog.AspNetCore` package in `.csproj`
- Look for `UseSerilog` in `Program.cs`
- Check for `Log.Logger = new LoggerConfiguration()` initialization
- Look for `WriteTo.Seq` or `WriteTo.Console` sink configuration
- Check `appsettings.json` for `"Serilog"` section

**Reference**: https://github.com/serilog/serilog-aspnetcore

---

### `observability/opentelemetry` — OpenTelemetry Traces & Metrics

**Purpose**: Teach OpenTelemetry integration for distributed tracing, custom metrics, and
telemetry export. Covers ASP.NET Core instrumentation, EF Core instrumentation, HTTP client
instrumentation, custom activities/metrics, and export to OTLP-compatible backends.

**Packages**:
- `OpenTelemetry.Extensions.Hosting`
- `OpenTelemetry.Instrumentation.AspNetCore`
- `OpenTelemetry.Instrumentation.Http`
- `OpenTelemetry.Instrumentation.EntityFrameworkCore`
- `OpenTelemetry.Exporter.OpenTelemetryProtocol` (OTLP)
- `OpenTelemetry.Exporter.Console` (development)

**Key Patterns**:
- `AddOpenTelemetry()` with tracing, metrics, and logging
- Built-in instrumentation: ASP.NET Core, HttpClient, EF Core
- Custom `ActivitySource` for application-level tracing
- Custom `Meter` and `Counter`/`Histogram` for business metrics
- `IMeterFactory` for DI-friendly metric creation (.NET 8+)
- OTLP exporter to Aspire Dashboard, Jaeger, Grafana, Seq
- Service name and version enrichment
- Baggage propagation for cross-service context

**Code Example**:
```csharp
// Program.cs — OpenTelemetry registration
var serviceName = "OrderService";
var serviceVersion = typeof(Program).Assembly.GetName().Version?.ToString() ?? "1.0.0";

builder.Services.AddOpenTelemetry()
    .ConfigureResource(resource => resource
        .AddService(serviceName, serviceVersion: serviceVersion))
    .WithTracing(tracing => tracing
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddEntityFrameworkCoreInstrumentation()
        .AddSource(serviceName) // custom ActivitySource
        .AddOtlpExporter(options =>
        {
            options.Endpoint = new Uri(builder.Configuration["Otlp:Endpoint"]
                ?? "http://localhost:4317");
        }))
    .WithMetrics(metrics => metrics
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddRuntimeInstrumentation()
        .AddMeter(serviceName) // custom Meter
        .AddOtlpExporter());

// Custom tracing with ActivitySource
public sealed class OrderService(IOrderRepository repository)
{
    private static readonly ActivitySource Activity = new("OrderService");

    public async Task<Order> CreateOrderAsync(CreateOrderCommand command, CancellationToken ct)
    {
        using var activity = Activity.StartActivity("CreateOrder", ActivityKind.Internal);
        activity?.SetTag("order.customer", command.CustomerName);
        activity?.SetTag("order.item_count", command.Items.Count);

        var order = Order.Create(command.CustomerName);
        repository.Add(order);

        activity?.SetTag("order.id", order.Id.ToString());
        return order;
    }
}

// Custom metrics with IMeterFactory
public sealed class OrderMetrics
{
    private readonly Counter<long> _ordersCreated;
    private readonly Histogram<double> _orderProcessingDuration;

    public OrderMetrics(IMeterFactory meterFactory)
    {
        var meter = meterFactory.Create("OrderService");
        _ordersCreated = meter.CreateCounter<long>(
            "orders.created", "orders", "Number of orders created");
        _orderProcessingDuration = meter.CreateHistogram<double>(
            "orders.processing.duration", "ms", "Order processing duration");
    }

    public void OrderCreated(string status) =>
        _ordersCreated.Add(1, new KeyValuePair<string, object?>("status", status));

    public void RecordProcessingDuration(double durationMs) =>
        _orderProcessingDuration.Record(durationMs);
}

// Register metrics as singleton
builder.Services.AddSingleton<OrderMetrics>();
```

**Detection**: How to detect if existing project uses this pattern
- Search for `OpenTelemetry` packages in `.csproj`
- Look for `AddOpenTelemetry()` in `Program.cs`
- Check for `ActivitySource` usage in service classes
- Look for `IMeterFactory` or `Meter` usage
- Check for `AddOtlpExporter` configuration

**Reference**: https://learn.microsoft.com/en-us/dotnet/core/diagnostics/observability-with-otel

---

### `observability/health-checks` — Health Checks

**Purpose**: Teach ASP.NET Core health check setup for infrastructure monitoring, Kubernetes
readiness/liveness probes, and custom health checks. Covers database checks, HTTP dependency
checks, and health check UI integration.

**Packages**:
- `Microsoft.Extensions.Diagnostics.HealthChecks` (built-in)
- `AspNetCore.HealthChecks.SqlServer` (SQL Server check)
- `AspNetCore.HealthChecks.NpgSql` (PostgreSQL check)
- `AspNetCore.HealthChecks.Redis` (Redis check)
- `AspNetCore.HealthChecks.Uris` (HTTP endpoint checks)
- `AspNetCore.HealthChecks.UI` (optional dashboard)

**Key Patterns**:
- `/health` for overall status (liveness)
- `/health/ready` for dependency readiness (readiness probe)
- Database health checks for EF Core / SQL Server / PostgreSQL
- HTTP dependency checks for downstream services
- Custom `IHealthCheck` for business-specific checks
- Tags for grouping checks: `ready`, `live`, `startup`
- Health check response writer with detailed JSON output
- Kubernetes probe configuration mapping

**Code Example**:
```csharp
// Program.cs — health check registration
builder.Services.AddHealthChecks()
    // Database check
    .AddSqlServer(
        connectionString: builder.Configuration.GetConnectionString("Default")!,
        name: "sqlserver",
        tags: ["ready", "db"])
    // Redis check
    .AddRedis(
        redisConnectionString: builder.Configuration.GetConnectionString("Redis")!,
        name: "redis",
        tags: ["ready", "cache"])
    // HTTP dependency check
    .AddUrlGroup(
        uri: new Uri(builder.Configuration["PaymentService:Url"]!),
        name: "payment-service",
        tags: ["ready", "external"])
    // Custom business check
    .AddCheck<OrderProcessingHealthCheck>(
        name: "order-processing",
        tags: ["ready", "business"]);

// Map endpoints with filtering by tags
app.MapHealthChecks("/health/live", new HealthCheckOptions
{
    Predicate = _ => false // no dependency checks, just "am I running?"
});

app.MapHealthChecks("/health/ready", new HealthCheckOptions
{
    Predicate = check => check.Tags.Contains("ready"),
    ResponseWriter = WriteDetailedResponse
});

app.MapHealthChecks("/health", new HealthCheckOptions
{
    ResponseWriter = WriteDetailedResponse
});

// Detailed JSON response writer
static Task WriteDetailedResponse(HttpContext context, HealthReport report)
{
    context.Response.ContentType = "application/json";
    var response = new
    {
        status = report.Status.ToString(),
        duration = report.TotalDuration.TotalMilliseconds,
        checks = report.Entries.Select(e => new
        {
            name = e.Key,
            status = e.Value.Status.ToString(),
            duration = e.Value.Duration.TotalMilliseconds,
            description = e.Value.Description,
            error = e.Value.Exception?.Message
        })
    };
    return context.Response.WriteAsJsonAsync(response);
}

// Custom health check
public sealed class OrderProcessingHealthCheck(AppDbContext db) : IHealthCheck
{
    public async Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context, CancellationToken ct = default)
    {
        var stuckOrders = await db.Orders
            .CountAsync(o => o.Status == OrderStatus.Processing
                          && o.UpdatedAt < DateTimeOffset.UtcNow.AddMinutes(-30), ct);

        return stuckOrders switch
        {
            0 => HealthCheckResult.Healthy("No stuck orders"),
            < 5 => HealthCheckResult.Degraded($"{stuckOrders} orders stuck > 30 min"),
            _ => HealthCheckResult.Unhealthy($"{stuckOrders} orders stuck > 30 min")
        };
    }
}
```

```yaml
# Kubernetes deployment probe configuration
livenessProbe:
  httpGet:
    path: /health/live
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 30
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 10
  failureThreshold: 3
```

**Detection**: How to detect if existing project uses this pattern
- Search for `AddHealthChecks()` in `Program.cs`
- Look for `MapHealthChecks` endpoint mapping
- Check for `IHealthCheck` implementations
- Look for `AspNetCore.HealthChecks.*` packages in `.csproj`
- Check Kubernetes manifests for health probe configuration

**Reference**: https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/health-checks

---

## Appendix: Version Compatibility Matrix

| Feature | .NET 8 / C# 12 | .NET 9 / C# 13 | .NET 10 / C# 14 |
|---------|-----------------|-----------------|------------------|
| Primary constructors | Yes | Yes | Yes |
| Collection expressions | Yes | Yes | Yes |
| `field` keyword | No | Preview | Yes |
| Extension types | No | No | Yes |
| `params` collections | No | Yes | Yes |
| `Lock` object | No | Yes | Yes |
| HybridCache | No | Yes | Yes |
| Native OpenAPI | No | Yes | Yes |
| `MapStaticAssets()` | No | Yes | Yes |
| `.slnx` format | No | Yes | Yes |
| Keyed services | Yes | Yes | Yes |
| `ValidateOnStart` | Yes | Yes | Yes |
| Output caching | Yes | Yes | Yes |
| `AddStandardResilienceHandler` | Yes | Yes | Yes |

Skills must check `<TargetFramework>` and emit version-appropriate code.

---

## Appendix: Cross-Skill Dependencies

| Skill | Depends On |
|-------|-----------|
| `architecture/vertical-slice` | `core/modern-csharp`, `core/dependency-injection` |
| `architecture/clean-architecture` | `core/dependency-injection`, `data/repository-pattern` |
| `architecture/ddd` | `core/modern-csharp` |
| `api/minimal-api` | `api/openapi`, `core/dependency-injection` |
| `api/controllers` | `api/openapi`, `core/dependency-injection` |
| `api/scalar` | `api/openapi` |
| `data/ef-core` | `core/configuration` |
| `data/repository-pattern` | `data/ef-core` |
| `data/specification-pattern` | `data/repository-pattern` |
| `data/audit-trail` | `data/ef-core` |
| `cqrs/command-generator` | `core/dependency-injection` |
| `cqrs/query-generator` | `core/dependency-injection` |
| `cqrs/pipeline-behaviors` | `cqrs/command-generator` |
| `cqrs/domain-events` | `architecture/ddd`, `data/ef-core` |
| `resilience/result-pattern` | `api/minimal-api` or `api/controllers` |
| `resilience/polly` | `core/dependency-injection` |
| `resilience/caching` | `core/configuration` |
| `security/jwt-authentication` | `core/configuration` |
| `security/permission-authorization` | `security/jwt-authentication` |
| `observability/serilog` | `core/configuration` |
| `observability/opentelemetry` | `core/dependency-injection` |
| `observability/health-checks` | `core/dependency-injection` |
