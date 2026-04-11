---
name: advisor
description: >
  Use when choosing between architecture patterns (VSA, Clean Architecture, DDD, Modular Monolith, Microservices) for a new project.
metadata:
  category: architecture
  agent: dotnet-architect
  when-to-use: "When evaluating architecture options or recommending an architectural approach"
---

# Architecture Advisor

## Decision Matrix

| Factor | VSA | Clean Arch | DDD | Modular Monolith | Microservices |
|--------|-----|-----------|-----|-------------------|---------------|
| Team size | 1-3 | 2-8 | 3-10 | 4-15 | 5+ per service |
| Domain complexity | Low | Medium | High | High | Very High |
| Expected scale | Small-Medium | Medium | Medium-Large | Large | Very Large |
| Deployment model | Single | Single | Single | Single | Independent |
| Data isolation | Shared DB | Shared DB | Bounded contexts | Schema per module | DB per service |
| Time to first feature | Fastest | Fast | Medium | Medium | Slowest |
| Long-term maintainability | Good | Very Good | Excellent | Excellent | Excellent (per service) |

## Questionnaire

### 1. Team Size
- **1-3 developers** → VSA or Clean Architecture
- **4-10 developers** → Clean Architecture, DDD, or Modular Monolith
- **10+ developers** → Modular Monolith or Microservices

### 2. Domain Complexity
- **Simple CRUD** (few business rules) → VSA
- **Moderate** (validation, workflows) → Clean Architecture
- **Complex** (invariants, aggregates, domain events) → DDD
- **Multiple bounded contexts** → Modular Monolith or Microservices

### 3. Scalability Needs
- **Single deployment** sufficient → VSA, Clean Arch, DDD, or Modular Monolith
- **Independent scaling** per feature → Microservices

### 4. Data Ownership
- **Single database** acceptable → VSA, Clean Architecture
- **Schema isolation** needed → Modular Monolith
- **Database per service** required → Microservices

### 5. Deployment Independence
- **Deploy everything together** → Any monolithic pattern
- **Deploy features independently** → Microservices

## Recommendations

### Vertical Slice Architecture (VSA)
**Choose when**: Small team, simple-to-moderate domain, rapid prototyping.
```
Features/
├── CreateOrder/
│   ├── CreateOrderCommand.cs
│   ├── CreateOrderHandler.cs
│   └── CreateOrderEndpoint.cs
└── GetOrders/
    ├── GetOrdersQuery.cs
    └── GetOrdersEndpoint.cs
```
**Pros**: Minimal boilerplate, feature-focused, easy to understand.
**Cons**: Harder to enforce boundaries as project grows.

### Clean Architecture
**Choose when**: Medium team, moderate complexity, clear layer boundaries needed.
```
Domain/         → Entities, value objects (zero dependencies)
Application/    → Commands, queries, handlers (depends on Domain)
Infrastructure/ → EF Core, external services (depends on Application)
Api/            → Controllers, endpoints (depends on Application)
```
**Pros**: Clear dependency direction, testable, well-documented pattern.
**Cons**: More boilerplate than VSA, can feel heavy for simple features.

### Domain-Driven Design (DDD)
**Choose when**: Complex domain with rich business rules, multiple aggregates.
```
Domain/
├── Aggregates/Order/
│   ├── Order.cs (aggregate root)
│   ├── OrderItem.cs (entity)
│   └── Money.cs (value object)
├── Events/
│   └── OrderCreated.cs
└── Interfaces/
    └── IOrderRepository.cs
```
**Pros**: Models complex business logic accurately, ubiquitous language.
**Cons**: Steeper learning curve, overkill for simple CRUD.

### Modular Monolith
**Choose when**: Large team, multiple feature areas, want independence without microservice overhead.
```
Modules/
├── Orders/
│   ├── OrdersModule.cs
│   ├── Domain/
│   ├── Application/
│   └── Infrastructure/ (own DbContext, own schema)
└── Customers/
    ├── CustomersModule.cs
    └── ...
```
**Pros**: Module independence, single deployment, easier than microservices.
**Cons**: Requires discipline to maintain module boundaries.

### Microservices (CQRS + Event Sourcing)
**Choose when**: Very large scale, independent deployment needed, multiple teams per service.
```
{Company}.{Domain}.Commands/    → Event-sourced aggregates
{Company}.{Domain}.Queries/     → Read-side projections
{Company}.{Domain}.Processor/   → Event routing
{Company}.Gateways.{Domain}/    → REST API gateway
```
**Pros**: Independent scaling/deployment, fault isolation, team autonomy.
**Cons**: Operational complexity, eventual consistency, network overhead.

## Migration Paths

```
VSA → Clean Architecture (add layers when complexity grows)
Clean Architecture → DDD (add aggregates, domain events when needed)
DDD → Modular Monolith (split into modules when team grows)
Modular Monolith → Microservices (extract modules to services when scale demands)
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Starting with microservices | Start monolithic, extract later |
| DDD for simple CRUD | Use VSA or Clean Architecture |
| Mixing architecture styles in one project | Pick one, be consistent |
| Choosing based on hype | Choose based on team size + domain complexity |

## Detect Existing Patterns

```bash
# Check for VSA (feature folders)
find . -type d -name "Features" | head -5

# Check for Clean Architecture (layer folders)
ls -d */Domain */Application */Infrastructure */Api 2>/dev/null

# Check for DDD (aggregates)
grep -r "AggregateRoot\|IAggregateRoot" --include="*.cs" | head -3

# Check for Modular Monolith (modules)
find . -type d -name "Modules" | head -3

# Check for Microservices
grep -r "Aggregate<\|Event<\|IEventData" --include="*.cs" | head -3
```

## Adding to Existing Project

1. **Detect** the current architecture before suggesting changes
2. **Never** change architecture mid-feature — complete the current work first
3. **Recommend** migration only when pain points are clearly identified
4. **Incremental** migration: one module/feature at a time
