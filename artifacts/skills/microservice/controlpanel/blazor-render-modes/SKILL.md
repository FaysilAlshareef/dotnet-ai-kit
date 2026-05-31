---
name: blazor-render-modes
description: "Selects and applies the right .NET 10 Blazor render mode per component — Static SSR, Interactive Server, Interactive WebAssembly, or Interactive Auto — and wires the App.razor host correctly. Use when deciding where a component runs and why a page is or is not interactive. Do NOT use for building the component UI itself (use blazor-component / mudblazor-patterns) or for persisting state across reconnects (use blazor-persistent-state)."
metadata:
  category: "microservice/controlpanel"
  agent: "controlpanel-architect"
---
# Blazor Render Modes (.NET 10)

## Core Principles

- A Blazor Web App has **four** render modes. Default (no `@rendermode`) is **Static SSR**: HTML rendered once, no interactivity, cheapest.
- `InteractiveServer` keeps a SignalR circuit and runs C# on the server — instant load, low download, but needs a live connection and server resources per user.
- `InteractiveWebAssembly` downloads the .NET runtime + DLLs and runs in the browser — offline-capable, no per-user server cost, but a heavier first load.
- `InteractiveAuto` renders Server on the first visit (fast), then silently switches to WASM once the runtime is cached — best of both for return visits.
- Render mode applies at the `@rendermode` directive on a component *or* per `<Component>` instance; it cascades to children, so set it as low in the tree as possible.
- Enable the modes you use in `Program.cs` (`AddInteractiveServerComponents` / `AddInteractiveWebAssemblyComponents`) and on `App.razor`.

## Example

```razor
@* Counter.razor — needs interactivity; pick Server for a control panel *@
@rendermode InteractiveServer

<MudButton OnClick="Increment">Count: @_count</MudButton>

@code {
    private int _count;
    private void Increment() => _count++;
}
```

```csharp
// Program.cs — register render modes you actually use
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents()
    .AddInteractiveWebAssemblyComponents();

var app = builder.Build();
app.MapRazorComponents<App>()
   .AddInteractiveServerRenderMode()
   .AddInteractiveWebAssemblyRenderMode();
```

```razor
@* App.razor — host head/body in Static SSR; opt specific pages in *@
<HeadOutlet @rendermode="InteractiveAuto" />
...
<Routes @rendermode="InteractiveAuto" />
```

## Decision Guide

| Component need | Mode |
|----------------|------|
| Read-only page, SEO/first-paint critical | Static SSR (default) |
| Rich interactivity, fast load, internal/admin app | Interactive Server |
| Offline / no per-user server cost / public SPA | Interactive WebAssembly |
| Fast first visit + cheap return visits | Interactive Auto |

## Gotchas

- Static SSR components have **no** `@onclick`, `OnInitializedAsync` re-renders, or event callbacks — adding a handler silently does nothing until you set an interactive mode.
- An interactive parent forces its children interactive; you cannot nest a Static SSR island inside an Interactive Server subtree.
- `InteractiveAuto` and WASM components run in the browser, so they cannot inject server-only services (e.g. a `DbContext`) — call an API instead.
- Prerendering runs component init **twice** (server prerender, then interactive) — make `OnInitializedAsync` idempotent and guard double data fetches.

## References

- https://learn.microsoft.com/en-us/aspnet/core/blazor/components/render-modes
