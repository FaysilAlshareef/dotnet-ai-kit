# {{ Company }}.{{ Domain }}.Queries

SQL Server query microservice template.

## Structure

- **Domain/** - Entities with private setters, events for deserialization
- **Application/** - Event handlers and query handlers via MediatR
- **Infra/** - EF Core DbContext, repositories, Service Bus listeners
- **Grpc/** - gRPC host with interceptors

## Getting Started

1. Add entities in `Domain/Entities/`
2. Create event handlers in `Application/EventHandlers/`
3. Add query handlers in `Application/Queries/`
4. Create a Service Bus listener in `Infra/Listeners/`
5. Add proto definitions in `Grpc/Protos/`
6. Run `dotnet ef migrations add Initial`

## Key Patterns

- **CQRS Read Side**: Entities built from events received via Service Bus
- **Strict Sequence Checking**: Events applied in order, out-of-order abandoned
- **Private Setters**: All entity properties updated only through event application
