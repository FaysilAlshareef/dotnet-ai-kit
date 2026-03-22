---
alwaysApply: true
description: Enforces architectural boundaries appropriate to the detected architecture pattern.
---

# Architecture Rules

DETECT the architecture from the existing project structure before applying rules.
If the project uses a different pattern than expected, follow what exists.

## Microservice Mode

### Layer Dependencies
- Domain layer has ZERO external dependencies
- Application depends only on Domain
- Infrastructure implements Domain/Application interfaces
- Grpc references Application and Infrastructure

### Patterns
- MediatR for CQRS dispatch (`IRequest`/`IRequestHandler`)
- `Event<T>` for all domain events
- Outbox pattern for reliable publishing (command side)
- Sequence-based idempotency (query side)
- UnitOfWork for transaction management
- Options pattern for all configuration

### Communication
- gRPC for inter-service communication
- Azure Service Bus for event messaging

### Data
- Resource files for all user-facing strings
- Row version + concurrency tokens for SQL Server entities (sequence in most entities)
- Event catalogue maintained per service
- Event versioning with versioned handlers for schema evolution

## Generic Mode -- Clean Architecture

- Dependency flow: Domain -> Application -> Infrastructure -> API/Web
- No circular dependencies between layers
- Domain has no dependencies on infrastructure concerns

## Generic Mode -- Vertical Slice Architecture

- One feature folder per operation
- Each slice is independent and self-contained
- Shared infrastructure via DI registration, not direct reference

## Generic Mode -- DDD

- Bounded contexts with clear boundaries
- Aggregates enforce invariants internally
- Domain events for cross-aggregate communication

## Detection Instructions

1. Scan the solution structure for layer folders (Domain, Application, Infrastructure, etc.)
2. Check project references in .csproj files for dependency direction
3. Look for existing patterns: MediatR, CQRS, Event Sourcing, Repository pattern
4. Identify if the project is microservice-based (gRPC, Service Bus) or monolithic
5. Apply the rules matching the detected architecture -- never impose a different one
