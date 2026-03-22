# {{ Company }}.{{ ProjectName }}

Clean Architecture project template.

## Structure

- **Domain/** - Entities, value objects, interfaces (no dependencies)
- **Application/** - Commands, queries, behaviors (depends on Domain)
- **Infrastructure/** - EF Core, repositories (depends on Application + Domain)
- **API/** - Endpoints, middleware (depends on all layers)

## Layer Dependencies

Domain -> (none), Application -> Domain, Infrastructure -> Application + Domain, API -> All

## Getting Started

1. Define domain entities in `Domain/Entities/`
2. Create repository interfaces in `Domain/Interfaces/`
3. Add command/query handlers in `Application/`
4. Implement repositories in `Infrastructure/Data/Repositories/`
5. Register endpoints in `API/Endpoints/`
6. Access Scalar API docs at `/scalar/v1`

## Key Patterns

- **Dependency Inversion**: Domain defines interfaces, Infrastructure implements
- **CQRS**: Separate command and query handlers via MediatR
- **Repository Pattern**: Generic repository with unit of work
