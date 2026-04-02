---
alwaysApply: true
description: "Architecture profile for Clean Architecture projects — hard constraints"
---

# Architecture Profile: Clean Architecture

## HARD CONSTRAINTS

### Layer Dependency Direction

- Dependencies MUST point inward: outer layers depend on inner layers, NEVER the reverse
- The dependency rule is: `WebApi -> Infrastructure -> Application -> Domain`
- NEVER add a project reference from an inner layer to an outer layer
- NEVER create circular references between layers

```
BAD:  Domain.csproj references Infrastructure.csproj
GOOD: Infrastructure.csproj references Application.csproj and Domain.csproj
```

### Domain Layer (Innermost)

- Domain layer MUST have ZERO external package dependencies — pure C# only
- NEVER reference EF Core, MediatR, FluentValidation, or any NuGet package in Domain
- NEVER add `using` statements for infrastructure namespaces in Domain classes
- MUST define repository interfaces in Domain — implementations go in Infrastructure
- MUST define `IUnitOfWork` in Domain or Application — NEVER in Infrastructure
- Domain entities MUST use private setters and factory methods to enforce invariants

```
BAD:  // In Domain/Entities/Order.cs
      using Microsoft.EntityFrameworkCore;
GOOD: // Domain has zero infrastructure imports
```

### Application Layer

- Application MUST reference only Domain — NEVER Infrastructure or WebApi
- MUST define interfaces for external services that Infrastructure implements
- NEVER create infrastructure objects directly (e.g., `new SqlConnection`, `new HttpClient`)
- MUST contain commands, queries, handlers, DTOs, and validators
- One use case per handler — Application layer orchestrates domain logic

```
BAD:  // In Application layer
      var conn = new SqlConnection(connectionString);
GOOD: // In Application layer
      await repository.FindAsync(id, ct);  // uses interface from Domain
```

### Infrastructure Layer

- Infrastructure MUST implement interfaces defined in Application and Domain
- NEVER define interfaces in Infrastructure that Application depends on
- MUST contain DbContext, repository implementations, and external service clients
- Each layer MUST have its own DI registration extension method

### WebApi Layer (Composition Root)

- WebApi is the composition root where DI wires all layers together
- NEVER put business logic in controllers or endpoints
- NEVER return domain entities from API endpoints — ALWAYS use DTOs
- WebApi MAY reference all layers for DI composition only

```
BAD:  app.MapGet("/orders/{id}", (AppDbContext db) => db.Orders.Find(id));
GOOD: app.MapGet("/orders/{id}", (ISender sender) => sender.Send(new GetOrder.Query(id)));
```

### No Inner-to-Outer References

- Domain MUST NOT reference Application, Infrastructure, or WebApi
- Application MUST NOT reference Infrastructure or WebApi
- Infrastructure MUST NOT reference WebApi
- ALWAYS verify project references follow the dependency rule after adding new references

## Testing Requirements

- MUST name test methods `{Method}_{Scenario}_{ExpectedResult}`
- MUST use Arrange-Act-Assert with clear visual separation
- NEVER call real services (HTTP, database servers) in unit tests
- NEVER share mutable state between tests
- Domain layer tests MUST have zero mocking — test pure domain logic directly
- Application layer tests MUST mock repository and service interfaces

## Data Access

- MUST register DbContext as Scoped — NEVER Singleton or Transient
- ALWAYS use `.AsNoTracking()` for read-only queries
- ALWAYS pass `CancellationToken` to all async EF Core calls
- MUST use pagination for all list queries — NEVER return unbounded results
- NEVER use lazy loading proxies
- NEVER call `SaveChanges()` inside loops — batch mutations, save once
- NEVER use `.ToList()` before `.Where()` — filter in the query, not in memory
