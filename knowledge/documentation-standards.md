# Documentation Standards

Documentation templates, XML doc comments, README structure, Architecture Decision Records (ADR), and API documentation standards for .NET projects.

---

## XML Doc Comments

### When to Document

- All public types and members
- All internal types used across projects
- Complex private methods (business logic, algorithms)
- Extension methods
- Factory methods and static creators

### Comment Patterns

```csharp
/// <summary>
/// Commits domain events and outbox messages in a single database transaction.
/// Guarantees at-least-once delivery via the outbox pattern.
/// </summary>
/// <typeparam name="T">The event data type implementing <see cref="IEventData"/>.</typeparam>
public interface ICommitEventService<T> where T : IEventData
{
    /// <summary>
    /// Saves events to the event store and creates corresponding outbox messages
    /// within a single transaction.
    /// </summary>
    /// <param name="aggregateId">The aggregate root identifier.</param>
    /// <param name="events">Uncommitted events from the aggregate.</param>
    /// <param name="ct">Cancellation token.</param>
    /// <exception cref="DbUpdateException">
    /// Thrown when a concurrency conflict occurs (duplicate sequence number).
    /// </exception>
    Task CommitAsync(Guid aggregateId, IReadOnlyList<Event<T>> events, CancellationToken ct);
}

/// <summary>
/// Creates a new order aggregate and produces an <see cref="EventTypes.OrderCreated"/> event.
/// </summary>
/// <param name="customerName">
/// The customer's full name. Must not be empty.
/// </param>
/// <param name="total">
/// The order total in the default currency. Must be greater than zero.
/// </param>
/// <returns>A new <see cref="Order"/> instance with one uncommitted event.</returns>
/// <example>
/// <code>
/// var order = Order.Create("John Doe", 99.99m);
/// await commitService.CommitAsync(order.Id, order.UncommittedEvents, ct);
/// </code>
/// </example>
public static Order Create(string customerName, decimal total)
```

### Tags Reference

| Tag            | Usage                                          |
|----------------|------------------------------------------------|
| `<summary>`    | Brief description of type/member               |
| `<param>`      | Parameter description                          |
| `<returns>`    | Return value description                       |
| `<exception>`  | Exceptions that may be thrown                  |
| `<remarks>`    | Additional details, usage notes                |
| `<example>`    | Code example                                   |
| `<see cref="">` | Cross-reference to another type/member        |
| `<typeparam>`  | Generic type parameter description             |
| `<inheritdoc>` | Inherit documentation from base/interface      |
| `<value>`      | Property value description                     |

### Project Configuration

Enable XML doc generation for all projects:

```xml
<!-- Directory.Build.props -->
<PropertyGroup>
    <GenerateDocumentationFile>true</GenerateDocumentationFile>
    <NoWarn>$(NoWarn);CS1591</NoWarn> <!-- Suppress missing XML comment warnings for private members -->
</PropertyGroup>
```

---

## README Structure

### Service README Template

```markdown
# {Company}.{Domain}.{Side}

Brief description of what this service does.

## Architecture

- **Type**: Command | Query | Processor | Gateway | ControlPanel
- **Pattern**: Event Sourcing + CQRS
- **.NET Version**: 10.0
- **Database**: SQL Server | Cosmos DB

## Getting Started

### Prerequisites

- .NET 10 SDK
- Docker Desktop
- Azure CLI (for Service Bus emulator)

### Running Locally

```bash
# Start dependencies
docker compose up -d

# Run the service
dotnet run --project src/{Company}.{Domain}.{Side}.Api
```

### Running with Aspire

```bash
dotnet run --project src/{Company}.{Domain}.AppHost
```

## Project Structure

```
src/
├── {Company}.{Domain}.{Side}.Api/           # Host, DI, endpoints
├── {Company}.{Domain}.{Side}.Application/   # Handlers, validators
├── {Company}.{Domain}.{Side}.Domain/        # Entities, events, aggregates
└── {Company}.{Domain}.{Side}.Infrastructure/# DB, Service Bus, gRPC
```

## Events

See [Event Catalogue](docs/event-catalogue.md) for all events produced/consumed.

## API Documentation

- **Scalar UI**: https://localhost:5001/scalar
- **OpenAPI spec**: https://localhost:5001/openapi/v1.json

## Configuration

| Setting                         | Default      | Description                    |
|---------------------------------|-------------|--------------------------------|
| ConnectionStrings:Database      | (required)   | SQL Server connection string   |
| ServiceBus:ConnectionString     | (required)   | Azure Service Bus connection   |
| ServiceBus:TopicName            | (required)   | Topic for event publishing     |

## Testing

```bash
# Unit tests
dotnet test tests/{Company}.{Domain}.UnitTests

# Integration tests (requires Docker)
dotnet test tests/{Company}.{Domain}.IntegrationTests
```

## Deployment

See [Deployment Guide](docs/deployment.md) for CI/CD and Kubernetes details.
```

---

## Architecture Decision Records (ADR)

### ADR Format

Store ADRs in `docs/adr/` with sequential numbering.

```markdown
# ADR-{NNN}: {Title}

## Status

Proposed | Accepted | Deprecated | Superseded by [ADR-XXX](XXXX.md)

## Date

YYYY-MM-DD

## Context

Describe the forces at play, including technological, political, social, and project-specific concerns. What is the issue that requires a decision?

## Decision

Describe the decision and its rationale. Be specific about what was chosen and what alternatives were considered.

## Alternatives Considered

### Option A: {Name}
- **Pros**: ...
- **Cons**: ...

### Option B: {Name}
- **Pros**: ...
- **Cons**: ...

## Consequences

What becomes easier or more difficult to do because of this decision? Include both positive and negative consequences.

### Positive
- ...

### Negative
- ...

## References

- Link to relevant documentation, discussions, or specifications
```

### Example ADR

```markdown
# ADR-001: Use Azure Service Bus for Inter-Service Messaging

## Status
Accepted

## Date
2026-01-15

## Context
Our microservice architecture requires reliable, ordered message delivery between services. The command side produces domain events that must be consumed by query, processor, and analytics services. We need:
- At-least-once delivery guarantee
- Ordered processing per aggregate
- Dead letter queue support
- Azure-native integration

## Decision
Use Azure Service Bus with topics and subscriptions. Session-based processing ensures per-aggregate ordering via SessionId = AggregateId.

## Alternatives Considered

### Option A: RabbitMQ
- **Pros**: Open source, no cloud lock-in, mature ecosystem
- **Cons**: No native session ordering, requires self-hosted infrastructure

### Option B: Azure Event Hubs
- **Pros**: Higher throughput, built for event streaming
- **Cons**: No built-in dead lettering, consumer group model less suited to CQRS

## Consequences

### Positive
- Native Azure integration with Managed Identity
- Session-based ordering eliminates need for application-level ordering
- Built-in dead letter queue for failed messages

### Negative
- Azure-specific (cloud lock-in)
- Cost per message (can be significant at high volume)

## References
- [Azure Service Bus documentation](https://learn.microsoft.com/en-us/azure/service-bus-messaging/)
- `knowledge/service-bus-patterns.md`
```

---

## API Documentation

### OpenAPI Annotations

Use endpoint metadata and XML comments for comprehensive API documentation:

```csharp
app.MapPost("/api/v1/orders", CreateOrder)
    .WithSummary("Create a new order")
    .WithDescription("Creates a new order and produces an OrderCreated event. " +
                     "Returns the order ID and initial sequence number.")
    .Produces<OrderResponse>(StatusCodes.Status201Created)
    .ProducesValidationProblem()
    .ProducesProblem(StatusCodes.Status500InternalServerError)
    .WithTags("Orders");
```

### Response Type Documentation

```csharp
/// <summary>
/// Response returned when an order is created or retrieved.
/// </summary>
/// <param name="Id">The unique order identifier.</param>
/// <param name="CustomerName">The customer's full name.</param>
/// <param name="Total">The order total in the default currency.</param>
/// <param name="Sequence">
/// The current event sequence number. Used for optimistic concurrency.
/// </param>
public sealed record OrderResponse(
    Guid Id,
    string CustomerName,
    decimal Total,
    int Sequence);
```

---

## Changelog Format

### CHANGELOG.md

Follow [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Currency field on OrderCreated event (v2)

### Changed
- Updated Service Bus SDK to 7.18.0

### Fixed
- Dead letter reprocessing now correctly tracks resubmit count

## [1.0.0] - 2026-01-15

### Added
- Initial release with CQRS event sourcing
- Order aggregate with Create, Update, Cancel operations
- Service Bus integration with session-based processing
- gRPC service with command and query endpoints
```

---

## Code Comment Guidelines

### When to Comment

- **Do**: Explain WHY, not WHAT
- **Do**: Document business rules and invariants
- **Do**: Note non-obvious side effects
- **Do**: Reference external documentation (ADRs, specs)
- **Don't**: Restate what the code already says
- **Don't**: Leave TODO comments without a tracking issue

### Good vs Bad Comments

```csharp
// BAD: Restates code
// Check if order is null
if (order is null) return NotFound();

// GOOD: Explains business rule
// Orders in "Processing" state cannot be cancelled — they must complete
// or be rejected by the fulfillment service. See ADR-007.
if (order.Status == OrderStatus.Processing)
    throw new DomainException("Cannot cancel order in processing state");

// GOOD: Documents non-obvious behavior
// Sequence check returns true (complete message) for already-processed events
// to prevent infinite retry loops. This is idempotent by design.
if (@event.Sequence <= order.Sequence)
    return true;
```

---

## Documentation File Structure

```
docs/
├── adr/
│   ├── 001-service-bus-messaging.md
│   ├── 002-cosmos-partition-strategy.md
│   └── template.md
├── event-catalogue.md
├── deployment.md
├── runbook.md              # Operational procedures
└── onboarding.md           # New developer guide
```

---

## Related Documents

- `knowledge/deployment-patterns.md` — CI/CD documentation
- `knowledge/event-versioning.md` — Event catalogue maintenance
- `knowledge/testing-patterns.md` — Test documentation
