---
name: mediator-migration
description: "Migrates off commercial MediatR to source-generated Mediator (MIT) or Wolverine behind an ISender port, or pins MediatR < 13. Use when removing or replacing the MediatR dependency, reacting to the MediatR 13+ commercial license, or future-proofing dispatch. Do NOT use for writing new handler bodies or pipeline behaviors (use mediatr-handlers / pipeline-behaviors)."
metadata:
  category: "cqrs"
  agent: "command-architect"
---
# Mediator Migration (Off Commercial MediatR)

MediatR became commercial at **v13** (paid license for production use). Treat MediatR as a *replaceable detail*: dispatch behind your own `ISender` port so the bus swaps without touching handlers or call sites.

## Decision Order

| Option | License | When |
|--------|---------|------|
| **source-generated Mediator** (`Martinothamar/Mediator`) | MIT | Default — drop-in `ISender`/`IRequest`/`IRequestHandler` shape, zero reflection |
| **Wolverine** (mediator mode) | MIT | You also want a real bus, outbox/inbox, or transactional messaging |
| **Pin `MediatR < 13`** | Apache-2.0 | Short-term hold; large legacy surface you cannot migrate yet |
| MediatR `>= 13` | Commercial (opt-in) | Only with a purchased license — note it in your `Directory.Packages.props` |

## Define the Port (decouple from any library)

```csharp
namespace {Company}.{Domain}.Application.Abstractions;

// Your own marker types — handlers depend on these, never on a vendor namespace.
public interface IRequest<out TResponse>;

public interface IRequestHandler<in TRequest, TResponse>
    where TRequest : IRequest<TResponse>
{
    Task<TResponse> Handle(TRequest request, CancellationToken ct);
}

// The single dispatch seam used by endpoints/controllers.
public interface ISender
{
    Task<TResponse> Send<TResponse>(IRequest<TResponse> request, CancellationToken ct = default);
}
```

Endpoints inject **`ISender`** only. Swapping MediatR for source-gen Mediator or Wolverine becomes a registration change, not a sweep across the codebase.

## Migrate to source-generated Mediator (MIT)

```bash
dotnet remove package MediatR
dotnet add package Mediator.SourceGenerator
dotnet add package Mediator.Abstractions
```

```csharp
// Program.cs — source generator wires handlers at compile time (no assembly scan).
builder.Services.AddMediator(o => o.ServiceLifetime = ServiceLifetime.Scoped);
```

The request/handler shape matches MediatR closely, so handler bodies usually compile unchanged once `using MediatR;` is replaced with your abstractions (or `using Mediator;`).

## Pin MediatR < 13 (interim)

```xml
<!-- Directory.Packages.props — explicit ceiling keeps you on the Apache-2.0 line. -->
<PackageVersion Include="MediatR" Version="[12.4.1,13.0.0)" />
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| `using MediatR;` scattered across handlers | Depend on your `Application.Abstractions` port |
| Injecting concrete `IMediator` into endpoints | Inject `ISender` only |
| Silently upgrading to MediatR 13+ | 13+ needs a paid license — make it an explicit, documented choice |
| Re-implementing pipeline behaviors during the swap | Migrate behavior contracts 1:1, then change registration |

## Migration Steps

1. Introduce the `Application.Abstractions` port (`IRequest`, `IRequestHandler`, `ISender`).
2. Repoint endpoints/controllers to inject `ISender`.
3. Pick a replacement (source-gen Mediator default; Wolverine if you want a bus).
4. Replace `AddMediatR(...)` with the new registration; delete the MediatR package.
5. Replace `using MediatR;` with the port (or new lib) namespace; build.
6. Move pipeline behaviors over; run tests to confirm dispatch parity.

## References

- https://github.com/martinothamar/Mediator (MIT, source-generated)
- https://wolverinefx.net (MIT)
