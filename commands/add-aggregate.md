---
description: "Add a new aggregate with initial event(s) to a command-side project"
---

# Add Aggregate

Create a new aggregate root in a command project with its initial event, command handler, and gRPC service stub.

## Usage

```
/dotnet-ai.add-aggregate $ARGUMENTS
```

**Examples:**
- `Order` -- Create Order aggregate with OrderCreated event
- `Order --events "Created,Updated,Completed"` -- With multiple initial events
- `Order --dry-run` -- Show generated code without writing files
- `Order --dry-run` -- Show file list only, no code output
- `Order --verbose` -- Show detailed detection and generation steps

## Flags

| Flag | Description |
|------|-------------|
| `--events "E1,E2,..."` | Generate multiple initial events (default: Created only) |
| `--dry-run` | Display generated code in terminal without writing to disk |
| `--dry-run` | List files that would be created/modified, no writes |
| `--verbose` | Show detection steps, pattern matching, and generation details |
| `--no-tests` | Skip test file generation |

## Pre-Generation

1. **Detect project type** -- scan for `Aggregate<T>` base class, `OutboxMessage`, or event store patterns.
   - If not a command project: report "This command requires a Command project. Detected: {actual}" and stop.
2. **Detect .NET version** -- read `<TargetFramework>` from `.csproj`. Adjust syntax:
   - .NET 8+: primary constructors, collection expressions allowed.
   - .NET 7: `required` modifier allowed, no primary constructors.
   - .NET 6: traditional constructors, `new List<T>()`.
3. **Learn naming conventions** -- scan existing aggregates in `Domain/Aggregates/` for:
   - Namespace format, base class usage, Apply method style, factory method pattern.
4. **Load config** -- read `.dotnet-ai-kit/config.yml` for `{Company}` name and project settings.
5. **Check name uniqueness** -- ensure no existing class named `{AggregateName}` in target directories.

## Load Specialist Agent

Read `agents/command-architect.md` for aggregate design guidance. Load all skills listed in the agent's Skills Loaded section.

## Skills to Read

Load these skills on demand based on what is being generated:

- `skills/microservice/command/aggregate-design` -- aggregate structure, factory methods, Apply pattern
- `skills/microservice/command/event-design` -- event class structure, EventData record pattern
- `skills/microservice/command/command-handler` -- handler structure, validation, CommitNewEventsAsync

## Generation Flow

Parse `$ARGUMENTS` to extract `{AggregateName}` (first positional arg, PascalCase singular).

### Step 1: Generate Aggregate Class
- Path: `Domain/Aggregates/{Name}.cs`
- Inherits `Aggregate<{Name}>`
- Factory method: `{Name}.Create(command)` that calls `ApplyChange`
- `Apply({Name}Created @event)` method with private setters
- Match existing aggregate patterns exactly

### Step 2: Generate Event(s)
For each event (default: `{Name}Created`, or from `--events` flag):
- Path: `Domain/Events/{Name}{Event}.cs` -- event class extending `Event<{Name}{Event}Data>`
- Path: `Domain/Events/{Name}{Event}Data.cs` -- data record with key fields
- Add `Apply({Name}{Event} @event)` method to aggregate

### Step 3: Generate Command Handler
- Path: `Application/Commands/Create{Name}Command.cs` -- command record
- Path: `Application/Commands/Create{Name}Handler.cs` -- `IRequestHandler` implementation
- Include validation, aggregate creation via factory, `CommitNewEventsAsync`

### Step 4: Generate Infrastructure
- Path: `Infra/Database/Configurations/{Name}EventConfiguration.cs` -- EF Core config
- Modify `ApplicationDbContext.OnModelCreating` to register configuration
- Update resource files (`Phrases.resx`, `Phrases.en.resx`) with new keys if they exist

### Step 5: Generate gRPC Service
- Path: `Grpc/Protos/{name}_commands.proto` -- proto definition (if not exists)
- Path: `Grpc/Services/{Name}CommandsService.cs` -- service inheriting generated base
- Path: `Grpc/Extensions/{Name}CommandExtensions.cs` -- mapping extensions
- Register in gRPC endpoint mapping and DI

### Step 6: Generate Tests (unless `--no-tests`)
- Path: `Test/Commands/Create{Name}HandlerTests.cs` -- unit test for handler
- Path: `Test/Fakers/{Name}Faker.cs` -- test data faker
- Match existing test framework (xUnit/NUnit/MSTest) and mocking library

## Post-Generation

1. **Run `dotnet build`** -- verify compilation. If build fails, show error and suggest fix.
2. **Report generated files** -- list all files created and modified.
3. **Suggest next steps:**
   ```
   Aggregate '{Name}' created with {Event} event(s).

   Next steps:
   1. Add more events: /dotnet-ai.add-event {Name}Updated Order
   2. Add query-side entity: /dotnet-ai.add-entity {Name} (in query project)
   3. Add gateway endpoint: /dotnet-ai.add-endpoint {Name} (in gateway project)
   ```

## Preview / Dry-Run Behavior

- `--dry-run`: Generate all code and display in terminal with file path headers. Write nothing.
- `--dry-run`: List files that would be created/modified with descriptions. No code output, no writes.
