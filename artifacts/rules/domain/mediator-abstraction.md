---
name: mediator-abstraction
description: "Dispatches CQRS requests through a thin ISender/IMediator port so the concrete mediator is swappable (MediatR is now commercial). Use when adding command/query dispatch in C# files. Do NOT use for cross-service message-bus selection (use messaging-bus-selection)."
metadata:
  paths: "**/*.cs"
---
# Mediator Abstraction (domain)

MediatR and AutoMapper are now commercial. Default to license-safe dispatch.

## MUST
- Dispatch commands/queries through a thin `ISender`/`IMediator` **port** owned by the app, not a direct MediatR dependency.
- Default to a source-generated mediator (Mediator, MIT) or hand-written dispatch; MediatR is opt-in only, with a license note.
- Keep handlers free of the concrete mediator type.

## MUST NOT
- Reference `MediatR` types directly from domain/application code.
- Introduce a commercial package by default without an explicit opt-in profile.
