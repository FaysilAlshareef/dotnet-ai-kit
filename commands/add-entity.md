---
description: "Generates a query-side entity with handler. Use when adding a new read model for projections."
---

# Add Entity

Create a new entity in a query project with event handlers, query handler, and repository. Auto-detects SQL vs Cosmos persistence.

## Usage

```
/dotnet-ai.add-entity $ARGUMENTS
```

**Examples:**
- `Order` -- Create Order entity (auto-detect SQL or Cosmos)
- `Order --cosmos` -- Force Cosmos mode
- `Order --from-event OrderCreated` -- Derive fields from event data
- `Order --dry-run` -- Show generated code without writing
- `Order --dry-run` -- Show file list only
- `Order --verbose` -- Show detection and generation details

## Flags

| Flag | Description |
|------|-------------|
| `--cosmos` | Force Cosmos mode (otherwise auto-detected) |
| `--from-event {EventName}` | Derive entity fields from an existing event data record |
| `--dry-run` | Display generated code without writing to disk |
| `--dry-run` | List files that would be created/modified |
| `--verbose` | Show detection steps and pattern matching details |
| `--no-tests` | Skip test file generation |

## Pre-Generation

1. **Detect project type** -- scan for query-side markers:
   - SQL: EF Core `DbContext`, entity configurations, `IRepository<T>`
   - Cosmos: `IContainerDocument`, `CosmosClient`, partition key patterns
   - If neither found: report "This command requires a Query project. Detected: {actual}" and stop.
2. **Auto-detect SQL vs Cosmos** -- check for `IContainerDocument` or `CosmosRepository` base classes.
   - If both present: ask user which mode. `--cosmos` flag overrides detection.
3. **Detect .NET version** -- read `<TargetFramework>` from `.csproj`.
4. **Learn naming conventions** -- scan existing entities for namespace, naming, folder structure.
5. **Load config** -- read `.dotnet-ai-kit/config.yml`.
6. **Check name uniqueness** -- ensure no existing entity with same name.

## Load Specialist Agent

Based on detected project type:
- query-sql → Read `agents/query-architect.md`
- query-cosmos → Read `agents/cosmos-architect.md`

Also read `agents/ef-specialist.md` for data access patterns. Load all skills listed in each loaded agent's Skills Loaded section.

## Skills to Read

Load on demand based on detected mode:

**SQL mode:**
- `skills/microservice/query/query-entity` -- entity structure, private setters, CTO pattern
- `skills/microservice/query/event-handler` -- event handler with sequence checking

**Cosmos mode:**
- `skills/microservice/cosmos/cosmos-entity` -- IContainerDocument, partition keys, discriminator
- `skills/microservice/cosmos/cosmos-repository` -- Cosmos repository pattern

**Both modes:**
- `skills/microservice/query/query-handler` -- query handler with pagination

## Generation Flow (SQL)

Parse `$ARGUMENTS` to extract `{EntityName}` (PascalCase singular).

### Step 1: Generate Entity
- Path: `Domain/Entities/{Name}.cs`
- Private setters on all properties
- Constructor from `Event<{Name}CreatedData>` (event constructor pattern)
- Private parameterized constructor for EF Core
- `Sequence` property for idempotency
- `RowVersion` property for concurrency

### Step 2: Generate Event Handlers
- Path: `Application/EventHandlers/{Name}CreatedHandler.cs`
- `IRequestHandler<Event<{Name}CreatedData>, bool>`
- Strict sequence check: `event.Sequence == entity.Sequence + 1`
- Return true if already processed (idempotent)
- `FindAsync` or `AddAsync` based on sequence

### Step 3: Generate Query Handler
- Path: `Application/Queries/Get{Name}sQuery.cs` -- query record with filter params
- Path: `Application/Queries/Get{Name}sHandler.cs` -- handler with pagination, filtering
- Path: `Application/Outputs/{Name}Output.cs` -- output DTO

### Step 4: Generate Infrastructure
- Path: `Infra/Database/Configurations/{Name}Configuration.cs` -- EF Core config
- Path: `Infra/Repositories/{Name}Repository.cs` -- repository implementation

### Step 5: Generate gRPC Service
- Path: `Grpc/Protos/{name}_queries.proto` -- proto definition
- Path: `Grpc/Services/{Name}QueriesService.cs` -- gRPC service

### Step 6: Generate Tests (unless `--no-tests`)
- Path: `Test/EventHandlers/{Name}CreatedHandlerTests.cs`
- Path: `Test/Fakers/{Name}Faker.cs` -- entity faker
- Path: `Test/Assertions/{Name}Assert.cs` -- assertion extensions

## Generation Flow (Cosmos)

### Step 1: Generate Entity
- Path: `Domain/Entities/{Name}.cs`
- Implements `IContainerDocument`
- `PartitionKeys` property (3-level composite)
- `Discriminator` property, `ETag` property
- Factory method from event

### Step 2: Generate Event Handler
- Path: `Application/EventHandlers/{Name}CreatedHandler.cs`

### Step 3: Generate Infrastructure
- Path: `Infra/Cosmos/{Name}Repository.cs` -- Cosmos repository
- Path: `Infra/Cosmos/Configurations/{Name}ContainerConfig.cs` -- container config

## Post-Generation

1. **Run `dotnet build`** -- verify compilation.
2. **Report generated files.**
3. **Suggest next steps:**
   ```
   Entity '{Name}' created with event handler.
   Next: Add gateway endpoint with /dotnet-ai.add-endpoint {Name}
   ```

## Preview / Dry-Run Behavior

- `--dry-run`: Show all generated code with file path headers. No writes.
- `--dry-run`: List files only. No code output, no writes.
