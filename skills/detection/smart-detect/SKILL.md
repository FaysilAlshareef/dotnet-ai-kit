---
name: smart-detect
description: "AI-assisted project type detection for .NET projects (microservice and generic architectures)"
metadata:
  category: detection
  when-to-use: "When detecting project architecture type or analyzing .NET project structure"
---
# Smart Detection Skill

You are analyzing a .NET project to determine its architectural type using behavioral analysis.

## Input

You will receive:
1. **Project directory path** to scan
2. **Up to 10 representative files** from the project (you will read these yourself)

## Step 1: Gather Project Context

Read the following files to build a picture of the project:

### Configuration Files (read first)
1. `Program.cs` or `Startup.cs` — startup configuration
2. `*.csproj` — NuGet packages, target framework, SDK type
3. `*.sln` or `*.slnx` — solution structure

### Code Samples (read up to 5)
1. `**/Application/**/Handlers/**/*.cs` or `**/Features/**/*Handler.cs`
2. `**/Controllers/**/*.cs`
3. `**/Services/**/*Service.cs`
4. `**/Domain/**/Aggregate*.cs` or `**/Domain/**/Core/*.cs`
5. `**/Endpoints/**/*.cs` or `**/Modules/**/*.cs`

### Structural Indicators (check existence)
- `Features/` directory — VSA indicator
- `Domain/`, `Application/`, `Infrastructure/` directories — Clean Architecture indicator
- `BoundedContexts/` or `Contexts/` directory — DDD indicator
- `Modules/` directory — Modular Monolith indicator
- `Controllers/` directory — traditional MVC/API
- `Listeners/` or `ServiceBus/` directory — event-driven
- `*.razor` files — Blazor UI

## Step 2: Analyze Data Flow

For each handler/service file, analyze:

### What comes IN?
- **Commands**: handler takes a command object (e.g., `IRequestHandler<CreateOrderCommand>`)
- **Events**: handler takes an event object (e.g., `IRequestHandler<Event<OrderCreatedData>, bool>`)
- **HTTP requests**: controller actions with `[HttpGet]`, `[HttpPost]`, etc.
- **Minimal API**: `app.MapGet()`, `app.MapPost()`, endpoint definitions

### What happens INSIDE?
- **Domain manipulation**: loads events by aggregate ID, rebuilds aggregate, calls domain methods, commits
- **Database save**: calls `SaveChangesAsync`, `AddAsync`, repository Add/Update
- **Service calls**: calls gRPC/HTTP clients to other services
- **Message publishing**: publishes to ServiceBus/queue/topic
- **Feature orchestration**: coordinates within a single feature slice

### What goes OUT?
- **Nothing (void/Task)**: typical command handler
- **Bool acknowledgment**: typical event handler
- **Data (DTOs/responses)**: typical query handler or controller
- **HTML/Blazor**: UI rendering

## Step 3: Classify

### Microservice Mode Types

These types are for projects following a CQRS/event-sourced microservice architecture:

| Type | IN | INSIDE | OUT |
|------|-----|--------|-----|
| **command** | Commands | Load aggregate -> domain method -> commit events | void/Task |
| **query-sql** | Events | Save to SQL database | bool (ack) |
| **query-cosmos** | Events | Save to Cosmos DB | bool (ack) |
| **processor** | Events | Call other gRPC services OR publish to message bus | bool (ack) |
| **gateway** | HTTP requests | Forward to gRPC services | HTTP responses |
| **controlpanel** | Browser requests | Blazor components render UI | HTML/Blazor |
| **hybrid** | Commands AND Events | Both domain manipulation AND DB save | Mixed |

### Generic Mode Types

These types are for projects following common .NET architectural patterns outside CQRS microservices:

| Type | Key Indicators | Structure | Typical Patterns |
|------|---------------|-----------|-----------------|
| **vsa** | `Features/` directory with self-contained slices | Each feature folder contains handler, validator, model, endpoint | MediatR handlers per feature, minimal cross-feature dependencies |
| **clean-arch** | 3+ layers: Domain, Application, Infrastructure | Separate projects per layer, dependency inversion | Use cases in Application, entities in Domain, repos in Infrastructure |
| **ddd** | `BoundedContexts/` or `Contexts/` directory | Bounded contexts with internal layering | Aggregates, value objects, domain events, anti-corruption layers |
| **modular-monolith** | `Modules/` directory with independent modules | Each module has its own API, domain, infrastructure | Module-to-module communication via contracts/events |
| **generic** | None of the above patterns match | Varies — could be simple API, console app, library | Standard .NET project without strong architectural pattern |

### VSA (Vertical Slice Architecture) — Detailed Indicators

**Structure signals:**
- `Features/` or `Slices/` directory at project root
- Each subdirectory under Features/ contains all layers for one feature (handler, request, response, validator)
- No separate `Application/`, `Domain/`, `Infrastructure/` top-level layers

**Code signals:**
- MediatR `IRequestHandler<TRequest, TResponse>` per feature
- `IValidator<T>` paired with handlers in same folder
- Endpoint classes or minimal API mappings grouped by feature
- AutoMapper/Mapster profiles per feature folder

**NuGet signals:**
- `MediatR`, `FluentValidation`, `Carter` or `FastEndpoints`

### Clean Architecture — Detailed Indicators

**Structure signals:**
- 3+ separate projects: `*.Domain`, `*.Application`, `*.Infrastructure`, `*.Api` (or `*.Web`, `*.Presentation`)
- Domain project has NO references to other projects
- Application references only Domain
- Infrastructure references Application (and sometimes Domain)
- API/Web references all others

**Code signals:**
- Interfaces in Application (`IRepository<T>`, `IUnitOfWork`)
- Implementations in Infrastructure
- Use case classes or command/query handlers in Application
- Entities and value objects in Domain with no framework dependencies

**NuGet signals:**
- Domain project: minimal packages (maybe `MediatR.Contracts` only)
- Infrastructure: `EntityFrameworkCore`, `Dapper`, provider packages

### DDD (Domain-Driven Design) — Detailed Indicators

**Structure signals:**
- `BoundedContexts/` or `Contexts/` directory
- Each bounded context has its own Domain, Application, Infrastructure
- `SharedKernel/` or `BuildingBlocks/` directory for cross-cutting concerns
- `AntiCorruption/` or `ACL/` directories

**Code signals:**
- `AggregateRoot` or `Entity` base classes in domain
- Value objects with structural equality
- Domain events (`IDomainEvent`, `DomainEvent`)
- Domain services with business logic
- Repository interfaces per aggregate root

**NuGet signals:**
- Domain event libraries, CQRS packages

### Modular Monolith — Detailed Indicators

**Structure signals:**
- `Modules/` directory with independent module directories
- Each module has its own `Api/`, `Core/` (or `Domain/`), `Infrastructure/`
- `Contracts/` or `IntegrationEvents/` for inter-module communication
- Shared `Infrastructure/` or `Common/` at root level

**Code signals:**
- Module registration in Program.cs (`AddModule<OrderModule>()` pattern)
- Internal module classes (not public)
- Inter-module communication via events or contracts
- Each module has its own DbContext or schema

**NuGet signals:**
- Module framework packages if any

### Generic — When to Classify

Use **generic** when:
- The project is a simple Web API without clear architectural layering
- Console application or background worker
- Class library or NuGet package project
- The project structure does not match any of the above patterns
- Mixed patterns that do not clearly fit one category

## Decision Process

Apply rules in order — first match wins:

1. If `.razor` files exist → **controlpanel**
2. If controllers forward ALL requests to gRPC clients (no local DB) → **gateway**
3. If REST API with reverse proxy (YARP) → **gateway**
4. If handlers receive commands AND events, manipulate domain AND save to DB → **hybrid**
5. If handlers receive commands, manipulate domain aggregates, commit events, NOT consuming events → **command**
6. If handlers receive events, call other services/publish messages, NOT saving to DB → **processor**
7. If handlers receive events and save to Cosmos DB → **query-cosmos**
8. If handlers receive events and save to SQL/EF → **query-sql**
9. If `Features/` directory with self-contained feature handlers → **vsa**
10. If 3+ layers (Domain, Application, Infrastructure) with dependency inversion → **clean-arch**
11. If `BoundedContexts/` or `Contexts/` directory with aggregate roots → **ddd**
12. If `Modules/` directory with independent module structure → **modular-monolith**
13. Otherwise → **generic**

## Output Format

```yaml
classification: {type}
mode: {microservice|generic}
confidence: {high|medium|low}
dotnet_version: "{version from csproj TargetFramework}"
architecture: "{human-readable description}"
namespace_format: "{detected namespace pattern}"
evidence:
  1. {most important behavioral evidence}
  2. {second most important evidence}
  3. {third most important evidence}
reasoning: "{1-2 sentences explaining the data flow that led to this classification}"
packages:
  - {key NuGet packages detected}
```

## Important Notes

- Focus on BEHAVIOR, not naming. A class called "OrderService" tells you nothing about data flow.
- A handler that receives events AND saves to DB is a QUERY handler, even if it calls other services for enrichment.
- A handler that receives events AND forwards to other services WITHOUT saving locally is a PROCESSOR.
- Command projects may PUBLISH events to ServiceBus (outbox pattern) but do not CONSUME/LISTEN to events.
- Look at the MAJORITY of handlers, not edge cases.
- For generic mode types, focus on STRUCTURAL patterns (directory layout, project references) over code patterns.
- When confidence is low, explain what additional files would help clarify the classification.
