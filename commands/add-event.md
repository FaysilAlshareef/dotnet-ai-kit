---
description: "Generates a domain event type for an aggregate. Use when adding a new event to an existing aggregate."
---

# Add Event

Add a new event to an existing aggregate in a command project. Creates the event class, data record, Apply method, command, and handler.

## Usage

```
/dotnet-ai.add-event $ARGUMENTS
```

**Examples:**
- `OrderShipped Order` -- Add OrderShipped event to Order aggregate
- `OrderShipped Order --fields "TrackingNumber:string,ShippedAt:DateTime"` -- With data fields
- `OrderShipped Order --dry-run` -- Show code without writing
- `OrderShipped Order --list` -- Show file list only
- `OrderShipped Order --verbose` -- Show detection details

## Flags

| Flag | Description |
|------|-------------|
| `--fields "Name:Type,..."` | Specify event data fields explicitly |
| `--dry-run` | Display generated code without writing to disk |
| `--list` | List files that would be created/modified with descriptions, no code output |
| `--verbose` | Show detection steps and pattern matching details |
| `--no-tests` | Skip test file generation |

## Pre-Generation

1. **Parse arguments** -- extract `{EventName}` (first arg) and `{AggregateName}` (second arg).
   - If only one arg provided: try to infer aggregate from event name prefix (e.g., `OrderShipped` implies `Order`).
   - If ambiguous: ask user for the aggregate name.
2. **Validate aggregate exists** -- scan `Domain/Aggregates/` for `{AggregateName}.cs`.
   - If not found: report "Aggregate '{AggregateName}' not found. Available: {list}" and stop.
3. **Detect project type** -- confirm this is a command project.
4. **Detect .NET version** -- read `<TargetFramework>` from `.csproj`.
5. **Learn patterns** -- scan existing events for this aggregate:
   - Event class structure, `EventType` naming convention, data record format.
6. **Check uniqueness** -- ensure no event with same name already exists.

## Load Specialist Agent

Read `agents/command-architect.md` for event design guidance. Load all skills listed in the agent's Skills Loaded section.

## Skills to Read

- `skills/microservice/command/event-design` -- event class structure, EventData record, naming

## Generation Flow

### Step 1: Generate Event Class
- Path: `Domain/Events/{EventName}.cs`
- Extends `Event<{EventName}Data>` following existing event pattern
- Set `EventType` matching naming convention from existing events

### Step 2: Generate Event Data Record
- Path: `Domain/Events/{EventName}Data.cs`
- Record with fields from `--fields` flag or sensible defaults based on event name
- Match existing data record patterns (property naming, types)

### Step 3: Modify Aggregate
- File: `Domain/Aggregates/{AggregateName}.cs`
- Add `Apply({EventName} @event)` method following existing Apply method pattern
- Add business method that creates the event and calls `ApplyChange`
- Preserve existing code structure and formatting

### Step 4: Generate Command + Handler
- Path: `Application/Commands/{Action}{Aggregate}Command.cs` -- command record
  - Infer `{Action}` from event name (e.g., `OrderShipped` -> `Ship`, `OrderCompleted` -> `Complete`)
- Path: `Application/Commands/{Action}{Aggregate}Handler.cs` -- handler implementation
  - Load aggregate, call business method, `CommitAsync`

### Step 5: Generate Infrastructure
- Path: `Infra/Database/Configurations/{EventName}Configuration.cs` -- EF Core event config
- Modify `ApplicationDbContext.cs` to register new configuration
- Add discriminator value for the new event type

### Step 6: Generate Test (unless `--no-tests`)
- Path: `Test/Commands/{Action}{Aggregate}HandlerTests.cs`
- Follow existing test patterns and naming conventions

### Step 7: Update Resources
- Add new keys to `Phrases.resx` and `Phrases.en.resx` if they exist

## Post-Generation

1. **Run `dotnet build`** -- verify compilation.
2. **Report generated files** -- list created and modified files.
3. **Suggest cross-service impact:**
   ```
   Event '{EventName}' added to {AggregateName} aggregate.

   Cross-service impact:
   - Query project needs: {EventName}Handler to update {AggregateName} entity
   - Processor may need: routing for {EventName} in listener
   - Gateway may need: new endpoint if this exposes new data

   To plan cross-service changes: /dotnet-ai.specify
   ```

## Preview / Dry-Run Behavior

- `--dry-run`: Show all generated code and the diff for modified files. No writes.
- `--list`: List files that would be created/modified. No code, no writes.
