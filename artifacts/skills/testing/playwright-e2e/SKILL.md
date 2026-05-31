---
name: playwright-e2e
description: "Authors cross-browser end-to-end UI tests for the Blazor control panel with Microsoft.Playwright, driving real Chromium/Firefox/WebKit through user-visible flows. Use when you must verify rendered behaviour (auth redirect, grid loads, dialog submits) in an actual browser. Do NOT use for in-process component rendering with bUnit (use blazor-component), backend HTTP contract tests (use integration-testing), or load/throughput tests (use performance-testing)."
metadata:
  category: "testing"
  agent: "test-engineer"
---
# Playwright End-to-End Tests for Blazor

## Core Principles

- Use the `Microsoft.Playwright.NUnit` (or xUnit) base classes so each test gets a fresh `Page`/`BrowserContext` and automatic teardown.
- Drive the app through **user-visible** locators: `GetByRole`, `GetByLabel`, `GetByText` — never brittle CSS/XPath tied to MudBlazor internals.
- Playwright **auto-waits** for actionability; do NOT add `Task.Delay`/sleeps. Assert with web-first `Expect(...)` which retries until timeout.
- Run the same test matrix across `chromium`, `firefox`, and `webkit` to catch engine-specific rendering.
- Start the real app once (Aspire/`dotnet run` or a fixture) and point `BaseURL` at it; reset DB state per test, not per assertion.
- Install browsers in CI via `pwsh bin/Debug/net10.0/playwright.ps1 install --with-deps`.

## Example

```csharp
[Parallelizable(ParallelScope.Self)]
[TestFixture(BrowserType.Chromium)]
[TestFixture(BrowserType.Firefox)]
[TestFixture(BrowserType.Webkit)]
public sealed class OrdersPageTests(BrowserType browser) : PageTest
{
    public override BrowserNewContextOptions ContextOptions() => new()
    {
        BaseURL = "https://localhost:7100",
        IgnoreHTTPSErrors = true,
    };

    [Test]
    public async Task Creating_an_order_shows_it_in_the_grid()
    {
        await Page.GotoAsync("/orders");

        // Auto-waits for the button to be visible + enabled.
        await Page.GetByRole(AriaRole.Button, new() { Name = "New Order" })
            .ClickAsync();

        await Page.GetByLabel("Customer Name").FillAsync("Acme Corp");
        await Page.GetByRole(AriaRole.Button, new() { Name = "Create" })
            .ClickAsync();

        // Web-first assertion: retries until the row appears or times out.
        await Expect(Page.GetByRole(AriaRole.Cell, new() { Name = "Acme Corp" }))
            .ToBeVisibleAsync();
    }

    [Test]
    public async Task Unauthenticated_user_is_redirected_to_login()
    {
        await Page.GotoAsync("/orders");
        await Expect(Page).ToHaveURLAsync(new Regex(".*/login.*"));
    }
}
```

## Gotchas

- Blazor Server has a render-then-hydrate gap; assert on rendered content (`Expect(...).ToBeVisibleAsync`) rather than acting the instant navigation returns.
- Capture artifacts on failure: enable `Trace`/`Screenshot`/`Video` in `ContextOptions` so CI failures are debuggable.
- Storage-state reuse (`StorageState`) lets you sign in once and skip the login flow in every test — sign in in a setup fixture, save the cookie, replay it.
- Keep tests independent: never depend on data left by a previous test; seed and tear down per test.

## References

- https://playwright.dev/dotnet/docs/intro
- https://playwright.dev/dotnet/docs/best-practices
