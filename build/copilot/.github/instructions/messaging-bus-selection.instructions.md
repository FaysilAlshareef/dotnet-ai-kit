---
applyTo: "**/*.cs"
---
# Messaging Bus Selection (domain)

MassTransit v9 is commercial; v8 is Apache-2.0 but loses support end-2026.

## MUST
- Abstract publish/consume behind an `IMessageBus` port; keep handlers transport-agnostic.
- Default to a license-safe option (Wolverine, MIT) or pin MassTransit v8 with a documented support horizon; MassTransit v9 is opt-in with a license note.
- Use the outbox pattern for reliable publishing.

## MUST NOT
- Hard-code a commercial bus client across the codebase.
- Mix transport concerns into domain/application logic.
