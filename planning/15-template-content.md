# dotnet-ai-kit - Template Content

## Overview

Defines the file structure and key file content for 11 project templates — 7 for microservices, 4 for generic .NET.

Templates are used by:
- `/dotnet-ai.implement` when creating new microservice projects (status: CREATE NEW in service map)
- `/dotnet-ai.init` when scaffolding a new generic .NET project

All templates use placeholders:
- `{Company}` — from config.yml (e.g., "Acme")
- `{company}` — lowercase (e.g., "acme")
- `{Domain}` — from feature spec (e.g., "Order")
- `{domain}` — lowercase (e.g., "order")
- `{ProjectName}` — project name (generic mode, e.g., "OrderApi")
- `{Side}` — project side (Commands, Queries, Processor, etc.)
- `{NetVersion}` — target framework (default: net10.0)

---

## Generic .NET Templates (4)

### Template 8: generic-vsa/ — Vertical Slice Architecture

```
{Company}.{ProjectName}/
├── {Company}.{ProjectName}.sln
├── src/
│   └── {Company}.{ProjectName}/
│       ├── {Company}.{ProjectName}.csproj
│       ├── Program.cs
│       ├── Features/
│       │   └── .gitkeep
│       ├── Common/
│       │   ├── Behaviors/
│       │   │   ├── ValidationBehavior.cs
│       │   │   └── LoggingBehavior.cs
│       │   ├── Models/
│       │   │   ├── Result.cs
│       │   │   └── Paginated.cs
│       │   └── Extensions/
│       │       └── ServiceCollectionExtensions.cs
│       ├── Data/
│       │   ├── ApplicationDbContext.cs
│       │   └── Migrations/
│       ├── appsettings.json
│       └── appsettings.Development.json
├── tests/
│   └── {Company}.{ProjectName}.Tests/
│       ├── {Company}.{ProjectName}.Tests.csproj
│       └── .gitkeep
├── Directory.Build.props
├── Directory.Packages.props
├── .editorconfig
├── .gitignore
└── README.md
```

**Key Files:**

**Program.cs:**
```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddOpenApi();
builder.Services.AddMediatR(cfg => cfg.RegisterServicesFromAssembly(typeof(Program).Assembly));
builder.Services.AddValidatorsFromAssembly(typeof(Program).Assembly);
builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("Default")));

var app = builder.Build();

app.MapOpenApi();
app.MapScalarApiReference();
// Feature endpoints registered via IEndpointGroup discovery
app.MapFeatureEndpoints();

app.Run();
```

**Features/ pattern (one file per operation):**
```csharp
// Features/Orders/CreateOrder.cs
public static class CreateOrder
{
    public sealed record Command(string CustomerName, decimal Total) : IRequest<Result<Guid>>;

    public sealed class Validator : AbstractValidator<Command>
    {
        public Validator()
        {
            RuleFor(x => x.CustomerName).NotEmpty();
            RuleFor(x => x.Total).GreaterThan(0);
        }
    }

    public sealed class Handler(ApplicationDbContext db) : IRequestHandler<Command, Result<Guid>>
    {
        public async Task<Result<Guid>> Handle(Command request, CancellationToken ct)
        {
            var order = new Order { CustomerName = request.CustomerName, Total = request.Total };
            db.Orders.Add(order);
            await db.SaveChangesAsync(ct);
            return Result<Guid>.Success(order.Id);
        }
    }
}
```

**Packages:** MediatR, FluentValidation, EF Core, Scalar.AspNetCore

---

### Template 9: generic-clean-arch/ — Clean Architecture

```
{Company}.{ProjectName}/
├── {Company}.{ProjectName}.sln
├── src/
│   ├── {Company}.{ProjectName}.Domain/
│   │   ├── {Company}.{ProjectName}.Domain.csproj
│   │   ├── Entities/
│   │   │   └── .gitkeep
│   │   ├── ValueObjects/
│   │   │   └── .gitkeep
│   │   ├── Events/
│   │   │   └── .gitkeep
│   │   ├── Exceptions/
│   │   │   └── .gitkeep
│   │   └── Interfaces/
│   │       ├── IRepository.cs
│   │       └── IUnitOfWork.cs
│   ├── {Company}.{ProjectName}.Application/
│   │   ├── {Company}.{ProjectName}.Application.csproj
│   │   ├── Commands/
│   │   │   └── .gitkeep
│   │   ├── Queries/
│   │   │   └── .gitkeep
│   │   ├── Behaviors/
│   │   │   ├── ValidationBehavior.cs
│   │   │   └── LoggingBehavior.cs
│   │   ├── Common/
│   │   │   ├── Result.cs
│   │   │   └── Paginated.cs
│   │   └── DependencyInjection.cs
│   ├── {Company}.{ProjectName}.Infrastructure/
│   │   ├── {Company}.{ProjectName}.Infrastructure.csproj
│   │   ├── Data/
│   │   │   ├── ApplicationDbContext.cs
│   │   │   ├── Configurations/
│   │   │   │   └── .gitkeep
│   │   │   └── Repositories/
│   │   │       └── GenericRepository.cs
│   │   └── DependencyInjection.cs
│   └── {Company}.{ProjectName}.API/
│       ├── {Company}.{ProjectName}.API.csproj
│       ├── Program.cs
│       ├── Endpoints/
│       │   └── .gitkeep
│       ├── Middleware/
│       │   └── ExceptionHandlerMiddleware.cs
│       ├── appsettings.json
│       └── appsettings.Development.json
├── tests/
│   ├── {Company}.{ProjectName}.Domain.Tests/
│   │   └── {Company}.{ProjectName}.Domain.Tests.csproj
│   ├── {Company}.{ProjectName}.Application.Tests/
│   │   └── {Company}.{ProjectName}.Application.Tests.csproj
│   └── {Company}.{ProjectName}.Integration.Tests/
│       └── {Company}.{ProjectName}.Integration.Tests.csproj
├── Directory.Build.props
├── Directory.Packages.props
├── .editorconfig
├── .gitignore
└── README.md
```

**Key Files:**

**Domain/Interfaces/IRepository.cs:**
```csharp
public interface IRepository<T> where T : class
{
    Task<T?> GetByIdAsync(Guid id, CancellationToken ct = default);
    Task<List<T>> ListAsync(CancellationToken ct = default);
    Task AddAsync(T entity, CancellationToken ct = default);
    void Update(T entity);
    void Remove(T entity);
}
```

**API/Program.cs:**
```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services
    .AddApplication()        // MediatR, FluentValidation, behaviors
    .AddInfrastructure(builder.Configuration);  // EF Core, repos

builder.Services.AddOpenApi();

var app = builder.Build();

app.UseMiddleware<ExceptionHandlerMiddleware>();
app.MapOpenApi();
app.MapScalarApiReference();
app.MapEndpoints();  // Auto-discover IEndpointGroup

app.Run();
```

**Layer dependencies:** Domain → (none), Application → Domain, Infrastructure → Application + Domain, API → All

**Packages:** MediatR, FluentValidation, EF Core, Scalar.AspNetCore

---

### Template 10: generic-ddd/ — Domain-Driven Design

```
{Company}.{ProjectName}/
├── {Company}.{ProjectName}.sln
├── src/
│   ├── {Company}.{ProjectName}.Domain/
│   │   ├── {Company}.{ProjectName}.Domain.csproj
│   │   ├── Common/
│   │   │   ├── Entity.cs
│   │   │   ├── AggregateRoot.cs
│   │   │   ├── ValueObject.cs
│   │   │   ├── DomainEvent.cs
│   │   │   └── StronglyTypedId.cs
│   │   ├── Aggregates/
│   │   │   └── .gitkeep
│   │   ├── Events/
│   │   │   └── .gitkeep
│   │   └── Interfaces/
│   │       └── IDomainEventDispatcher.cs
│   ├── {Company}.{ProjectName}.Application/
│   │   ├── {Company}.{ProjectName}.Application.csproj
│   │   ├── Commands/
│   │   ├── Queries/
│   │   ├── Behaviors/
│   │   │   └── DomainEventDispatchBehavior.cs
│   │   └── DependencyInjection.cs
│   ├── {Company}.{ProjectName}.Infrastructure/
│   │   ├── {Company}.{ProjectName}.Infrastructure.csproj
│   │   ├── Data/
│   │   │   ├── ApplicationDbContext.cs
│   │   │   └── DomainEventInterceptor.cs
│   │   └── DependencyInjection.cs
│   └── {Company}.{ProjectName}.API/
│       ├── {Company}.{ProjectName}.API.csproj
│       ├── Program.cs
│       ├── Endpoints/
│       ├── appsettings.json
│       └── appsettings.Development.json
├── tests/
│   └── {Company}.{ProjectName}.Tests/
│       └── {Company}.{ProjectName}.Tests.csproj
├── Directory.Build.props
├── Directory.Packages.props
├── .editorconfig
├── .gitignore
└── README.md
```

**Key Files:**

**Domain/Common/AggregateRoot.cs:**
```csharp
public abstract class AggregateRoot<TId> : Entity<TId> where TId : StronglyTypedId
{
    private readonly List<DomainEvent> _domainEvents = [];
    public IReadOnlyList<DomainEvent> DomainEvents => _domainEvents;

    protected void RaiseDomainEvent(DomainEvent @event) => _domainEvents.Add(@event);
    public void ClearDomainEvents() => _domainEvents.Clear();
}
```

**Domain/Common/StronglyTypedId.cs:**
```csharp
public abstract record StronglyTypedId(Guid Value)
{
    public override string ToString() => Value.ToString();
}

public sealed record OrderId(Guid Value) : StronglyTypedId(Value)
{
    public static OrderId New() => new(Guid.NewGuid());
}
```

**Packages:** MediatR, FluentValidation, EF Core, Scalar.AspNetCore

---

### Template 11: generic-modular-monolith/ — Modular Monolith

```
{Company}.{ProjectName}/
├── {Company}.{ProjectName}.sln
├── src/
│   ├── {Company}.{ProjectName}.Host/
│   │   ├── {Company}.{ProjectName}.Host.csproj
│   │   ├── Program.cs
│   │   ├── appsettings.json
│   │   └── appsettings.Development.json
│   ├── Modules/
│   │   └── {Company}.{ProjectName}.Module.Template/
│   │       ├── {Company}.{ProjectName}.Module.Template.csproj
│   │       ├── Domain/
│   │       │   ├── Entities/
│   │       │   └── Events/
│   │       ├── Application/
│   │       │   ├── Commands/
│   │       │   └── Queries/
│   │       ├── Infrastructure/
│   │       │   └── Data/
│   │       ├── Endpoints/
│   │       │   └── .gitkeep
│   │       └── ModuleExtensions.cs
│   └── Shared/
│       └── {Company}.{ProjectName}.Shared/
│           ├── {Company}.{ProjectName}.Shared.csproj
│           ├── Contracts/
│           │   └── IModuleInitializer.cs
│           ├── Common/
│           │   ├── Result.cs
│           │   └── Paginated.cs
│           └── Events/
│               └── IIntegrationEvent.cs
├── tests/
│   └── Modules/
│       └── {Company}.{ProjectName}.Module.Template.Tests/
│           └── {Company}.{ProjectName}.Module.Template.Tests.csproj
├── Directory.Build.props
├── Directory.Packages.props
├── .editorconfig
├── .gitignore
└── README.md
```

**Key Files:**

**Host/Program.cs:**
```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddOpenApi();

// Auto-discover and register modules
builder.Services.AddModules(builder.Configuration);

var app = builder.Build();

app.MapOpenApi();
app.MapScalarApiReference();
app.MapModuleEndpoints();

app.Run();
```

**Shared/Contracts/IModuleInitializer.cs:**
```csharp
public interface IModuleInitializer
{
    void ConfigureServices(IServiceCollection services, IConfiguration configuration);
    void MapEndpoints(IEndpointRouteBuilder endpoints);
}
```

**Module/ModuleExtensions.cs:**
```csharp
public sealed class TemplateModule : IModuleInitializer
{
    public void ConfigureServices(IServiceCollection services, IConfiguration configuration)
    {
        services.AddMediatR(cfg => cfg.RegisterServicesFromAssembly(typeof(TemplateModule).Assembly));
        services.AddDbContext<TemplateDbContext>(o =>
            o.UseSqlServer(configuration.GetConnectionString("TemplateModule")));
    }

    public void MapEndpoints(IEndpointRouteBuilder endpoints)
    {
        // Module endpoints registered here
    }
}
```

**Cross-module communication:** Via integration events through MediatR INotification, NOT direct references.

**Packages:** MediatR, FluentValidation, EF Core, Scalar.AspNetCore

---

## Microservice Templates (7)

(Templates 1-7 below)

---

## Template 1: command/

### Directory Tree

```
{Company}.{Domain}.Commands/
├── {Company}.{Domain}.Commands.sln
├── src/
│   ├── {Company}.{Domain}.Commands.Domain/
│   │   ├── {Company}.{Domain}.Commands.Domain.csproj
│   │   ├── Aggregates/
│   │   │   └── .gitkeep
│   │   ├── Events/
│   │   │   ├── Event.cs
│   │   │   ├── IEventData.cs
│   │   │   └── .gitkeep
│   │   ├── Exceptions/
│   │   │   └── .gitkeep
│   │   └── Resources/
│   │       ├── Phrases.resx
│   │       └── Phrases.en.resx
│   ├── {Company}.{Domain}.Commands.Application/
│   │   ├── {Company}.{Domain}.Commands.Application.csproj
│   │   ├── Commands/
│   │   │   └── .gitkeep
│   │   ├── Extensions/
│   │   │   └── ApplicationServiceExtensions.cs
│   │   └── Outputs/
│   │       └── .gitkeep
│   ├── {Company}.{Domain}.Commands.Infra/
│   │   ├── {Company}.{Domain}.Commands.Infra.csproj
│   │   ├── Database/
│   │   │   ├── ApplicationDbContext.cs
│   │   │   └── Configurations/
│   │   │       └── .gitkeep
│   │   ├── Outbox/
│   │   │   ├── OutboxMessage.cs
│   │   │   ├── CommitEventService.cs
│   │   │   └── ServiceBusPublisher.cs
│   │   ├── Options/
│   │   │   ├── ConnectionStringsOption.cs
│   │   │   └── ServiceBusOptions.cs
│   │   └── Extensions/
│   │       └── InfraServiceExtensions.cs
│   └── {Company}.{Domain}.Commands.Grpc/
│       ├── {Company}.{Domain}.Commands.Grpc.csproj
│       ├── Program.cs
│       ├── Protos/
│       │   └── .gitkeep
│       ├── Services/
│       │   └── .gitkeep
│       ├── Interceptors/
│       │   ├── ThreadCultureInterceptor.cs
│       │   └── ApplicationExceptionInterceptor.cs
│       └── appsettings.json
├── test/
│   ├── {Company}.{Domain}.Commands.Test/
│   │   └── {Company}.{Domain}.Commands.Test.csproj
│   └── {Company}.{Domain}.Commands.Test.Live/
│       └── {Company}.{Domain}.Commands.Test.Live.csproj
├── k8s/
│   └── dev-manifest.yaml
├── Dockerfile
├── .gitignore
└── Directory.Build.props
```

### Key Files Content

**Directory.Build.props**
```xml
<Project>
  <PropertyGroup>
    <TargetFramework>{NetVersion}</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
  </PropertyGroup>
</Project>
```

**Program.cs** (`Grpc/`)
```csharp
var logger = LoggerServiceBuilder.Build(configuration =>
{
    configuration.AppName = "{Company}.{Domain}.Commands";
    // Console + Seq sinks configured
});

try
{
    var builder = WebApplication.CreateBuilder(args);
    builder.Host.UseSerilog();

    builder.Services.AddApplicationServices();   // MediatR, validators
    builder.Services.AddInfraServices(builder.Configuration);  // DbContext, outbox, service bus

    builder.Services.AddGrpc(options =>
    {
        options.Interceptors.Add<ThreadCultureInterceptor>();
        options.Interceptors.Add<ApplicationExceptionInterceptor>();
    });
    builder.Services.AddAppValidators();         // Calzolari FluentValidation

    var app = builder.Build();

    // Map gRPC services here
    // app.MapGrpcService<{Domain}Service>();

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

**Event.cs** (`Domain/Events/`)
```csharp
namespace {Company}.{Domain}.Commands.Domain.Events;

public class Event<TData> where TData : IEventData
{
    public Guid Id { get; init; } = Guid.NewGuid();
    public Guid AggregateId { get; init; }
    public int Sequence { get; init; }
    public string Type { get; init; } = default!;
    public TData Data { get; init; } = default!;
    public DateTime DateTime { get; init; } = DateTime.UtcNow;
    public int Version { get; init; } = 1;
}

public interface IEventData { }
```

**Aggregate base** (created by `add-aggregate` command, pattern reference only)
```csharp
namespace {Company}.{Domain}.Commands.Domain.Aggregates;

public abstract class Aggregate<T> where T : Aggregate<T>
{
    public Guid Id { get; protected set; }
    public int Sequence { get; protected set; }
    private readonly List<Event<IEventData>> _uncommittedEvents = [];

    public IReadOnlyList<Event<IEventData>> UncommittedEvents => _uncommittedEvents;

    public void LoadFromHistory(IEnumerable<Event<IEventData>> events)
    {
        foreach (var e in events)
            ApplyChange(e, isNew: false);
    }

    protected void ApplyChange(Event<IEventData> @event, bool isNew = true)
    {
        ((dynamic)this).Apply(@event);
        if (isNew) _uncommittedEvents.Add(@event);
        Sequence = @event.Sequence;
    }
}
```

**ApplicationDbContext.cs** (`Infra/Database/`)
```csharp
namespace {Company}.{Domain}.Commands.Infra.Database;

public class ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
    : DbContext(options)
{
    // DbSet<Event<TData>> registered per event type via GenericEventConfiguration
    // DbSet<OutboxMessage> OutboxMessages

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // GenericEventConfiguration<EventEntity, EventData> per event type
        // Discriminator pattern for event types
        // Unique index on (AggregateId, Sequence)
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(ApplicationDbContext).Assembly);
    }
}
```

**OutboxMessage.cs** (`Infra/Outbox/`)
```csharp
namespace {Company}.{Domain}.Commands.Infra.Outbox;

public class OutboxMessage
{
    public Guid Id { get; init; }
    public Guid EventId { get; init; }
    public Guid AggregateId { get; init; }
    public string EventType { get; init; } = default!;
    public string Data { get; init; } = default!;
    public int Sequence { get; init; }
    public int Version { get; init; }
    public DateTime CreatedAt { get; init; } = DateTime.UtcNow;
}
```

**CommitEventService.cs** (`Infra/Outbox/`)
```csharp
// Saves events + outbox messages atomically in a single transaction
// Called from command handlers after aggregate.ApplyChange()
// Uses UnitOfWork to ensure atomicity
// After commit, fires ServiceBusPublisher.PublishPendingAsync()
```

**ServiceBusPublisher.cs** (`Infra/Outbox/`)
```csharp
// Background polling: reads unpublished OutboxMessages in batches of 200
// Publishes to Azure Service Bus with:
//   - CorrelationId = EventId
//   - PartitionKey = AggregateId
//   - Subject = EventType
//   - ApplicationProperties for metadata
// Deletes outbox messages after successful publish
// Thread-safe with lock counter pattern
```

**ApplicationServiceExtensions.cs** (`Application/Extensions/`)
```csharp
namespace {Company}.{Domain}.Commands.Application.Extensions;

public static class ApplicationServiceExtensions
{
    public static IServiceCollection AddApplicationServices(this IServiceCollection services)
    {
        services.AddMediatR(cfg =>
            cfg.RegisterServicesFromAssembly(typeof(ApplicationServiceExtensions).Assembly));
        return services;
    }
}
```

**InfraServiceExtensions.cs** (`Infra/Extensions/`)
```csharp
namespace {Company}.{Domain}.Commands.Infra.Extensions;

public static class InfraServiceExtensions
{
    public static IServiceCollection AddInfraServices(
        this IServiceCollection services, IConfiguration configuration)
    {
        services.AddDbContext<ApplicationDbContext>(options =>
            options.UseSqlServer(configuration.GetConnectionString("DefaultConnection")));

        services.AddOptions<ServiceBusOptions>()
            .Bind(configuration.GetSection("ServiceBus"))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        services.AddSingleton<ServiceBusPublisher>();
        services.AddScoped<CommitEventService>();
        return services;
    }
}
```

**Grpc .csproj** (main host project)
```xml
<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
  </PropertyGroup>
  <ItemGroup>
    <Protobuf Include="Protos\*.proto" GrpcServices="Server" />
  </ItemGroup>
  <ItemGroup>
    <PackageReference Include="Grpc.AspNetCore" />
    <PackageReference Include="Calzolari.Grpc.AspNetCore.Validation" />
    <PackageReference Include="Serilog.AspNetCore" />
    <PackageReference Include="Serilog.Sinks.Seq" />
  </ItemGroup>
  <ItemGroup>
    <ProjectReference Include="..\{Company}.{Domain}.Commands.Application\{Company}.{Domain}.Commands.Application.csproj" />
    <ProjectReference Include="..\{Company}.{Domain}.Commands.Infra\{Company}.{Domain}.Commands.Infra.csproj" />
  </ItemGroup>
</Project>
```

**Dockerfile**
```dockerfile
FROM mcr.microsoft.com/dotnet/aspnet:{NetVersion} AS base
WORKDIR /app
EXPOSE 8080

FROM mcr.microsoft.com/dotnet/sdk:{NetVersion} AS build
WORKDIR /src
COPY ["src/{Company}.{Domain}.Commands.Grpc/{Company}.{Domain}.Commands.Grpc.csproj", "src/{Company}.{Domain}.Commands.Grpc/"]
COPY ["src/{Company}.{Domain}.Commands.Application/{Company}.{Domain}.Commands.Application.csproj", "src/{Company}.{Domain}.Commands.Application/"]
COPY ["src/{Company}.{Domain}.Commands.Domain/{Company}.{Domain}.Commands.Domain.csproj", "src/{Company}.{Domain}.Commands.Domain/"]
COPY ["src/{Company}.{Domain}.Commands.Infra/{Company}.{Domain}.Commands.Infra.csproj", "src/{Company}.{Domain}.Commands.Infra/"]
RUN dotnet restore "src/{Company}.{Domain}.Commands.Grpc/{Company}.{Domain}.Commands.Grpc.csproj"
COPY . .
RUN dotnet publish "src/{Company}.{Domain}.Commands.Grpc/{Company}.{Domain}.Commands.Grpc.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=build /app/publish .
USER $APP_UID
ENTRYPOINT ["dotnet", "{Company}.{Domain}.Commands.Grpc.dll"]
```

### NuGet Packages

| Package | Project Layer |
|---------|---------------|
| MediatR | Application |
| FluentValidation | Application |
| FluentValidation.DependencyInjectionExtensions | Application |
| Microsoft.EntityFrameworkCore.SqlServer | Infra |
| Azure.Messaging.ServiceBus | Infra |
| Newtonsoft.Json | Infra |
| Grpc.AspNetCore | Grpc |
| Calzolari.Grpc.AspNetCore.Validation | Grpc |
| Serilog.AspNetCore | Grpc |
| Serilog.Sinks.Seq | Grpc |
| Serilog.Sinks.Console | Grpc |
| xunit | Test |
| Bogus | Test |
| NSubstitute | Test |
| FluentAssertions | Test |
| Microsoft.AspNetCore.Mvc.Testing | Test.Live |

### Post-Scaffold Steps

1. Create first aggregate using `/dotnet-ai.add-aggregate`
2. Define first event using `/dotnet-ai.add-event`
3. Create proto file in `Protos/` with service definition
4. Implement gRPC service in `Services/`
5. Register `MapGrpcService<T>()` in Program.cs
6. Add EF Core migration: `dotnet ef migrations add Initial`
7. Configure `appsettings.json` with connection strings and Service Bus config
8. Update `k8s/dev-manifest.yaml` with service-specific values

---

## Template 2: query/

### Directory Tree

```
{Company}.{Domain}.Queries/
├── {Company}.{Domain}.Queries.sln
├── src/
│   ├── {Company}.{Domain}.Queries.Domain/
│   │   ├── {Company}.{Domain}.Queries.Domain.csproj
│   │   ├── Entities/
│   │   │   └── .gitkeep
│   │   ├── Events/
│   │   │   ├── Event.cs
│   │   │   ├── IEventData.cs
│   │   │   └── .gitkeep
│   │   ├── Exceptions/
│   │   │   └── .gitkeep
│   │   └── Resources/
│   │       ├── Phrases.resx
│   │       └── Phrases.en.resx
│   ├── {Company}.{Domain}.Queries.Application/
│   │   ├── {Company}.{Domain}.Queries.Application.csproj
│   │   ├── EventHandlers/
│   │   │   └── .gitkeep
│   │   ├── Queries/
│   │   │   └── .gitkeep
│   │   ├── Extensions/
│   │   │   └── ApplicationServiceExtensions.cs
│   │   └── Outputs/
│   │       └── .gitkeep
│   ├── {Company}.{Domain}.Queries.Infra/
│   │   ├── {Company}.{Domain}.Queries.Infra.csproj
│   │   ├── Database/
│   │   │   ├── ApplicationDbContext.cs
│   │   │   └── Configurations/
│   │   │       └── .gitkeep
│   │   ├── Repositories/
│   │   │   ├── AsyncRepository.cs
│   │   │   └── UnitOfWork.cs
│   │   ├── Options/
│   │   │   ├── ConnectionStringsOption.cs
│   │   │   └── ServiceBusOptions.cs
│   │   ├── Listeners/
│   │   │   └── .gitkeep
│   │   └── Extensions/
│   │       └── InfraServiceExtensions.cs
│   └── {Company}.{Domain}.Queries.Grpc/
│       ├── {Company}.{Domain}.Queries.Grpc.csproj
│       ├── Program.cs
│       ├── Protos/
│       │   └── .gitkeep
│       ├── Services/
│       │   └── .gitkeep
│       ├── Interceptors/
│       │   ├── ThreadCultureInterceptor.cs
│       │   └── ApplicationExceptionInterceptor.cs
│       └── appsettings.json
├── test/
│   ├── {Company}.{Domain}.Queries.Test/
│   │   └── {Company}.{Domain}.Queries.Test.csproj
│   └── {Company}.{Domain}.Queries.Test.Live/
│       └── {Company}.{Domain}.Queries.Test.Live.csproj
├── k8s/
│   └── dev-manifest.yaml
├── Dockerfile
├── .gitignore
└── Directory.Build.props
```

### Key Files Content

**Program.cs** (`Grpc/`)
```csharp
var logger = LoggerServiceBuilder.Build(configuration =>
{
    configuration.AppName = "{Company}.{Domain}.Queries";
});

try
{
    var builder = WebApplication.CreateBuilder(args);
    builder.Host.UseSerilog();

    builder.Services.AddApplicationServices();   // MediatR, event handlers
    builder.Services.AddInfraServices(builder.Configuration);  // DbContext, repos, listeners

    builder.Services.AddGrpc(options =>
    {
        options.Interceptors.Add<ThreadCultureInterceptor>();
        options.Interceptors.Add<ApplicationExceptionInterceptor>();
    });
    builder.Services.AddAppValidators();

    var app = builder.Build();

    // Map gRPC services here
    // app.MapGrpcService<{Domain}QueryService>();

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

**Event.cs** (`Domain/Events/`)
```csharp
// Same Event<TData> and IEventData as command template
// Query side receives and deserializes events from Service Bus
namespace {Company}.{Domain}.Queries.Domain.Events;

public class Event<TData> where TData : IEventData
{
    public Guid Id { get; init; }
    public Guid AggregateId { get; init; }
    public int Sequence { get; init; }
    public string Type { get; init; } = default!;
    public TData Data { get; init; } = default!;
    public DateTime DateTime { get; init; }
    public int Version { get; init; }
}

public interface IEventData { }
```

**Query entity pattern** (reference — entities created by `add-entity`)
```csharp
namespace {Company}.{Domain}.Queries.Domain.Entities;

public class SampleEntity
{
    public Guid Id { get; private set; }
    public int Sequence { get; private set; }
    // All properties use private setters

    // CTO constructor: create from first event
    public SampleEntity(Event<SampleCreatedData> @event)
    {
        Id = @event.AggregateId;
        Sequence = @event.Sequence;
        // Map event data to properties
    }

    // Private parameterized constructor for EF Core reconstruction
    private SampleEntity() { }

    // Business method: apply subsequent events
    public void Apply(Event<SampleUpdatedData> @event)
    {
        // Strict sequence check done in handler
        Sequence = @event.Sequence;
        // Update properties from event data
    }
}
```

**AsyncRepository.cs** (`Infra/Repositories/`)
```csharp
namespace {Company}.{Domain}.Queries.Infra.Repositories;

public class AsyncRepository<T>(ApplicationDbContext context)
    where T : class
{
    protected readonly ApplicationDbContext Context = context;
    protected readonly DbSet<T> DbSet = context.Set<T>();

    public virtual async Task<T?> FindAsync(Guid id)
        => await DbSet.FindAsync(id);

    public virtual async Task AddAsync(T entity)
        => await DbSet.AddAsync(entity);

    public virtual void Update(T entity)
        => DbSet.Update(entity);

    public virtual IQueryable<T> Query()
        => DbSet.AsQueryable();
}
```

**UnitOfWork.cs** (`Infra/Repositories/`)
```csharp
namespace {Company}.{Domain}.Queries.Infra.Repositories;

public class UnitOfWork(ApplicationDbContext context) : IUnitOfWork
{
    // Lazy-loaded repository properties
    // private SampleRepository? _samples;
    // public SampleRepository Samples => _samples ??= new(context);

    public async Task<int> SaveChangesAsync(CancellationToken ct = default)
        => await context.SaveChangesAsync(ct);
}

public interface IUnitOfWork
{
    Task<int> SaveChangesAsync(CancellationToken ct = default);
}
```

**ApplicationDbContext.cs** (`Infra/Database/`)
```csharp
namespace {Company}.{Domain}.Queries.Infra.Database;

public class ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
    : DbContext(options)
{
    // DbSet<Entity> per entity type

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(ApplicationDbContext).Assembly);
    }
}
```

**Listener pattern** (reference — listeners created per subscription)
```csharp
// IHostedService with ServiceBusSessionProcessor
// Dead letter processor for failed messages
// HandelSubject() switch routing by event type
// Event<T> deserialization from UTF-8 JSON body
// LogContext enrichment (EventType, SessionId, MessageId)
// Complete on true (handler success), Abandon on false (out-of-order)
```

**Event handler pattern** (reference — handlers created by `add-event`)
```csharp
// IRequestHandler<Event<TData>, bool>
// Strict sequence checking: @event.Sequence == entity.Sequence + 1
// Return true for already-processed events (idempotent)
// Return false for out-of-order events (message abandoned, retried)
// Create entity on first event (sequence 1), update on subsequent
```

**Dockerfile**
```dockerfile
FROM mcr.microsoft.com/dotnet/aspnet:{NetVersion} AS base
WORKDIR /app
EXPOSE 8080

FROM mcr.microsoft.com/dotnet/sdk:{NetVersion} AS build
WORKDIR /src
COPY ["src/{Company}.{Domain}.Queries.Grpc/{Company}.{Domain}.Queries.Grpc.csproj", "src/{Company}.{Domain}.Queries.Grpc/"]
COPY ["src/{Company}.{Domain}.Queries.Application/{Company}.{Domain}.Queries.Application.csproj", "src/{Company}.{Domain}.Queries.Application/"]
COPY ["src/{Company}.{Domain}.Queries.Domain/{Company}.{Domain}.Queries.Domain.csproj", "src/{Company}.{Domain}.Queries.Domain/"]
COPY ["src/{Company}.{Domain}.Queries.Infra/{Company}.{Domain}.Queries.Infra.csproj", "src/{Company}.{Domain}.Queries.Infra/"]
RUN dotnet restore "src/{Company}.{Domain}.Queries.Grpc/{Company}.{Domain}.Queries.Grpc.csproj"
COPY . .
RUN dotnet publish "src/{Company}.{Domain}.Queries.Grpc/{Company}.{Domain}.Queries.Grpc.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=build /app/publish .
USER $APP_UID
ENTRYPOINT ["dotnet", "{Company}.{Domain}.Queries.Grpc.dll"]
```

### NuGet Packages

| Package | Project Layer |
|---------|---------------|
| MediatR | Application |
| FluentValidation | Application |
| FluentValidation.DependencyInjectionExtensions | Application |
| Microsoft.EntityFrameworkCore.SqlServer | Infra |
| Azure.Messaging.ServiceBus | Infra |
| Newtonsoft.Json | Infra |
| Grpc.AspNetCore | Grpc |
| Calzolari.Grpc.AspNetCore.Validation | Grpc |
| Serilog.AspNetCore | Grpc |
| Serilog.Sinks.Seq | Grpc |
| xunit | Test |
| Bogus | Test |
| NSubstitute | Test |
| FluentAssertions | Test |
| Microsoft.AspNetCore.Mvc.Testing | Test.Live |

### Post-Scaffold Steps

1. Create first entity using `/dotnet-ai.add-entity`
2. Add event data classes matching command-side events
3. Create event handlers for each event type
4. Create Service Bus listener in `Infra/Listeners/`
5. Create gRPC query service in `Services/`
6. Register listener as `IHostedService` in `InfraServiceExtensions`
7. Add EF Core migration: `dotnet ef migrations add Initial`
8. Configure `appsettings.json` with connection strings and Service Bus subscription

---

## Template 3: cosmos-query/

### Directory Tree

```
{Company}.{Domain}.Queries/
├── {Company}.{Domain}.Queries.sln
├── src/
│   ├── {Company}.{Domain}.Queries.Domain/
│   │   ├── {Company}.{Domain}.Queries.Domain.csproj
│   │   ├── Documents/
│   │   │   ├── IContainerDocument.cs
│   │   │   └── .gitkeep
│   │   ├── Events/
│   │   │   ├── Event.cs
│   │   │   ├── IEventData.cs
│   │   │   └── .gitkeep
│   │   ├── Exceptions/
│   │   │   └── .gitkeep
│   │   └── Resources/
│   │       ├── Phrases.resx
│   │       └── Phrases.en.resx
│   ├── {Company}.{Domain}.Queries.Application/
│   │   ├── {Company}.{Domain}.Queries.Application.csproj
│   │   ├── EventHandlers/
│   │   │   └── .gitkeep
│   │   ├── Queries/
│   │   │   └── .gitkeep
│   │   ├── Extensions/
│   │   │   └── ApplicationServiceExtensions.cs
│   │   └── Outputs/
│   │       └── .gitkeep
│   ├── {Company}.{Domain}.Queries.Infra/
│   │   ├── {Company}.{Domain}.Queries.Infra.csproj
│   │   ├── Cosmos/
│   │   │   ├── CosmosUnitOfWork.cs
│   │   │   ├── CosmosRepository.cs
│   │   │   └── DatabaseRunner.cs
│   │   ├── Options/
│   │   │   ├── CosmosDbOptions.cs
│   │   │   └── ServiceBusOptions.cs
│   │   ├── Listeners/
│   │   │   └── .gitkeep
│   │   └── Extensions/
│   │       └── InfraServiceExtensions.cs
│   └── {Company}.{Domain}.Queries.Grpc/
│       ├── {Company}.{Domain}.Queries.Grpc.csproj
│       ├── Program.cs
│       ├── Protos/
│       │   └── .gitkeep
│       ├── Services/
│       │   └── .gitkeep
│       ├── Interceptors/
│       │   ├── ThreadCultureInterceptor.cs
│       │   └── ApplicationExceptionInterceptor.cs
│       └── appsettings.json
├── test/
│   ├── {Company}.{Domain}.Queries.Test/
│   │   └── {Company}.{Domain}.Queries.Test.csproj
│   └── {Company}.{Domain}.Queries.Test.Live/
│       └── {Company}.{Domain}.Queries.Test.Live.csproj
├── k8s/
│   └── dev-manifest.yaml
├── Dockerfile
├── .gitignore
└── Directory.Build.props
```

**Note**: Cosmos query projects use the same naming format as SQL query projects (`{Company}.{Domain}.Queries`). Detection is by code patterns (IContainerDocument, CosmosClient) not by project name.

### Key Files Content

**IContainerDocument.cs** (`Domain/Documents/`)
```csharp
namespace {Company}.{Domain}.Queries.Domain.Documents;

public interface IContainerDocument
{
    string Id { get; }
    string Discriminator { get; }
    string PartitionKey1 { get; }      // Primary
    string PartitionKey2 { get; }      // Secondary
    string PartitionKey3 { get; }      // Tertiary
    string? ETag { get; set; }
    bool IsReport { get; }
}
```

**Cosmos document pattern** (reference — documents created by `add-entity`)
```csharp
namespace {Company}.{Domain}.Queries.Domain.Documents;

public class SampleDocument : IContainerDocument
{
    public string Id { get; private set; } = default!;
    public string Discriminator => nameof(SampleDocument);
    public string PartitionKey1 { get; private set; } = default!;
    public string PartitionKey2 { get; private set; } = default!;
    public string PartitionKey3 { get; private set; } = default!;
    public string? ETag { get; set; }
    public bool IsReport => false;

    // Properties with private setters
    public int Sequence { get; private set; }

    // Factory method from event
    public static SampleDocument FromCreated(Event<SampleCreatedData> @event)
    {
        return new SampleDocument
        {
            Id = @event.AggregateId.ToString(),
            PartitionKey1 = /* derived from event data */,
            PartitionKey2 = /* derived from event data */,
            PartitionKey3 = /* derived from event data */,
            Sequence = @event.Sequence
        };
    }

    // Nested collections
    // public List<NestedItem> Items { get; private set; } = [];
}
```

**CosmosDbOptions.cs** (`Infra/Options/`)
```csharp
namespace {Company}.{Domain}.Queries.Infra.Options;

public class CosmosDbOptions
{
    [Required] public string AccountEndpoint { get; set; } = default!;
    public string? AuthKey { get; set; }
    public bool UseServicePrincipal { get; set; }
    [Required] public string DatabaseName { get; set; } = default!;
}
```

**CosmosUnitOfWork.cs** (`Infra/Cosmos/`)
```csharp
namespace {Company}.{Domain}.Queries.Infra.Cosmos;

public class CosmosUnitOfWork(Container container)
{
    private readonly List<(IContainerDocument Doc, OperationType Op)> _operations = [];

    public void Insert(IContainerDocument doc) => _operations.Add((doc, OperationType.Insert));
    public void Replace(IContainerDocument doc) => _operations.Add((doc, OperationType.Replace));
    public void Upsert(IContainerDocument doc) => _operations.Add((doc, OperationType.Upsert));
    public void Remove(IContainerDocument doc) => _operations.Add((doc, OperationType.Remove));

    public async Task CommitAsync()
    {
        // Single operation: direct call
        // 2-100 operations: TransactionalBatch
        // 100+ operations: chunked batches
        // ETag-based optimistic concurrency (IfMatchEtag)
    }
}
```

**CosmosRepository.cs** (`Infra/Cosmos/`)
```csharp
namespace {Company}.{Domain}.Queries.Infra.Cosmos;

public class CosmosRepository(Container container)
{
    // LINQ queries with discriminator filtering
    // FeedIterator for pagination
    // Cross-partition queries with ToListWithoutPartitionFilterAsync
    // SQL queries with parameters
    // Request charge (RU) monitoring and logging
}
```

**DatabaseRunner.cs** (`Infra/Cosmos/`)
```csharp
namespace {Company}.{Domain}.Queries.Infra.Cosmos;

// IHostedService that initializes database and container on startup
// Creates database and container in development only
// Configures 3-level hierarchical partition key
// Uses CosmosDbOptions for connection configuration
// ServicePrincipal (production) vs AuthKey (development)
// Direct connection mode, CamelCase serialization, IgnoreNullValues
```

**Program.cs** (`Grpc/`)
```csharp
var logger = LoggerServiceBuilder.Build(configuration =>
{
    configuration.AppName = "{Company}.{Domain}.Queries";
});

try
{
    var builder = WebApplication.CreateBuilder(args);
    builder.Host.UseSerilog();

    builder.Services.AddApplicationServices();
    builder.Services.AddInfraServices(builder.Configuration);  // Cosmos, listeners

    builder.Services.AddGrpc(options =>
    {
        options.Interceptors.Add<ThreadCultureInterceptor>();
        options.Interceptors.Add<ApplicationExceptionInterceptor>();
    });
    builder.Services.AddAppValidators();

    var app = builder.Build();

    // app.MapGrpcService<{Domain}QueryService>();

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

**InfraServiceExtensions.cs** (`Infra/Extensions/`)
```csharp
namespace {Company}.{Domain}.Queries.Infra.Extensions;

public static class InfraServiceExtensions
{
    public static IServiceCollection AddInfraServices(
        this IServiceCollection services, IConfiguration configuration)
    {
        services.AddOptions<CosmosDbOptions>()
            .Bind(configuration.GetSection("CosmosDb"))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        services.AddOptions<ServiceBusOptions>()
            .Bind(configuration.GetSection("ServiceBus"))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        // Register CosmosClient singleton (ServicePrincipal or AuthKey based on config)
        // Register Container singleton
        // Register DatabaseRunner as IHostedService
        // Register CosmosUnitOfWork as scoped
        // Register listeners as IHostedService

        return services;
    }
}
```

**Dockerfile** — same multi-stage pattern as query template (SQL), replacing project names.

### NuGet Packages

| Package | Project Layer |
|---------|---------------|
| MediatR | Application |
| FluentValidation | Application |
| Microsoft.Azure.Cosmos | Infra |
| Azure.Identity | Infra |
| Azure.Messaging.ServiceBus | Infra |
| Newtonsoft.Json | Infra |
| Grpc.AspNetCore | Grpc |
| Calzolari.Grpc.AspNetCore.Validation | Grpc |
| Serilog.AspNetCore | Grpc |
| Serilog.Sinks.Seq | Grpc |
| xunit | Test |
| Bogus | Test |
| FluentAssertions | Test |

### Post-Scaffold Steps

1. Define IContainerDocument implementations in `Documents/`
2. Configure partition key strategy per document type
3. Add event data classes matching command-side events
4. Create event handlers with factory methods on documents
5. Create Service Bus listener in `Infra/Listeners/`
6. Configure `appsettings.json` with Cosmos DB endpoint and Service Bus subscription
7. Verify DatabaseRunner creates container with correct partition key path

---

## Template 4: processor/

### Directory Tree

```
{Company}.{Domain}.Processor/
├── {Company}.{Domain}.Processor.sln
├── src/
│   ├── {Company}.{Domain}.Processor.Domain/
│   │   ├── {Company}.{Domain}.Processor.Domain.csproj
│   │   ├── Events/
│   │   │   ├── Event.cs
│   │   │   ├── IEventData.cs
│   │   │   └── .gitkeep
│   │   ├── Exceptions/
│   │   │   └── .gitkeep
│   │   └── Resources/
│   │       ├── Phrases.resx
│   │       └── Phrases.en.resx
│   ├── {Company}.{Domain}.Processor.Application/
│   │   ├── {Company}.{Domain}.Processor.Application.csproj
│   │   ├── Handlers/
│   │   │   └── .gitkeep
│   │   ├── Extensions/
│   │   │   └── ApplicationServiceExtensions.cs
│   │   └── Outputs/
│   │       └── .gitkeep
│   ├── {Company}.{Domain}.Processor.Infra/
│   │   ├── {Company}.{Domain}.Processor.Infra.csproj
│   │   ├── Listeners/
│   │   │   └── .gitkeep
│   │   ├── GrpcClients/
│   │   │   └── .gitkeep
│   │   ├── Options/
│   │   │   ├── ServiceBusOptions.cs
│   │   │   └── ExternalServicesOptions.cs
│   │   └── Extensions/
│   │       └── InfraServiceExtensions.cs
│   └── {Company}.{Domain}.Processor.Host/
│       ├── {Company}.{Domain}.Processor.Host.csproj
│       ├── Program.cs
│       └── appsettings.json
├── test/
│   ├── {Company}.{Domain}.Processor.Test/
│   │   └── {Company}.{Domain}.Processor.Test.csproj
│   └── {Company}.{Domain}.Processor.Test.Live/
│       └── {Company}.{Domain}.Processor.Test.Live.csproj
├── k8s/
│   └── dev-manifest.yaml
├── Dockerfile
├── .gitignore
└── Directory.Build.props
```

### Key Files Content

**Program.cs** (`Host/`)
```csharp
var logger = LoggerServiceBuilder.Build(configuration =>
{
    configuration.AppName = "{Company}.{Domain}.Processor";
});

try
{
    var builder = WebApplication.CreateBuilder(args);
    builder.Host.UseSerilog();

    builder.Services.AddApplicationServices();   // MediatR handlers
    builder.Services.AddInfraServices(builder.Configuration);  // Listeners, gRPC clients

    var app = builder.Build();
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

**Listener pattern** (reference — listeners created per topic/subscription)
```csharp
namespace {Company}.{Domain}.Processor.Infra.Listeners;

public class SampleListener(IServiceProvider serviceProvider, IOptions<ServiceBusOptions> options)
    : IHostedService
{
    private ServiceBusSessionProcessor? _processor;
    private ServiceBusSessionProcessor? _deadLetterProcessor;

    public async Task StartAsync(CancellationToken ct)
    {
        var client = new ServiceBusClient(options.Value.ConnectionString);

        _processor = client.CreateSessionProcessor(
            options.Value.TopicName,
            options.Value.SubscriptionName,
            new ServiceBusSessionProcessorOptions
            {
                AutoCompleteMessages = false,
                MaxConcurrentSessions = 5,
                PrefetchCount = 10
            });

        _processor.ProcessMessageAsync += HandleMessage;
        _processor.ProcessErrorAsync += HandleError;
        await _processor.StartProcessingAsync(ct);

        // Dead letter processor setup (similar)
    }

    private async Task HandleMessage(ProcessSessionMessageEventArgs args)
    {
        using var scope = serviceProvider.CreateScope();
        var mediator = scope.ServiceProvider.GetRequiredService<IMediator>();

        var subject = args.Message.Subject;

        // HandelSubject: switch on subject to deserialize Event<T> and dispatch via MediatR
        var result = await HandleSubject(mediator, subject, args.Message);

        if (result)
            await args.CompleteMessageAsync(args.Message);
        else
            await args.AbandonMessageAsync(args.Message);
    }

    public async Task StopAsync(CancellationToken ct)
    {
        if (_processor is not null) await _processor.StopProcessingAsync(ct);
        if (_deadLetterProcessor is not null) await _deadLetterProcessor.StopProcessingAsync(ct);
    }
}
```

**ExternalServicesOptions.cs** (`Infra/Options/`)
```csharp
namespace {Company}.{Domain}.Processor.Infra.Options;

public class ExternalServicesOptions
{
    // [Required, Url] per external gRPC service
    // e.g., [Required, Url] public string CommandServiceUrl { get; set; } = default!;
    // e.g., [Required, Url] public string QueryServiceUrl { get; set; } = default!;
}
```

**gRPC client registration pattern** (reference)
```csharp
// AddGrpcClient<TService.TServiceClient> with URL from ExternalServicesOptions
// Configured via IOptions<ExternalServicesOptions>
// Exception handling: RpcException status codes
// Retry semantics via message abandonment (not Polly — processor retries by abandoning)
```

**Batch processing pattern** (reference)
```csharp
// SemaphoreSlim for concurrent session control
// ServiceBusSessionReceiver for batch message fetching
// Deduplication by SourceId using GroupBy/First
// Batch gRPC calls for efficiency
```

**InfraServiceExtensions.cs** (`Infra/Extensions/`)
```csharp
namespace {Company}.{Domain}.Processor.Infra.Extensions;

public static class InfraServiceExtensions
{
    public static IServiceCollection AddInfraServices(
        this IServiceCollection services, IConfiguration configuration)
    {
        services.AddOptions<ServiceBusOptions>()
            .Bind(configuration.GetSection("ServiceBus"))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        services.AddOptions<ExternalServicesOptions>()
            .Bind(configuration.GetSection("ExternalServices"))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        // Register gRPC clients
        // services.AddGrpcClient<SomeService.SomeServiceClient>((sp, options) =>
        // {
        //     var urls = sp.GetRequiredService<IOptions<ExternalServicesOptions>>().Value;
        //     options.Address = new Uri(urls.SomeServiceUrl);
        // });

        // Register listeners as IHostedService
        // services.AddHostedService<SampleListener>();

        return services;
    }
}
```

**Dockerfile**
```dockerfile
FROM mcr.microsoft.com/dotnet/aspnet:{NetVersion} AS base
WORKDIR /app

FROM mcr.microsoft.com/dotnet/sdk:{NetVersion} AS build
WORKDIR /src
COPY ["src/{Company}.{Domain}.Processor.Host/{Company}.{Domain}.Processor.Host.csproj", "src/{Company}.{Domain}.Processor.Host/"]
COPY ["src/{Company}.{Domain}.Processor.Application/{Company}.{Domain}.Processor.Application.csproj", "src/{Company}.{Domain}.Processor.Application/"]
COPY ["src/{Company}.{Domain}.Processor.Domain/{Company}.{Domain}.Processor.Domain.csproj", "src/{Company}.{Domain}.Processor.Domain/"]
COPY ["src/{Company}.{Domain}.Processor.Infra/{Company}.{Domain}.Processor.Infra.csproj", "src/{Company}.{Domain}.Processor.Infra/"]
RUN dotnet restore "src/{Company}.{Domain}.Processor.Host/{Company}.{Domain}.Processor.Host.csproj"
COPY . .
RUN dotnet publish "src/{Company}.{Domain}.Processor.Host/{Company}.{Domain}.Processor.Host.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=build /app/publish .
USER $APP_UID
ENTRYPOINT ["dotnet", "{Company}.{Domain}.Processor.Host.dll"]
```

### NuGet Packages

| Package | Project Layer |
|---------|---------------|
| MediatR | Application |
| Azure.Messaging.ServiceBus | Infra |
| Grpc.Net.Client | Infra |
| Grpc.Net.ClientFactory | Infra |
| Google.Protobuf | Infra |
| Grpc.Tools | Infra |
| Newtonsoft.Json | Infra |
| Serilog.AspNetCore | Host |
| Serilog.Sinks.Seq | Host |
| Serilog.Sinks.Console | Host |
| xunit | Test |
| Bogus | Test |
| NSubstitute | Test |
| FluentAssertions | Test |

### Post-Scaffold Steps

1. Create Service Bus listener(s) in `Infra/Listeners/`
2. Add event data classes for events to process
3. Create handlers in `Application/Handlers/`
4. Register gRPC clients for external services in `InfraServiceExtensions`
5. Add proto files from external services (GrpcServices="Client")
6. Register listeners as `AddHostedService<T>()` in `InfraServiceExtensions`
7. Configure `appsettings.json` with Service Bus and external service URLs

---

## Template 5: gateway-management/

### Directory Tree

```
{Company}.Gateways.{Domain}.Management/
├── {Company}.Gateways.{Domain}.Management.sln
├── src/
│   └── {Company}.Gateways.{Domain}.Management/
│       ├── {Company}.Gateways.{Domain}.Management.csproj
│       ├── Program.cs
│       ├── Controllers/
│       │   └── .gitkeep
│       ├── Models/
│       │   ├── Requests/
│       │   │   └── .gitkeep
│       │   ├── Responses/
│       │   │   └── .gitkeep
│       │   └── Paginated.cs
│       ├── GrpcClients/
│       │   └── .gitkeep
│       ├── Options/
│       │   ├── ServicesUrlsOptions.cs
│       │   └── AuthOptions.cs
│       ├── Extensions/
│       │   ├── GrpcRegistrationExtensions.cs
│       │   └── AuthExtensions.cs
│       ├── Protos/
│       │   └── .gitkeep
│       ├── Middleware/
│       │   └── .gitkeep
│       ├── Resources/
│       │   ├── Phrases.resx
│       │   └── Phrases.en.resx
│       └── appsettings.json
├── test/
│   └── {Company}.Gateways.{Domain}.Management.Test/
│       └── {Company}.Gateways.{Domain}.Management.Test.csproj
├── k8s/
│   └── dev-manifest.yaml
├── Dockerfile
├── .gitignore
└── Directory.Build.props
```

### Key Files Content

**Program.cs**
```csharp
var logger = LoggerServiceBuilder.Build(configuration =>
{
    configuration.AppName = "{Company}.Gateways.{Domain}.Management";
});

try
{
    var builder = WebApplication.CreateBuilder(args);
    builder.Host.UseSerilog();

    builder.Services.AddControllers();

    // OpenAPI with Scalar
    builder.Services.AddOpenApi();

    // gRPC client registration
    builder.Services.AddGrpcClients(builder.Configuration);

    // JWT + policy authorization
    builder.Services.AddAuthServices(builder.Configuration);

    // Options
    builder.Services.AddOptions<ServicesUrlsOptions>()
        .Bind(builder.Configuration.GetSection("ServicesUrls"))
        .ValidateDataAnnotations()
        .ValidateOnStart();

    var app = builder.Build();

    app.UseAuthentication();
    app.UseAuthorization();

    app.MapOpenApi();
    app.MapScalarApiReference(options =>
    {
        options.Theme = ScalarTheme.BluePlanet;
        // Basic auth protection on documentation endpoints
    });

    app.MapControllers();

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

**ServicesUrlsOptions.cs** (`Options/`)
```csharp
namespace {Company}.Gateways.{Domain}.Management.Options;

public class ServicesUrlsOptions
{
    // One [Required, Url] property per backing gRPC service
    // [Required, Url] public string CommandServiceUrl { get; set; } = default!;
    // [Required, Url] public string QueryServiceUrl { get; set; } = default!;
}
```

**GrpcRegistrationExtensions.cs** (`Extensions/`)
```csharp
namespace {Company}.Gateways.{Domain}.Management.Extensions;

public static class GrpcRegistrationExtensions
{
    public static IServiceCollection AddGrpcClients(
        this IServiceCollection services, IConfiguration configuration)
    {
        // Per backing service:
        // services.AddGrpcClient<CommandService.CommandServiceClient>((sp, options) =>
        // {
        //     var urls = sp.GetRequiredService<IOptions<ServicesUrlsOptions>>().Value;
        //     options.Address = new Uri(urls.CommandServiceUrl);
        // });

        return services;
    }
}
```

**AuthExtensions.cs** (`Extensions/`)
```csharp
namespace {Company}.Gateways.{Domain}.Management.Extensions;

public static class AuthExtensions
{
    public static IServiceCollection AddAuthServices(
        this IServiceCollection services, IConfiguration configuration)
    {
        services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
            .AddJwtBearer(options =>
            {
                options.Authority = configuration["Auth:Authority"];
                options.Audience = configuration["Auth:Audience"];
            });

        services.AddAuthorization(options =>
        {
            // Policy-based authorization (CircleOfficer, Operator, Reporter, etc.)
            // options.AddPolicy("CircleOfficer", policy => ...);
        });

        // Pentagon device authentication middleware (if applicable)

        return services;
    }
}
```

**Paginated.cs** (`Models/`)
```csharp
namespace {Company}.Gateways.{Domain}.Management.Models;

public class Paginated<T>
{
    public List<T> Items { get; init; } = [];
    public int TotalCount { get; init; }
    public int PageNumber { get; init; }
    public int PageSize { get; init; }
    public bool HasNextPage => PageNumber * PageSize < TotalCount;
}
```

**Controller pattern** (reference — controllers created by `add-endpoint`)
```csharp
namespace {Company}.Gateways.{Domain}.Management.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize(Policy = "CircleOfficer")]
public class SampleController(CommandService.CommandServiceClient commandClient,
    QueryService.QueryServiceClient queryClient) : ControllerBase
{
    [HttpGet]
    public async Task<ActionResult<Paginated<SampleResponse>>> GetAll(
        [FromQuery] int page = 1, [FromQuery] int pageSize = 20)
    {
        var grpcResponse = await queryClient.GetAllAsync(new GetAllRequest
        {
            Page = page, PageSize = pageSize
        });
        return Ok(grpcResponse.ToPaginated());
    }

    [HttpPost]
    public async Task<ActionResult<CreateSampleResponse>> Create(
        [FromBody] CreateSampleRequest request)
    {
        var grpcResponse = await commandClient.CreateAsync(request.ToGrpc());
        return Ok(grpcResponse.ToResponse());
    }
}
```

**Dockerfile**
```dockerfile
FROM mcr.microsoft.com/dotnet/aspnet:{NetVersion} AS base
WORKDIR /app
EXPOSE 8080

FROM mcr.microsoft.com/dotnet/sdk:{NetVersion} AS build
WORKDIR /src
COPY ["src/{Company}.Gateways.{Domain}.Management/{Company}.Gateways.{Domain}.Management.csproj", "src/{Company}.Gateways.{Domain}.Management/"]
RUN dotnet restore "src/{Company}.Gateways.{Domain}.Management/{Company}.Gateways.{Domain}.Management.csproj"
COPY . .
RUN dotnet publish "src/{Company}.Gateways.{Domain}.Management/{Company}.Gateways.{Domain}.Management.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=build /app/publish .
USER $APP_UID
ENTRYPOINT ["dotnet", "{Company}.Gateways.{Domain}.Management.dll"]
```

### NuGet Packages

| Package | Project Layer |
|---------|---------------|
| Grpc.Net.Client | Main |
| Grpc.Net.ClientFactory | Main |
| Google.Protobuf | Main |
| Grpc.Tools | Main |
| Microsoft.AspNetCore.Authentication.JwtBearer | Main |
| Scalar.AspNetCore | Main |
| Serilog.AspNetCore | Main |
| Serilog.Sinks.Seq | Main |
| xunit | Test |
| FluentAssertions | Test |
| Microsoft.AspNetCore.Mvc.Testing | Test |

### Post-Scaffold Steps

1. Add proto files from backing services in `Protos/` (GrpcServices="Client")
2. Configure gRPC client registration per service in `GrpcRegistrationExtensions`
3. Define authorization policies in `AuthExtensions`
4. Create controllers using `/dotnet-ai.add-endpoint`
5. Add request/response models in `Models/`
6. Configure `appsettings.json` with backing service URLs and auth settings
7. Verify Scalar API docs are accessible

---

## Template 6: gateway-consumer/

### Directory Tree

```
{Company}.Gateways.{Domain}.Consumers/
├── {Company}.Gateways.{Domain}.Consumers.sln
├── src/
│   └── {Company}.Gateways.{Domain}.Consumers/
│       ├── {Company}.Gateways.{Domain}.Consumers.csproj
│       ├── Program.cs
│       ├── Controllers/
│       │   ├── V1/
│       │   │   └── .gitkeep
│       │   └── V2/
│       │       └── .gitkeep
│       ├── Models/
│       │   ├── V1/
│       │   │   ├── Requests/
│       │   │   │   └── .gitkeep
│       │   │   └── Responses/
│       │   │       └── .gitkeep
│       │   ├── V2/
│       │   │   ├── Requests/
│       │   │   │   └── .gitkeep
│       │   │   └── Responses/
│       │   │       └── .gitkeep
│       │   └── Paginated.cs
│       ├── GrpcClients/
│       │   └── .gitkeep
│       ├── Options/
│       │   ├── ServicesUrlsOptions.cs
│       │   └── AuthOptions.cs
│       ├── Extensions/
│       │   ├── GrpcRegistrationExtensions.cs
│       │   └── AuthExtensions.cs
│       ├── Protos/
│       │   └── .gitkeep
│       ├── Middleware/
│       │   └── .gitkeep
│       ├── Resources/
│       │   ├── Phrases.resx
│       │   └── Phrases.en.resx
│       └── appsettings.json
├── test/
│   └── {Company}.Gateways.{Domain}.Consumers.Test/
│       └── {Company}.Gateways.{Domain}.Consumers.Test.csproj
├── k8s/
│   └── dev-manifest.yaml
├── Dockerfile
├── .gitignore
└── Directory.Build.props
```

### Key Files Content

**Program.cs**
```csharp
var logger = LoggerServiceBuilder.Build(configuration =>
{
    configuration.AppName = "{Company}.Gateways.{Domain}.Consumers";
});

try
{
    var builder = WebApplication.CreateBuilder(args);
    builder.Host.UseSerilog();

    builder.Services.AddControllers();

    // OpenAPI with Scalar (new projects use Scalar, not Swagger)
    builder.Services.AddOpenApi();

    // API versioning
    builder.Services.AddApiVersioning(options =>
    {
        options.DefaultApiVersion = new ApiVersion(1, 0);
        options.AssumeDefaultVersionWhenUnspecified = true;
        options.ReportApiVersions = true;
    }).AddApiExplorer(options =>
    {
        options.GroupNameFormat = "'v'VVV";
        options.SubstituteApiVersionInUrl = true;
    });

    // gRPC client registration
    builder.Services.AddGrpcClients(builder.Configuration);

    // JWT authorization
    builder.Services.AddAuthServices(builder.Configuration);

    builder.Services.AddOptions<ServicesUrlsOptions>()
        .Bind(builder.Configuration.GetSection("ServicesUrls"))
        .ValidateDataAnnotations()
        .ValidateOnStart();

    var app = builder.Build();

    app.UseAuthentication();
    app.UseAuthorization();

    app.MapOpenApi();
    app.MapScalarApiReference(options =>
    {
        options.Theme = ScalarTheme.BluePlanet;
    });

    app.MapControllers();

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

**Versioned controller pattern** (reference)
```csharp
namespace {Company}.Gateways.{Domain}.Consumers.Controllers.V1;

[ApiController]
[Route("api/v{version:apiVersion}/[controller]")]
[ApiVersion("1.0")]
[Authorize]
public class SampleController(QueryService.QueryServiceClient queryClient)
    : ControllerBase
{
    [HttpGet("{id:guid}")]
    public async Task<ActionResult<V1.SampleResponse>> GetById(Guid id)
    {
        var grpcResponse = await queryClient.GetByIdAsync(
            new GetByIdRequest { Id = id.ToString() });
        return Ok(grpcResponse.ToV1Response());
    }
}
```

```csharp
namespace {Company}.Gateways.{Domain}.Consumers.Controllers.V2;

[ApiController]
[Route("api/v{version:apiVersion}/[controller]")]
[ApiVersion("2.0")]
[Authorize]
public class SampleController(QueryService.QueryServiceClient queryClient)
    : ControllerBase
{
    [HttpGet("{id:guid}")]
    public async Task<ActionResult<V2.SampleResponse>> GetById(Guid id)
    {
        // V2 may return enriched response or different shape
        var grpcResponse = await queryClient.GetByIdAsync(
            new GetByIdRequest { Id = id.ToString() });
        return Ok(grpcResponse.ToV2Response());
    }
}
```

**Key differences from gateway-management**:
- Multi-version folder structure (`Controllers/V1/`, `Controllers/V2/`, `Models/V1/`, `Models/V2/`)
- API versioning middleware (Asp.Versioning)
- Consumer-facing auth (token-based, no Pentagon)
- Scalar API docs for all new projects (Swagger is legacy only for existing old gateways)

**Dockerfile** — same multi-stage pattern as gateway-management, replacing project names.

### NuGet Packages

| Package | Project Layer |
|---------|---------------|
| Grpc.Net.Client | Main |
| Grpc.Net.ClientFactory | Main |
| Google.Protobuf | Main |
| Grpc.Tools | Main |
| Microsoft.AspNetCore.Authentication.JwtBearer | Main |
| Asp.Versioning.Mvc | Main |
| Asp.Versioning.Mvc.ApiExplorer | Main |
| Scalar.AspNetCore | Main |
| Serilog.AspNetCore | Main |
| Serilog.Sinks.Seq | Main |
| xunit | Test |
| FluentAssertions | Test |
| Microsoft.AspNetCore.Mvc.Testing | Test |

### Post-Scaffold Steps

1. Add proto files from backing services in `Protos/` (GrpcServices="Client")
2. Configure gRPC client registration in `GrpcRegistrationExtensions`
3. Create V1 controllers and models using `/dotnet-ai.add-endpoint`
4. Define consumer-facing auth policies in `AuthExtensions`
5. Configure `appsettings.json` with backing service URLs and auth
6. Plan V2 versioning strategy if needed

---

## Template 7: controlpanel-module/

### Directory Tree

```
{Company}.ControlPanel.{Domain}/
├── {Company}.ControlPanel.{Domain}.sln
├── src/
│   └── {Company}.ControlPanel.{Domain}/
│       ├── {Company}.ControlPanel.{Domain}.csproj
│       ├── Program.cs
│       ├── wwwroot/
│       │   └── css/
│       │       └── app.css
│       ├── App.razor
│       ├── _Imports.razor
│       ├── Pages/
│       │   ├── Index.razor
│       │   └── .gitkeep
│       ├── Components/
│       │   ├── Dialogs/
│       │   │   └── .gitkeep
│       │   └── Shared/
│       │       └── .gitkeep
│       ├── Gateways/
│       │   ├── Gateway.cs
│       │   ├── HttpExtensions.cs
│       │   └── .gitkeep
│       ├── Models/
│       │   ├── Filters/
│       │   │   └── .gitkeep
│       │   ├── Requests/
│       │   │   └── .gitkeep
│       │   └── Responses/
│       │   │   └── .gitkeep
│       ├── Services/
│       │   ├── MenuItemsProvider.cs
│       │   └── WebAppRegistration.cs
│       └── Resources/
│           ├── Phrases.resx
│           └── Phrases.en.resx
├── test/
│   └── {Company}.ControlPanel.{Domain}.Test/
│       └── {Company}.ControlPanel.{Domain}.Test.csproj
├── .gitignore
└── Directory.Build.props
```

### Key Files Content

**Program.cs**
```csharp
var builder = WebAssemblyHostBuilder.CreateDefault(args);
builder.RootComponents.Add<App>("#app");

// Gateway HTTP client
builder.Services.AddServerApiClients(builder.Configuration);

// MudBlazor
builder.Services.AddMudServices(config =>
{
    config.SnackbarConfiguration.PositionClass = Defaults.Classes.Position.BottomRight;
});

// Localization
builder.Services.AddLocalization();

// Menu items
builder.Services.AddScoped<MenuItemsProvider>();

await builder.Build().RunAsync();
```

**Gateway.cs** (`Gateways/`)
```csharp
namespace {Company}.ControlPanel.{Domain}.Gateways;

public class Gateway(HttpClient httpClient)
{
    // Nested Management classes, lazy initialized
    // private {Domain}Management? _{domain}Management;
    // public {Domain}Management {Domain} => _{domain}Management ??= new(httpClient);
}

// public class {Domain}Management(HttpClient httpClient)
// {
//     private const string BaseRoute = "api/{domain}";
//
//     public Task<ResponseResult<Paginated<SampleResponse>>> GetAllAsync(SampleFilter filter)
//         => httpClient.GetAsync<Paginated<SampleResponse>>($"{BaseRoute}?{filter.ToQueryString()}");
//
//     public Task<ResponseResult<CreateResponse>> CreateAsync(CreateRequest request)
//         => httpClient.PostAsync<CreateResponse>(BaseRoute, request);
// }
```

**HttpExtensions.cs** (`Gateways/`)
```csharp
namespace {Company}.ControlPanel.{Domain}.Gateways;

public static class HttpExtensions
{
    public static async Task<ResponseResult<T>> GetAsync<T>(
        this HttpClient client, string url)
    {
        // Makes HTTP call, deserializes response
        // Returns SuccessResult<T> or FailedResult<T> with ProblemDetails
    }

    public static async Task<ResponseResult<T>> PostAsync<T>(
        this HttpClient client, string url, object body)
    {
        // Serializes body, makes HTTP call, deserializes response
    }

    // PutAsync, PatchAsync, DeleteAsync follow same pattern
    // PostAsFormAsync for file uploads (MultipartFormDataContent)
}
```

**ResponseResult pattern** (reference)
```csharp
// ResponseResult<T> abstract record — SuccessResult<T> or FailedResult<T>
// Switch() and SwitchAsync() extension methods
// Usage in pages:
//   var result = await gateway.{Domain}.GetAllAsync(filter);
//   result.Switch(
//       success => items = success.Value.Items,
//       failure => snackbar.Add(failure.ProblemDetails.Detail, Severity.Error)
//   );
```

**QueryStringBindable pattern** (reference — filters created by `add-page`)
```csharp
namespace {Company}.ControlPanel.{Domain}.Models.Filters;

public class SampleFilter : QueryStringBindable, INotifyPropertyChanged
{
    private string? _search;
    public string? Search
    {
        get => _search;
        set => UpdateQueryStringIfChanged(ref _search, value);
    }

    private int _page = 1;
    public int Page
    {
        get => _page;
        set => UpdateQueryStringIfChanged(ref _page, value);
    }

    // BindToNavigationManager for URL state sync
    // PropertyChanged triggers data reload
}
```

**Page pattern** (reference — pages created by `add-page`)
```csharp
@page "/{domain}"
@inject Gateway Gateway
@inject ISnackbar Snackbar

<MudDataGrid T="SampleResponse" Items="@_items" Loading="@_loading"
    ServerData="LoadServerData">
    <Columns>
        <PropertyColumn Property="x => x.Name" Title="@Phrases.Name" />
        <!-- More columns -->
    </Columns>
</MudDataGrid>

@code {
    private SampleFilter _filter = new();
    private List<SampleResponse> _items = [];
    private bool _loading = true;

    protected override async Task OnInitializedAsync()
    {
        _filter.BindToNavigationManager(NavigationManager);
        _filter.PropertyChanged += async (_, _) => await LoadData();
        await LoadData();
    }

    private async Task LoadData()
    {
        _loading = true;
        var result = await Gateway.{Domain}.GetAllAsync(_filter);
        result.Switch(
            success => _items = success.Value.Items,
            failure => Snackbar.Add(failure.ProblemDetails.Detail, Severity.Error)
        );
        _loading = false;
        StateHasChanged();
    }
}
```

**WebAppRegistration.cs** (`Services/`)
```csharp
namespace {Company}.ControlPanel.{Domain}.Services;

public static class WebAppRegistration
{
    public static IServiceCollection AddServerApiClients(
        this IServiceCollection services, IConfiguration configuration)
    {
        services.AddHttpClient<Gateway>(client =>
        {
            client.BaseAddress = new Uri(configuration["GatewayBaseUrl"]!);
        });
        // AddAuthenticationService if needed
        return services;
    }
}
```

**MenuItemsProvider.cs** (`Services/`)
```csharp
namespace {Company}.ControlPanel.{Domain}.Services;

public class MenuItemsProvider
{
    // Provides MudNavMenu items for this module
    // Integrates with the main ControlPanel shell navigation
    // Icon, Title, Href, Group for each page
}
```

**_Imports.razor**
```razor
@using Microsoft.AspNetCore.Components.Web
@using Microsoft.AspNetCore.Components.WebAssembly.Hosting
@using MudBlazor
@using {Company}.ControlPanel.{Domain}.Gateways
@using {Company}.ControlPanel.{Domain}.Models.Filters
@using {Company}.ControlPanel.{Domain}.Models.Responses
@using {Company}.ControlPanel.{Domain}.Resources
```

**.csproj**
```xml
<Project Sdk="Microsoft.NET.Sdk.BlazorWebAssembly">
  <PropertyGroup>
    <TargetFramework>{NetVersion}</TargetFramework>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="MudBlazor" />
    <PackageReference Include="Microsoft.AspNetCore.Components.WebAssembly" />
    <PackageReference Include="Microsoft.Extensions.Http" />
  </ItemGroup>
</Project>
```

### NuGet Packages

| Package | Project Layer |
|---------|---------------|
| MudBlazor | Main |
| Microsoft.AspNetCore.Components.WebAssembly | Main |
| Microsoft.AspNetCore.Components.WebAssembly.DevServer | Main (dev) |
| Microsoft.Extensions.Http | Main |
| Microsoft.Extensions.Localization | Main |
| bunit | Test |
| xunit | Test |
| FluentAssertions | Test |

### Post-Scaffold Steps

1. Configure `Gateway.cs` with management classes for each domain area
2. Create pages using `/dotnet-ai.add-page`
3. Define filter models in `Models/Filters/`
4. Add request/response models matching the gateway API
5. Configure `MenuItemsProvider` with navigation items
6. Set `GatewayBaseUrl` in configuration
7. Register module in the main ControlPanel shell (if applicable)

---

## Cross-Template Standards

### appsettings.json (all templates)

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information"
    }
  },
  "Serilog": {
    "AppName": "{Company}.{Domain}.{Side}",
    "SeqUrl": "http://localhost:5341",
    "WriteToConsole": true
  }
}
```

Additional sections per template:
- **Command/Query (SQL)**: `"ConnectionStrings": { "DefaultConnection": "" }`
- **Query (Cosmos)**: `"CosmosDb": { "AccountEndpoint": "", "AuthKey": "", "DatabaseName": "" }`
- **Command/Query/Processor**: `"ServiceBus": { "ConnectionString": "", "TopicName": "", "SubscriptionName": "" }`
- **Gateway**: `"ServicesUrls": { "CommandServiceUrl": "", "QueryServiceUrl": "" }`, `"Auth": { "Authority": "", "Audience": "" }`
- **ControlPanel**: `"GatewayBaseUrl": ""`

### k8s/dev-manifest.yaml (all backend templates)

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: {company}-{domain}
---
apiVersion: v1
kind: Secret
metadata:
  name: {company}-{domain}-{side}-secrets
  namespace: {company}-{domain}
type: Opaque
stringData:
  ConnectionStrings__DefaultConnection: "___CONNECTION_STRING___"
  ServiceBus__ConnectionString: "___SERVICEBUS_CONNECTION___"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {company}-{domain}-{side}
  namespace: {company}-{domain}
spec:
  replicas: 1
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  selector:
    matchLabels:
      app: {company}-{domain}-{side}
  template:
    metadata:
      labels:
        app: {company}-{domain}-{side}
    spec:
      containers:
      - name: {company}-{domain}-{side}
        image: "___ACR_NAME___.azurecr.io/{company}-{domain}-{side}:___IMAGE_TAG___"
        ports:
        - containerPort: 8080
        envFrom:
        - secretRef:
            name: {company}-{domain}-{side}-secrets
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "250m"
---
apiVersion: v1
kind: Service
metadata:
  name: {company}-{domain}-{side}
  namespace: {company}-{domain}
spec:
  selector:
    app: {company}-{domain}-{side}
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
```

### .gitignore (all templates)

```
## .NET
bin/
obj/
*.user
*.suo
*.cache
*.dll
*.pdb

## IDE
.vs/
.idea/
*.swp

## Secrets
appsettings.*.local.json
*.pfx

## Build
publish/
out/

## Test Results
TestResults/
coverage/
```

### Interceptors (shared across command, query, cosmos-query)

**ThreadCultureInterceptor.cs**
```csharp
// Reads "language" header from gRPC metadata
// Sets Thread.CurrentThread.CurrentCulture and CurrentUICulture
// Enables localized resource string responses
```

**ApplicationExceptionInterceptor.cs**
```csharp
// Catches domain exceptions implementing IProblemDetailsProvider
// Converts to RpcException with appropriate StatusCode
// Maps: NotFound → NotFound, Validation → InvalidArgument, Business → FailedPrecondition
// Serializes ProblemDetails into RpcException trailers
```

### Test Project Structure (all templates)

**Test .csproj** (unit tests)
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <ItemGroup>
    <PackageReference Include="xunit" />
    <PackageReference Include="xunit.runner.visualstudio" />
    <PackageReference Include="Bogus" />
    <PackageReference Include="NSubstitute" />
    <PackageReference Include="FluentAssertions" />
  </ItemGroup>
  <ItemGroup>
    <ProjectReference Include="..\..\src\{ProjectLayer}\{ProjectLayer}.csproj" />
  </ItemGroup>
</Project>
```

**Test.Live .csproj** (integration/live tests)
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <ItemGroup>
    <PackageReference Include="xunit" />
    <PackageReference Include="xunit.runner.visualstudio" />
    <PackageReference Include="Bogus" />
    <PackageReference Include="FluentAssertions" />
    <PackageReference Include="Microsoft.AspNetCore.Mvc.Testing" />
    <PackageReference Include="Grpc.Net.Client" />
  </ItemGroup>
  <ItemGroup>
    <ProjectReference Include="..\..\src\{HostProject}\{HostProject}.csproj" />
  </ItemGroup>
</Project>
```

**Testing patterns used across all templates**:
- `CustomConstructorFaker<T>` — uses `RuntimeHelpers.GetUninitializedObject` to bypass constructors
- `AssertEquality` extension methods — compare events to entities, requests to events
- `WebApplicationFactory<Program>` with `WithDefaultConfigurations` extension
- `SetLiveTestsDefaultEnvironment` / `SetUnitTestsDefaultEnvironment` helpers
- `FakeServicesHelper` for mocking external gRPC services

---

## Template Selection Logic

The `/dotnet-ai.implement` command determines which template to use based on the service map:

| Service Map Entry | Template Used |
|---|---|
| `{Company}.{Domain}.Commands` | `command/` |
| `{Company}.{Domain}.Queries` (SQL patterns detected or specified) | `query/` |
| `{Company}.{Domain}.Queries` (Cosmos patterns detected or specified) | `cosmos-query/` |
| `{Company}.{Domain}.Processor` | `processor/` |
| `{Company}.Gateways.{Domain}.Management` | `gateway-management/` |
| `{Company}.Gateways.{Domain}.Consumers` | `gateway-consumer/` |
| `{Company}.ControlPanel.{Domain}` | `controlpanel-module/` |

Detection between `query/` and `cosmos-query/` is based on:
1. Explicit `storage: cosmos` or `storage: sql` in service map
2. If the domain already has Cosmos patterns in other services
3. Default: SQL (query template)
