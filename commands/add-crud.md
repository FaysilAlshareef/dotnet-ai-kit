---
description: "Generates full CRUD stack for an entity. Use when adding complete create/read/update/delete operations."
---

# Add CRUD

Generate full Create/Read/Update/Delete operations for an entity. Detects project architecture and generates the appropriate pattern: VSA feature folders, Clean Architecture layers, DDD aggregates, or microservice cross-service components.

## Usage

```
/dotnet-ai.add-crud $ARGUMENTS
```

**Examples:**
- `Order` -- Full CRUD with architecture auto-detection
- `Order --fields "Name:string,Total:decimal,CustomerId:Guid"` -- With explicit fields
- `Order --no-tests` -- Skip test generation
- `Order --dry-run` -- Show generated code without writing
- `Order --list` -- Show file list only
- `Order --verbose` -- Show detection and generation details

## Flags

| Flag | Description |
|------|-------------|
| `--fields "Name:Type,..."` | Entity fields (prompted interactively if omitted) |
| `--no-tests` | Skip test file generation |
| `--dry-run` | Display generated code without writing to disk |
| `--list` | List files that would be created/modified with descriptions, no code output |
| `--verbose` | Show architecture detection, pattern matching, generation details |

## Pre-Generation

1. **Detect architecture** -- scan project structure to determine mode:
   - **VSA**: `Features/` folder with handler-per-file pattern
   - **Clean Architecture**: separate `Domain/`, `Application/`, `Infrastructure/`, `API/` layers
   - **DDD**: `Domain/Aggregates/`, domain events, application services
   - **Microservice**: `Aggregate<T>` base (command), `IContainerDocument` (cosmos), gRPC clients (gateway)
   - If ambiguous: ask user to confirm detected architecture.
2. **Detect .NET version** -- read `<TargetFramework>` from `.csproj`.
3. **Learn conventions** -- scan existing entities, handlers, endpoints for:
   - Naming patterns, namespace format, DI registration style
   - Pagination approach (cursor-based vs offset)
   - Validation library (FluentValidation, DataAnnotations)
   - Mapping approach (records, extension methods, AutoMapper)
4. **Load config** -- read `.dotnet-ai-kit/config.yml`.
5. **Prompt for fields** -- if `--fields` not provided, interactively ask: field name, type, required?
6. **Check uniqueness** -- ensure no existing entity with same name.

## Load Specialist Agent

For generic mode: Read `agents/dotnet-architect.md`.
For microservice mode: Read the project's primary architect based on detected project type:
- command → Read `agents/command-architect.md`
- query-sql → Read `agents/query-architect.md`
- query-cosmos → Read `agents/cosmos-architect.md`
- processor → Read `agents/processor-architect.md`
- gateway → Read `agents/gateway-architect.md`
- controlpanel → Read `agents/controlpanel-architect.md`
- hybrid → Read both `agents/command-architect.md` and `agents/query-architect.md`

Also read `agents/ef-specialist.md` for data patterns and `agents/api-designer.md` for API patterns.
Load all skills listed in each loaded agent's Skills Loaded section.

## Skills to Read (architecture-dependent)

**VSA mode:**
- `skills/architecture/vertical-slice` -- feature folder structure
- `skills/cqrs/mediatr-handlers` -- handler patterns
- `skills/api/minimal-api` -- endpoint registration

**Clean Architecture mode:**
- `skills/architecture/clean-architecture` -- layer boundaries
- `skills/data/repository-patterns` -- repository interface + implementation
- `skills/cqrs/mediatr-handlers` -- command/query handlers

**DDD mode:**
- `skills/architecture/ddd-patterns` -- aggregate, domain events, services
- `skills/microservice/command/aggregate-design` -- aggregate structure

**Microservice mode:**
- `skills/microservice/command/aggregate-design` -- aggregate (command project)
- `skills/microservice/command/event-design` -- events (command project)
- `skills/microservice/query/query-entity` -- entity (query project)
- `skills/microservice/query/event-handler` -- handlers (query project)
- `skills/microservice/gateway/gateway-endpoint` -- endpoints (gateway project)

## Generation Flow -- VSA

| File | Description |
|------|-------------|
| `Features/{Name}s/Create{Name}.cs` | Command + handler + validator |
| `Features/{Name}s/Get{Name}s.cs` | Query + handler with pagination |
| `Features/{Name}s/Get{Name}ById.cs` | Query + handler |
| `Features/{Name}s/Update{Name}.cs` | Command + handler + validator |
| `Features/{Name}s/Delete{Name}.cs` | Command + handler |
| `Domain/Entities/{Name}.cs` | Entity class |
| `Infrastructure/Persistence/{Name}Configuration.cs` | EF Core config |
| `Features/{Name}s/{Name}Endpoints.cs` | Minimal API endpoint group |

## Generation Flow -- Clean Architecture

| File | Layer | Description |
|------|-------|-------------|
| `Domain/Entities/{Name}.cs` | Domain | Entity |
| `Application/{Name}s/Commands/Create{Name}Command.cs` | Application | Create |
| `Application/{Name}s/Commands/Update{Name}Command.cs` | Application | Update |
| `Application/{Name}s/Commands/Delete{Name}Command.cs` | Application | Delete |
| `Application/{Name}s/Queries/Get{Name}sQuery.cs` | Application | List |
| `Application/{Name}s/Queries/Get{Name}ByIdQuery.cs` | Application | Get |
| `Application/{Name}s/{Name}Output.cs` | Application | DTO |
| `Application/{Name}s/{Name}Validator.cs` | Application | Validation |
| `Infrastructure/Persistence/{Name}Configuration.cs` | Infra | EF config |
| `Infrastructure/Persistence/{Name}Repository.cs` | Infra | Repository |
| `API/Endpoints/{Name}Endpoints.cs` | API | Endpoints |

## Generation Flow -- Microservice (current repo only)

- **Command project**: Aggregate + Created/Updated/Deleted events + handlers + gRPC
- **Query project**: Entity + event handlers + query handlers + gRPC
- **Gateway project**: Controller + request/response models + gRPC registration

After generation, suggest running the same command in other repos.

## Common Patterns Included

All modes include these enterprise patterns automatically:
- **Pagination**: Cursor-based or offset (detected from existing code)
- **Filtering**: Query parameters mapped to `IQueryable` filters
- **Sorting**: `sortBy` and `sortDir` support
- **Validation**: FluentValidation rules for create/update commands
- **Concurrency**: RowVersion / concurrency token on entity
- **Audit fields**: `CreatedAt`/`UpdatedAt` if `IAuditable` pattern exists

## Post-Generation

1. **Register services** in DI container (`Program.cs` or extension method).
2. **Add EF migration** if EF Core is used: suggest `dotnet ef migrations add Add{Name}`.
3. **Run `dotnet build`** -- verify compilation.
4. **Run `dotnet test`** (unless `--no-tests`).
5. **Report:** `Created full CRUD for {Name}. {N} files generated.`
6. **Suggest:** `Test with: GET /api/v{N}/{name}s`

## Preview / Dry-Run Behavior

- `--dry-run`: Generate and display all code with file headers. No writes.
- `--list`: List files with descriptions. No code, no writes.
