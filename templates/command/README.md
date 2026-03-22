# {{ Company }}.{{ Domain }}.Commands

Event-sourced command microservice template.

## Structure

- **Domain/** - Aggregates, events, and domain exceptions
- **Application/** - Command handlers via MediatR
- **Infra/** - EF Core DbContext, outbox pattern, Service Bus publisher
- **Grpc/** - gRPC host with interceptors

## Getting Started

1. Add your first aggregate in `Domain/Aggregates/`
2. Define domain events in `Domain/Events/`
3. Create command handlers in `Application/Commands/`
4. Add proto definitions in `Grpc/Protos/`
5. Run `dotnet ef migrations add Initial` to create the initial migration

## Key Patterns

- **Event Sourcing**: Aggregates emit events, stored atomically with outbox messages
- **Transactional Outbox**: Events published to Azure Service Bus after commit
- **gRPC**: All external communication via gRPC with FluentValidation
