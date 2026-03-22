---
description: "AI-assisted project type detection for .NET microservices"
category: "detection"
---
# Smart Detection Skill

You are analyzing a .NET project to determine its architectural type using behavioral analysis.

## Input

You will receive:
1. **Static analysis results** from the 3-layer detection engine (ProgramConfig, HandlerBehavior, ProjectStructure)
2. **Up to 5 representative handler/service files** from the project

## Static Analysis Results

```
Program.cs Configuration:
  serves_grpc: {serves_grpc}
  serves_rest: {serves_rest}
  has_service_bus: {has_service_bus}
  has_grpc_clients: {has_grpc_clients}
  has_reverse_proxy: {has_reverse_proxy}
  has_database: {has_database}

Handler Behavior:
  receives_commands: {receives_commands}
  receives_events: {receives_events}
  receives_http: {receives_http}
  manipulates_domain: {manipulates_domain}
  saves_to_database: {saves_to_database}
  calls_other_services: {calls_other_services}
  publishes_messages: {publishes_messages}

Project Structure:
  has_domain_layer: {has_domain_layer}
  has_features_dir: {has_features_dir}
  has_controllers_dir: {has_controllers_dir}
  has_listeners_dir: {has_listeners_dir}
  layer_count: {layer_count}
```

## Code Samples

Read up to 5 representative files from these directories (in priority order):
1. `**/Application/**/Handlers/**/*.cs` or `**/Features/**/*Handler.cs`
2. `**/Controllers/**/*.cs`
3. `**/Services/**/*Service.cs`
4. `**/Domain/**/Aggregate*.cs` or `**/Domain/**/Core/*.cs`
5. `Program.cs` or `Startup.cs`

## Classification Rules

Analyze the DATA FLOW through each handler file:

### What comes IN?
- **Commands**: handler takes a command object (e.g., `IRequestHandler<CreateOrderCommand>`)
- **Events**: handler takes an event object (e.g., `IRequestHandler<Event<OrderCreatedData>, bool>`)
- **HTTP requests**: controller actions with `[HttpGet]`, `[HttpPost]`, etc.

### What happens INSIDE?
- **Domain manipulation**: loads events by aggregate ID, rebuilds aggregate, calls domain methods, commits
- **Database save**: calls `SaveChangesAsync`, `AddAsync`, repository Add/Update
- **Service calls**: calls gRPC/HTTP clients to other services
- **Message publishing**: publishes to ServiceBus/queue/topic

### What goes OUT?
- **Nothing (void/Task)**: typical command handler
- **Bool acknowledgment**: typical event handler
- **Data (DTOs/responses)**: typical query handler or controller

## Type Determination

Based on the data flow:

| Type | IN | INSIDE | OUT |
|------|-----|--------|-----|
| **command** | Commands | Load aggregate -> domain method -> commit events | void/Task |
| **query-sql** | Events | Save to SQL database | bool (ack) |
| **query-cosmos** | Events | Save to Cosmos DB | bool (ack) |
| **processor** | Events | Call other gRPC services OR publish to message bus | bool (ack) |
| **gateway** | HTTP requests | Forward to gRPC services | HTTP responses |
| **controlpanel** | Browser requests | Blazor components render UI | HTML/Blazor |
| **hybrid** | Commands AND Events | Both domain manipulation AND DB save | Mixed |

## Decision Process

1. If the project has `.razor` files -> **controlpanel**
2. If controllers forward ALL requests to gRPC clients (no local DB) -> **gateway**
3. If handlers receive commands, manipulate domain aggregates, commit events, and do NOT consume events -> **command**
4. If handlers receive events and call other gRPC services or publish messages (no local DB save) -> **processor**
5. If handlers receive events and save to database:
   - With Cosmos DB -> **query-cosmos**
   - With SQL/EF -> **query-sql**
6. If both command and query patterns exist -> **hybrid**
7. If Features/ directory with handlers but no CQRS pattern -> **vsa**
8. If Domain + Application + Infrastructure layers -> **clean-arch**
9. If BoundedContexts/ directory -> **ddd**
10. If Modules/ directory -> **modular-monolith**
11. Otherwise -> **generic**

## Output Format

```
Classification: {type}
Confidence: {high|medium|low}
Evidence:
  1. {most important behavioral evidence}
  2. {second most important evidence}
  3. {third most important evidence}
Reasoning: {1-2 sentences explaining the data flow that led to this classification}
```

## Important Notes

- Focus on BEHAVIOR, not naming. A class called "OrderService" tells you nothing about data flow.
- A handler that receives events AND saves to DB is a QUERY handler, even if it calls other services for enrichment.
- A handler that receives events AND forwards to other services WITHOUT saving locally is a PROCESSOR.
- Command projects may PUBLISH events to ServiceBus (outbox pattern) but do not CONSUME/LISTEN to events.
- Look at the MAJORITY of handlers, not edge cases. A project with 20 event-save handlers and 1 gRPC call for cache rebuild is a query project.
