---
name: tunit-testing
description: "Authors source-generated tests with TUnit, a Microsoft.Testing.Platform-native framework (no VSTest adapter, AOT-friendly). Use when you want compile-time test discovery, rich async lifecycle hooks, and fluent assertions on .NET 10. Do NOT use for established xUnit/NSubstitute suites (use unit-testing), HTTP integration tests (use integration-testing), or mutation scoring (use mutation-testing). MATURITY: TUnit is pre-1.0 — API may shift; pin the version and treat it as evolving."
metadata:
  category: "testing"
  agent: "test-engineer"
---
# TUnit — Source-Generated Testing

> **Maturity:** TUnit is **pre-1.0**. The API is still evolving and may introduce
> breaking changes between minor versions. Pin an exact package version and review
> release notes on upgrade. For mainstream/stable suites prefer xUnit (see
> `unit-testing`); adopt TUnit where its source-generation/AOT story earns its keep.

## Core Principles

- TUnit runs **only** on `Microsoft.Testing.Platform` — there is no VSTest adapter. The test project *is* the runnable; `dotnet test` and `dotnet run` both invoke it.
- Tests are discovered via a **source generator** at compile time, not reflection — this is what makes TUnit Native-AOT and trimming friendly.
- Set `<EnableTUnit>` / `<OutputType>Exe</OutputType>` is handled by the SDK ref; you do not add a separate runner package.
- Lifecycle is async-first: `[Before(Test)]`, `[After(Test)]`, `[Before(Class)]`, `[Before(Assembly)]`.
- Assertions are async and fluent: `await Assert.That(value).IsEqualTo(expected)`.
- Data-driven via `[Arguments(...)]`, `[MethodDataSource]`, `[ClassDataSource]`; tests run in parallel by default — opt out with `[NotInParallel]`.

## Example

```csharp
public sealed class PriceCalculatorTests
{
    private PriceCalculator _sut = null!;

    [Before(Test)]
    public Task Setup()
    {
        _sut = new PriceCalculator(taxRate: 0.10m);
        return Task.CompletedTask;
    }

    [Test]
    [Arguments(100, 110)]
    [Arguments(0, 0)]
    public async Task Applies_tax_to_subtotal(decimal subtotal, decimal expected)
    {
        var total = _sut.WithTax(subtotal);

        await Assert.That(total).IsEqualTo(expected);
    }

    [Test]
    public async Task Throws_on_negative_subtotal()
    {
        await Assert.That(() => _sut.WithTax(-1m))
            .Throws<ArgumentOutOfRangeException>();
    }
}
```

```xml
<!-- Tests.csproj: a runnable executable, MTP-native -->
<PropertyGroup>
  <TargetFramework>net10.0</TargetFramework>
  <OutputType>Exe</OutputType>
</PropertyGroup>
<ItemGroup>
  <PackageReference Include="TUnit" Version="0.*" /> <!-- pin exact in real use -->
</ItemGroup>
```

## Gotchas

- Mixing TUnit and xUnit in one project does not work — TUnit owns the entry point. Keep them in separate projects.
- CI runners that shell out to a VSTest adapter need the MTP `--report-trx` style args instead; pass platform options directly to the test executable.
- `IDE` test explorers need MTP support enabled (`dotnet.testWindow.useTestingPlatformProtocol`) to discover TUnit tests.
- Because discovery is compile-time, a test that does not build is simply absent — watch the build output, not just the run summary.

## References

- https://tunit.dev/
- https://learn.microsoft.com/en-us/dotnet/core/testing/microsoft-testing-platform-intro
