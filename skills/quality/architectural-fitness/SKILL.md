---
name: architectural-fitness
description: >
  Architecture tests with NetArchTest for enforcing dependency rules and
  project structure conventions. Covers layer dependency validation and naming rules.
  Trigger: architecture test, NetArchTest, dependency rule, fitness function.
metadata:
  category: quality
  agent: reviewer
  when-to-use: "When writing architecture fitness tests with NetArchTest or dependency rules"
---

# Architectural Fitness — NetArchTest & Dependency Rules

## Core Principles

- Architecture tests enforce project structure as code
- `NetArchTest` validates assembly dependencies and naming conventions
- Tests run in CI to prevent architectural drift
- Layer dependency rules: inner layers never reference outer layers
- Naming conventions enforced: handlers end with `Handler`, etc.

## Key Patterns

### NetArchTest Setup

```xml
<!-- Test project .csproj -->
<PackageReference Include="NetArchTest.Rules" />
<PackageReference Include="FluentAssertions" />
```

### Layer Dependency Tests

```csharp
namespace {Company}.{Domain}.Tests.Architecture;

public sealed class LayerDependencyTests
{
    private static readonly Assembly DomainAssembly =
        typeof(Order).Assembly;
    private static readonly Assembly ApplicationAssembly =
        typeof(CreateOrderCommand).Assembly;
    private static readonly Assembly InfrastructureAssembly =
        typeof(ApplicationDbContext).Assembly;

    [Fact]
    public void Domain_ShouldNotDependOn_Application()
    {
        var result = Types.InAssembly(DomainAssembly)
            .ShouldNot()
            .HaveDependencyOn(ApplicationAssembly.GetName().Name!)
            .GetResult();

        result.IsSuccessful.Should().BeTrue(
            because: FormatFailures(result));
    }

    [Fact]
    public void Domain_ShouldNotDependOn_Infrastructure()
    {
        var result = Types.InAssembly(DomainAssembly)
            .ShouldNot()
            .HaveDependencyOn(InfrastructureAssembly.GetName().Name!)
            .GetResult();

        result.IsSuccessful.Should().BeTrue(
            because: FormatFailures(result));
    }

    [Fact]
    public void Application_ShouldNotDependOn_Infrastructure()
    {
        var result = Types.InAssembly(ApplicationAssembly)
            .ShouldNot()
            .HaveDependencyOn(InfrastructureAssembly.GetName().Name!)
            .GetResult();

        result.IsSuccessful.Should().BeTrue(
            because: FormatFailures(result));
    }

    private static string FormatFailures(TestResult result) =>
        string.Join(", ", result.FailingTypeNames ?? []);
}
```

### Naming Convention Tests

```csharp
namespace {Company}.{Domain}.Tests.Architecture;

public sealed class NamingConventionTests
{
    [Fact]
    public void Handlers_ShouldEndWith_Handler()
    {
        var result = Types.InAssembly(typeof(CreateOrderHandler).Assembly)
            .That()
            .ImplementInterface(typeof(IRequestHandler<,>))
            .Should()
            .HaveNameEndingWith("Handler")
            .GetResult();

        result.IsSuccessful.Should().BeTrue(
            because: FormatFailures(result));
    }

    [Fact]
    public void Validators_ShouldEndWith_Validator()
    {
        var result = Types.InAssembly(typeof(CreateOrderValidator).Assembly)
            .That()
            .Inherit(typeof(AbstractValidator<>))
            .Should()
            .HaveNameEndingWith("Validator")
            .GetResult();

        result.IsSuccessful.Should().BeTrue(
            because: FormatFailures(result));
    }

    [Fact]
    public void Entities_ShouldHave_PrivateSetters()
    {
        var entityTypes = Types.InAssembly(typeof(Order).Assembly)
            .That()
            .ResideInNamespace("{Company}.{Domain}.Query.Domain")
            .GetTypes();

        foreach (var type in entityTypes)
        {
            var publicSetters = type.GetProperties()
                .Where(p => p.SetMethod?.IsPublic == true
                    && p.Name != "ETag"); // Cosmos exception

            publicSetters.Should().BeEmpty(
                because: $"{type.Name} should use private setters");
        }
    }
}
```

### Microservice Architecture Tests

```csharp
[Fact]
public void CommandHandlers_ShouldNotDirectly_AccessDbContext()
{
    var result = Types.InAssembly(typeof(CreateOrderHandler).Assembly)
        .That()
        .HaveNameEndingWith("Handler")
        .ShouldNot()
        .HaveDependencyOn("Microsoft.EntityFrameworkCore")
        .GetResult();

    result.IsSuccessful.Should().BeTrue(
        because: "Handlers should use ICommitEventService, not DbContext directly");
}

[Fact]
public void EventData_ShouldBe_Sealed_Records()
{
    var eventDataTypes = Types.InAssembly(typeof(OrderCreatedData).Assembly)
        .That()
        .ImplementInterface(typeof(IEventData))
        .GetTypes();

    foreach (var type in eventDataTypes)
    {
        type.IsSealed.Should().BeTrue(
            because: $"{type.Name} should be sealed");
        type.IsClass.Should().BeTrue(); // records are classes
    }
}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| No architecture tests | Add tests for critical dependency rules |
| Tests only at creation | Run in CI to prevent drift |
| Overly strict rules | Focus on critical boundaries |
| Ignoring test failures | Fix violations or update rules with justification |

## Detect Existing Patterns

```bash
# Find NetArchTest
grep -r "NetArchTest" --include="*.csproj" tests/

# Find architecture tests
grep -r "Types.InAssembly\|ShouldNot.*HaveDependencyOn" --include="*.cs" tests/

# Find naming convention tests
grep -r "HaveNameEndingWith" --include="*.cs" tests/
```

## Adding to Existing Project

1. **Check for existing architecture tests** before adding new ones
2. **Start with critical boundaries** — Domain should not reference Infrastructure
3. **Add naming convention tests** for handlers, validators, entities
4. **Run in CI pipeline** as part of the test step
5. **Document exceptions** when rules need to be relaxed
