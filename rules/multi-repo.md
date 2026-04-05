---
description: "Multi-repo event contract and deployment conventions for microservice architectures"
alwaysApply: true
---

# Multi-Repo Conventions

## Event Contract Ownership

- The **Command** service MUST be the sole owner and publisher of domain events.
- Downstream services (Query, Processor, Gateway) MUST NOT publish events they do not own.
- Event contracts MUST be defined in the Command service and shared via NuGet or a contracts repo.
- Breaking changes to event contracts MUST be versioned — never remove or rename existing fields.

## Branch Naming

- Feature branches MUST use: `feat/{brief-NNN}-{short-name}`
- Tooling upgrade branches MUST use: `chore/brief-{NNN}-{name}`
- Hotfix branches MUST use: `fix/{brief-NNN}-{short-name}`
- Branch names MUST use lowercase kebab-case only. No spaces or underscores.

## Deploy Order

When deploying a cross-repo feature, MUST follow this order:

1. **Command** — aggregate and event contract changes first
2. **Processor** — event handler changes after Command is deployed
3. **Query** — read model changes after events are being published
4. **Gateway** — API route changes after query/command services are stable
5. **ControlPanel** — UI changes last, after all backend services are ready

MUST NOT deploy ControlPanel before Gateway. MUST NOT deploy Query before Command.

## No Circular Dependencies

- Services MUST NOT call each other synchronously in a cycle.
- Gateway MAY call Command and Query. Command MUST NOT call Gateway.
- Query services MUST NOT call Command services directly.
- Use events for cross-service communication — never shared databases or direct HTTP calls between services.

## Cross-Repo Feature Briefs

- When a feature spans repos, a brief MUST be projected to each affected secondary repo.
- Each repo's brief MUST declare its `role`, `required_changes`, `events_produces`, and `events_consumes`.
- `blocked_by` MUST list upstream repos that must complete first (following deploy order above).
- Secondary repo briefs MUST be kept in sync with the primary spec when the spec changes.
