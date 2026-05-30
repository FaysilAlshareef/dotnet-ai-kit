---
name: add-aggregate
description: "Generates an event-sourced aggregate root with its domain events and command handlers behind an ISender dispatch port. Use when adding a command-side aggregate to a CQRS or event-sourced project. Do NOT use for query-side read models (use add-entity) or a full CRUD stack (use add-crud)."
paths:
  - "**/Domain/**/*.cs"
  - "**/Aggregates/**/*.cs"
---
# Add Aggregate

Generate an aggregate root, its events, and license-light command dispatch.

## Conventions
- Aggregate state is private; mutate only through methods that raise events.
- No public setters on the aggregate (analyzer-backed: DAK0004).
- Dispatch commands through an `ISender` port — never a hard dependency on MediatR (commercial).
- Events are immutable records; the apply method is pure.

## License note
Default uses a hand-written `ISender`/source-generated mediator (MIT). MediatR is opt-in only.
