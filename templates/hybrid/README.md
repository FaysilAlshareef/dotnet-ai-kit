# {{ Company }}.{{ Domain }}.{{ Side }}

Hybrid microservice template — combines command-side (write model) and query-side (read model) patterns in a single project.

## Structure

- **Domain/Aggregates/** - Aggregate roots and domain logic (write side)
- **Domain/Events/** - Domain event definitions
- **Domain/Entities/** - Read model entities (query side)
- **Application/Commands/** - Command handlers via MediatR
- **Application/Queries/** - Query handlers for read operations
- **Application/EventHandlers/** - Event handlers for read model sync
- **Infra/** - EF Core DbContext, outbox pattern, Service Bus publisher
- **Infra/Listeners/** - Service Bus listeners for event consumption
- **Grpc/** - gRPC host with interceptors

## Getting Started

1. Add aggregates in `Domain/Aggregates/`
2. Define domain events in `Domain/Events/`
3. Create command handlers in `Application/Commands/`
4. Add read model entities in `Domain/Entities/`
5. Create query handlers in `Application/Queries/`
6. Add event handlers in `Application/EventHandlers/`
7. Add proto definitions in `Grpc/Protos/`

## Key Patterns

- **CQRS**: Separate command and query paths within one project
- **Event Sourcing**: Aggregates emit events, stored with outbox messages
- **Read Model Sync**: Event handlers update denormalized read entities
- **gRPC**: All external communication via gRPC
