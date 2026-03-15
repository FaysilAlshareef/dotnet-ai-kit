# dotnet-ai-kit - Code Generation Command Flows

## Overview

6 code generation commands for rapidly adding components to existing projects (generic or microservice). Each command detects existing patterns, generates code following conventions, and runs build verification.

These commands are "quick add" shortcuts — they bypass the full SDD lifecycle (specify → plan → implement) for common, well-defined operations.

---

## Shared Behavior (All Commands)

### Pre-Generation Steps
1. **Detect project type** — scan for Aggregate<T>, IContainerDocument, controllers, etc.
2. **Detect .NET version** — read `<TargetFramework>` from .csproj
3. **Learn naming conventions** — scan existing class names, namespaces, folder structure
4. **Load config** — read `.dotnet-ai-kit/config.yml` for {Company} name
5. **Validate prerequisites** — correct project type for the command

### Post-Generation Steps
1. **Run `dotnet build`** — verify compilation
2. **Report generated files** — list all files created/modified
3. **Suggest next steps** — what to do after generation (e.g., "add event handlers in query side")

### Error Handling
- If wrong project type: "This command requires a {type} project. Detected: {actual}"
- If build fails: show error, suggest fix, do NOT auto-delete generated files
- If name conflicts: "A {type} named {name} already exists at {path}"

### .NET Version Validation
Generated code syntax must match the target .NET version:
- Primary constructors: only for .NET 8+ (C# 12)
- Collection expressions: only for .NET 8+ (C# 12)
- `required` modifier: only for .NET 7+ (C# 11)
- `field` keyword: only for .NET 10+ (C# 14)
- If target is .NET 6/7: use traditional constructors, `new List<T>()`, etc.

### Cross-Repo Awareness
Code gen commands operate on the **current repo only**. After generation, they suggest impacts on other repos but do NOT modify them.
- If other repos are cloned locally (in workspace `repos/` directory): suggestions include file paths
- If other repos are NOT available: suggestions are generic ("Add event handler in query service")
- Cross-repo changes require the full SDD lifecycle (`/dotnet-ai.specify` → `/dotnet-ai.implement`)

---

## 1. `/dotnet-ai.add-aggregate` — Add Aggregate (Command Side)

**Requires**: Command project (detected by Aggregate<T> base class or OutboxMessage)

### Input
```
/dotnet-ai.add-aggregate Order
```
Arguments:
- `{AggregateName}` — PascalCase singular (e.g., Order, Account, Competition)
- Optional: `--events "Created,Updated,Completed"` — initial events to generate

### Generated Files

| File | Layer | Description |
|------|-------|-------------|
| `Domain/Aggregates/{Name}.cs` | Domain | Aggregate class with factory method |
| `Domain/Events/{Name}Created.cs` | Domain | First event (always generated) |
| `Domain/Events/{Name}CreatedData.cs` | Domain | Event data record |
| `Application/Commands/Create{Name}Command.cs` | Application | Command record |
| `Application/Commands/Create{Name}Handler.cs` | Application | Command handler |
| `Application/Outputs/{Name}Output.cs` | Application | Output DTO |
| `Infra/Database/Configurations/{Name}EventConfiguration.cs` | Infra | EF Core config |
| `Grpc/Protos/{name}_commands.proto` | Grpc | Proto file (if not exists) |
| `Grpc/Services/{Name}CommandsService.cs` | Grpc | gRPC service |
| `Grpc/Extensions/{Name}CommandExtensions.cs` | Grpc | Mapping extensions |
| `Domain/Resources/Phrases.resx` | Domain | Updated with new keys |
| `Domain/Resources/Phrases.en.resx` | Domain | Updated with new keys |
| `Test/Commands/Create{Name}HandlerTests.cs` | Test | Unit test |
| `Test/Fakers/{Name}Faker.cs` | Test | Test data faker |

### Flow

```
1. Validate: project is Command type
2. Scan: existing aggregates in Domain/Aggregates/
3. Learn: naming pattern, namespace format, existing events
4. Generate: aggregate class
   - Inherits Aggregate<{Name}>
   - Factory method: {Name}.Create(command)
   - Apply({Name}Created @event) method
   - Private setters for all properties
5. Generate: {Name}Created event
   - Event<{Name}CreatedData>
   - {Name}CreatedData record with key fields
6. Generate: Create{Name}Handler
   - IRequestHandler<Create{Name}Command, {Name}Output>
   - Validation, aggregate creation, CommitNewEventsAsync
7. Generate: EF Core configuration
   - GenericEventConfiguration<{Name}Event, {Name}CreatedData>
   - Add to ApplicationDbContext OnModelCreating
8. Generate: gRPC service + proto
   - Proto: service {Name}Commands { rpc Create{Name}(...) returns (...); }
   - Service: inherits generated base, dispatches via MediatR
   - Mapping extensions: request → command, output → response
9. Generate: unit test
   - Test handler with faker data
   - Assert event created correctly
10. Register: add to DI, add to gRPC endpoint mapping
11. Build: run dotnet build
12. Report: files created, next steps
```

### Next Steps Suggestion
```
Aggregate 'Order' created with OrderCreated event.

Next steps:
1. Add more events: /dotnet-ai.add-event OrderUpdated --aggregate Order
2. Add query-side entity: /dotnet-ai.add-entity Order (in query project)
3. Add gateway endpoint: /dotnet-ai.add-endpoint Order (in gateway project)
```

---

## 2. `/dotnet-ai.add-entity` — Add Entity (Query Side)

**Requires**: Query project (SQL or Cosmos, auto-detected)

### Input
```
/dotnet-ai.add-entity Order
```
Arguments:
- `{EntityName}` — PascalCase singular
- Optional: `--from-event OrderCreated` — generates entity fields from event data
- Optional: `--cosmos` — force Cosmos mode (otherwise auto-detected)

### Generated Files (SQL Query)

| File | Layer | Description |
|------|-------|-------------|
| `Domain/Entities/{Name}.cs` | Domain | Entity with private setters |
| `Application/EventHandlers/{Name}CreatedHandler.cs` | Application | First event handler |
| `Application/Queries/Get{Name}sQuery.cs` | Application | Query record |
| `Application/Queries/Get{Name}sHandler.cs` | Application | Query handler |
| `Application/Outputs/{Name}Output.cs` | Application | Output DTO |
| `Infra/Database/Configurations/{Name}Configuration.cs` | Infra | EF Core config |
| `Infra/Repositories/{Name}Repository.cs` | Infra | Repository implementation |
| `Grpc/Protos/{name}_queries.proto` | Grpc | Proto file (if not exists) |
| `Grpc/Services/{Name}QueriesService.cs` | Grpc | gRPC service |
| `Test/EventHandlers/{Name}CreatedHandlerTests.cs` | Test | Event handler test |
| `Test/Fakers/{Name}Faker.cs` | Test | Entity faker |
| `Test/Assertions/{Name}Assert.cs` | Test | Assertion extensions |

### Generated Files (Cosmos Query)

| File | Layer | Description |
|------|-------|-------------|
| `Domain/Entities/{Name}.cs` | Domain | IContainerDocument entity |
| `Application/EventHandlers/{Name}CreatedHandler.cs` | Application | Event handler |
| `Infra/Cosmos/{Name}Repository.cs` | Infra | Cosmos repository |
| `Infra/Cosmos/Configurations/{Name}ContainerConfig.cs` | Infra | Container config |

### Flow (SQL)

```
1. Validate: project is Query type (SQL)
2. Scan: existing entities in Domain/Entities/
3. Learn: naming, namespace, existing event handlers
4. If --from-event: read event data record to derive entity fields
5. Generate: entity class
   - Private setters on all properties
   - Constructor from Event<{Name}CreatedData> (CTO pattern)
   - Private parameterized constructor for EF Core
   - Sequence property for idempotency
   - RowVersion property
6. Generate: event handler
   - IRequestHandler<Event<{Name}CreatedData>, bool>
   - Strict sequence check: event.Sequence == entity.Sequence + 1
   - Return true if already processed (idempotent)
   - FindAsync or AddAsync based on sequence
7. Generate: query handler
   - IRequestHandler<Get{Name}sQuery, Get{Name}sOutput>
   - Filtering, pagination, DTO projection
8. Generate: EF Core config + repository
9. Generate: gRPC service + proto
10. Generate: tests + faker + assertions
11. Build: run dotnet build
12. Report: files created, next steps
```

### Flow (Cosmos)

```
1-3. Same as SQL
4. Generate: entity class
   - Implements IContainerDocument
   - PartitionKeys property (3-level composite)
   - Discriminator property
   - ETag property
   - Factory method from event
5-12. Similar to SQL but with Cosmos-specific patterns
```

---

## 3. `/dotnet-ai.add-event` — Add Event to Existing Aggregate

**Requires**: Command project with existing aggregate

### Input
```
/dotnet-ai.add-event OrderUpdated --aggregate Order
```
Arguments:
- `{EventName}` — PascalCase (e.g., OrderUpdated, OrderCompleted)
- `--aggregate {Name}` — required, target aggregate
- Optional: `--data "Status string, UpdatedAt DateTime"` — event data fields

### Generated Files

| File | Layer | Description |
|------|-------|-------------|
| `Domain/Events/{EventName}.cs` | Domain | Event class |
| `Domain/Events/{EventName}Data.cs` | Domain | Event data record |
| `Domain/Aggregates/{Aggregate}.cs` | Domain | Modified: + Apply method |
| `Application/Commands/{Action}{Aggregate}Command.cs` | Application | Command record |
| `Application/Commands/{Action}{Aggregate}Handler.cs` | Application | Handler |
| `Infra/Database/Configurations/{EventName}Configuration.cs` | Infra | EF config |
| `Infra/Database/ApplicationDbContext.cs` | Infra | Modified: + config registration |
| `Test/Commands/{Action}{Aggregate}HandlerTests.cs` | Test | Test |

### Flow

```
1. Validate: aggregate exists in Domain/Aggregates/
2. Scan: existing events for this aggregate (learn EventType naming)
3. Generate: event + data record
4. Modify: aggregate class
   - Add Apply({EventName} @event) method
   - Add business method that calls ApplyChange
5. Generate: command + handler
6. Register: EF config, add discriminator value
7. Generate: test
8. Build
9. Report + suggest: "Add handler in query project for {EventName}"
```

### Cross-Repo Awareness
After generating, the command suggests:
```
Event 'OrderUpdated' added to Order aggregate.

Cross-service impact:
- Query project needs: {EventName}Handler to update Order entity
- Processor may need: routing for {EventName} in listener
- Gateway may need: new endpoint if this exposes new data

Run these in the respective projects:
  Query: (manually add event handler following existing patterns)
  Or use full lifecycle: /dotnet-ai.specify to plan cross-service changes
```

---

## 4. `/dotnet-ai.add-endpoint` — Add Gateway Endpoint

**Requires**: Gateway project (detected by REST controllers + AddGrpcClient)

### Input
```
/dotnet-ai.add-endpoint Order
```
Arguments:
- `{ResourceName}` — PascalCase singular (e.g., Order)
- Optional: `--operations "list,get,create,update,delete"` — which CRUD operations
- Optional: `--version v1` — API version (default: detected from existing)

### Generated Files

| File | Layer | Description |
|------|-------|-------------|
| `Controllers/V{N}/{Name}Controller.cs` | API | REST controller |
| `Models/Requests/Create{Name}Request.cs` | Models | Request DTOs |
| `Models/Responses/{Name}Response.cs` | Models | Response DTOs |
| `Extensions/{Name}MappingExtensions.cs` | Extensions | Request→gRPC, gRPC→Response |
| `Infra/GrpcRegistration.cs` | Infra | Modified: + new client |

### Flow

```
1. Validate: project is Gateway type
2. Scan: existing controllers for patterns (auth policies, response format, versioning)
3. Learn: API version scheme, authorization patterns, Paginated<T> usage
4. Generate: controller
   - [ApiController], [Route("api/v{N}/[controller]")]
   - [Authorize(Policy = "...")] from existing patterns
   - Inject gRPC client
   - CRUD methods based on --operations
   - Return ActionResult<T> or Paginated<T>
5. Generate: request/response models
6. Generate: mapping extensions (request → gRPC message, gRPC response → DTO)
7. Register: gRPC client in ServicesUrlsOptions + AddGrpcClient
8. Build
9. Report
```

---

## 5. `/dotnet-ai.add-page` — Add Control Panel Page

**Requires**: ControlPanel project (detected by Blazor + ResponseResult<T>)

### Input
```
/dotnet-ai.add-page Orders --module OrderManagement
```
Arguments:
- `{PageName}` — PascalCase plural (e.g., Orders, Competitions)
- `--module {ModuleName}` — module/section for the page
- Optional: `--operations "list,create,edit,delete"` — page capabilities

### Generated Files

| File | Layer | Description |
|------|-------|-------------|
| `API/{Module}/{Module}Gateway.cs` | API | Gateway facade (or modify existing) |
| `API/{Module}/{Module}Management.cs` | API | Management sub-class |
| `Presentation/{Module}/{PageName}Page.razor` | UI | Blazor page |
| `Presentation/{Module}/{PageName}Page.razor.cs` | UI | Code-behind |
| `Presentation/{Module}/{PageName}FilterModel.cs` | UI | Filter model |
| `Presentation/{Module}/Dialogs/Create{Singular}Dialog.razor` | UI | Create dialog |

### Flow

```
1. Validate: project is ControlPanel type
2. Scan: existing pages for patterns (MudBlazor version, dialog patterns)
3. Learn: gateway facade pattern, filter model pattern, menu registration
4. Generate: gateway facade
   - If module gateway exists: add new Management class
   - If new module: create gateway class with Management
   - Methods: GetAllAsync, GetByIdAsync, CreateAsync, UpdateAsync, DeleteAsync
5. Generate: filter model
   - Extends QueryStringBindable
   - Properties with UpdateQueryStringIfChanged
   - ToQuery() mapping
6. Generate: Blazor page
   - MudDataGrid with ServerData callback
   - Filter panel with MudExpansionPanels
   - BindToNavigationManager for URL state
   - Gateway call → Switch result pattern
   - Dialog triggers for create/edit
7. Generate: create/edit dialog
   - MudDialog with form
   - Validation
   - Gateway call on submit
8. Register: menu item, service registration
9. Build
10. Report
```

### No Tests Generated
Control panel modules do not require unit or integration tests — testing is done at the gateway level.

---

## Validation Rules (All Commands)

| Rule | Check |
|------|-------|
| Name uniqueness | No existing class with same name in target directory |
| Valid C# identifier | Name must be valid PascalCase identifier |
| Project type match | Command requires Command project, Entity requires Query, etc. |
| .NET version | Generated code uses version-appropriate syntax |
| Namespace consistency | Generated namespace matches existing pattern |
| Resource files | Updated Phrases.resx and Phrases.en.resx if they exist |

---

## Integration with SDD Lifecycle

Code generation commands are shortcuts that bypass the full lifecycle. They are best used for:
- Adding a single aggregate/entity/event to an existing well-understood project
- Quick prototyping before full specification
- Extending existing features with new components

For cross-service features (new aggregate + entity + endpoint + page), use the full SDD lifecycle instead:
```
/dotnet-ai.specify → /dotnet-ai.plan → /dotnet-ai.implement
```

The full lifecycle ensures consistency across services, generates event catalogues, and validates cross-service contracts.

---

## 6. `/dotnet-ai.add-crud` — Full CRUD for Entity (Generic + Microservice)

**Works in**: Any project type (generic or microservice). The most commonly needed code gen command.

### Input
```
/dotnet-ai.add-crud Order
/dotnet-ai.add-crud Order --fields "Name:string,Total:decimal,CustomerId:Guid"
/dotnet-ai.add-crud Order --no-tests
/dotnet-ai.add-crud Order --preview
```
Arguments:
- `{EntityName}` — PascalCase singular
- Optional: `--fields "Name:Type,..."` — entity fields (prompted if omitted)
- Optional: `--no-tests` — skip test generation
- Optional: `--preview` — show code without writing
- Optional: `--dry-run` — show file list only

### Generated Files — Generic Mode (VSA)

| File | Description |
|------|-------------|
| `Features/Orders/CreateOrder.cs` | Command + handler + validator |
| `Features/Orders/GetOrders.cs` | Query + handler with pagination |
| `Features/Orders/GetOrderById.cs` | Query + handler |
| `Features/Orders/UpdateOrder.cs` | Command + handler + validator |
| `Features/Orders/DeleteOrder.cs` | Command + handler |
| `Domain/Entities/Order.cs` | Entity class |
| `Infrastructure/Persistence/OrderConfiguration.cs` | EF Core config |
| `Features/Orders/OrderEndpoints.cs` | Minimal API endpoint group |
| `Tests/Features/Orders/CreateOrderTests.cs` | Unit tests |
| EF Migration | Auto-generated via `dotnet ef` |

### Generated Files — Generic Mode (Clean Architecture)

| File | Layer | Description |
|------|-------|-------------|
| `Domain/Entities/Order.cs` | Domain | Entity |
| `Application/Orders/Commands/CreateOrderCommand.cs` | Application | Create command + handler |
| `Application/Orders/Commands/UpdateOrderCommand.cs` | Application | Update command + handler |
| `Application/Orders/Commands/DeleteOrderCommand.cs` | Application | Delete command + handler |
| `Application/Orders/Queries/GetOrdersQuery.cs` | Application | List query + handler |
| `Application/Orders/Queries/GetOrderByIdQuery.cs` | Application | Get by ID query + handler |
| `Application/Orders/OrderOutput.cs` | Application | Output DTO |
| `Application/Orders/OrderValidator.cs` | Application | FluentValidation |
| `Infrastructure/Persistence/OrderConfiguration.cs` | Infrastructure | EF Core config |
| `Infrastructure/Persistence/OrderRepository.cs` | Infrastructure | Repository |
| `API/Endpoints/OrderEndpoints.cs` | API | Minimal API / Controller |
| `Tests/Orders/CreateOrderTests.cs` | Tests | Unit tests |

### Generated Files — Microservice Mode (Current Repo Only)

Depends on detected project type:
- **Command project**: Aggregate + Created/Updated/Deleted events + handlers + proto + tests
- **Query project**: Entity + event handlers + query handlers + proto
- **Gateway project**: Controller + models + gRPC client registration

After generation, suggests: "Run `/dotnet-ai.add-crud Order` in the {other} repo to generate the matching side."

### Flow

```
1. Detect project type and architecture
2. If --fields not provided: prompt for entity fields (Name, Type, Required?)
3. Detect existing patterns (DI style, naming, folder structure)
4. Generate all files per architecture pattern
5. Register services in DI container (Program.cs or extension method)
6. Add EF migration if EF Core is used
7. Run dotnet build
8. Run tests (unless --no-tests)
9. Report: "Created full CRUD for Order. {N} files generated."
10. Suggest: "Test with: GET /api/v1/orders"
```

### Common Patterns Included

CRUD generation includes these common enterprise patterns automatically:
- **Pagination**: Cursor-based or offset (detected from existing queries)
- **Filtering**: Query parameters mapped to `IQueryable` filters
- **Sorting**: `?sortBy=name&sortDir=asc` support
- **Validation**: FluentValidation rules for create/update
- **Mapping**: Entity ↔ DTO mapping (records or extension methods)
- **Concurrency**: Row version / concurrency token on entity
- **Audit**: CreatedAt/UpdatedAt fields if IAuditable pattern exists
