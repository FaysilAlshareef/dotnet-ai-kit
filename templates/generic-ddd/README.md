# {{ Company }}.{{ ProjectName }}

Domain-Driven Design project template.

## Structure

- **Domain/** - Aggregate roots, entities, value objects, domain events
- **Application/** - Commands, queries, domain event dispatch behavior
- **Infrastructure/** - EF Core with domain event interceptor
- **API/** - Minimal API endpoints

## Getting Started

1. Define aggregates in `Domain/Aggregates/`
2. Create domain events in `Domain/Events/`
3. Add command/query handlers in `Application/`
4. Implement infrastructure in `Infrastructure/Data/`
5. Register endpoints in `API/Endpoints/`

## Key Patterns

- **Aggregate Root**: Rich domain model with encapsulated state
- **Domain Events**: Raised during aggregate operations, dispatched after save
- **Strongly Typed IDs**: Type-safe identifiers for aggregates
- **Value Objects**: Immutable domain concepts with structural equality
