---
name: blazor-hybrid
description: "Reuses the control-panel's Razor component library in a .NET MAUI Blazor Hybrid app (BlazorWebView) to ship a native desktop/mobile shell from the same components. Use when packaging the existing web control-panel UI into a MAUI Blazor Hybrid host. Do NOT use for choosing web render modes (use blazor-render-modes) or for building the components themselves (use blazor-component)."
---
# Blazor Hybrid (MAUI) — reuse the control-panel components natively

MAUI Blazor Hybrid hosts your existing Razor components in a native app via `BlazorWebView`,
rendering with the platform WebView but executing component logic in the native .NET process
(no WebAssembly, no server round-trip). Use it to ship the control panel as a desktop/mobile app
from the same component library — not to replace the web app.

## When to reach for it

- You already have a Razor Class Library (RCL) of control-panel components (grids, dialogs, forms)
  and want a native desktop/mobile shell without rewriting the UI.
- You need native-device access (file system, notifications, MAUI Essentials) alongside the shared UI.
- **Not** for choosing where a web component runs (that is `blazor-render-modes`), and **not** for
  authoring the components (that is `blazor-component` / `mudblazor-patterns`).

## Shape

```csharp
// MauiProgram.cs
var builder = MauiApp.CreateBuilder();
builder.UseMauiApp<App>();
builder.Services.AddMauiBlazorWebView();
#if DEBUG
builder.Services.AddBlazorWebViewDeveloperTools();
#endif
builder.Services.AddControlPanelComponents(); // the shared RCL's DI extension
return builder.Build();
```

```razor
@* MainPage.xaml hosts a BlazorWebView whose RootComponent points at the shared App *@
<BlazorWebView HostPage="wwwroot/index.html">
    <BlazorWebView.RootComponents>
        <RootComponent Selector="#app" ComponentType="typeof(ControlPanel.Shared.Routes)" />
    </BlazorWebView.RootComponents>
</BlazorWebView>
```

## Key constraints

- **Share via an RCL**: factor components into a Razor Class Library referenced by both the web host
  and the MAUI host. Keep gateway/HTTP access behind an injected service so each host wires its own.
- **No server interactivity**: Hybrid runs component logic in-process — `@rendermode` directives and
  circuit/`[PersistentState]` concerns do not apply (that is the web app's domain).
- **Platform branching** belongs behind abstractions (`#if`/DI), never scattered in components.
- **Auth/token flow** differs from the web app (no cookie/circuit) — use MAUI-appropriate secure storage.

## Anti-patterns

- Forking the components for native instead of sharing the RCL (drift).
- Calling gateways directly from a component instead of an injected typed client (use `gateway-facade`).
- Treating Hybrid like Blazor Server/WASM (wrong interactivity model).
