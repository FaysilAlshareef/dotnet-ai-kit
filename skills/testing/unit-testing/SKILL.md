---
name: unit-testing
description: >
  Unit testing patterns with xUnit, NSubstitute/Moq, and FluentAssertions.
  Covers Arrange-Act-Assert, test naming, mocking strategies, and test organization.
  Trigger: unit test, xUnit, NSubstitute, Moq, FluentAssertions, AAA.
category: testing
agent: test-engineer
---

# Unit Testing — xUnit, Mocking, Assertions

## Core Principles

- Follow **Arrange-Act-Assert** (AAA) pattern in every test
- Test naming: `{MethodName}_When{Condition}_Should{Expected}`
- One assertion per test (or closely related assertions)
- Use NSubstitute (preferred) or Moq for mocking dependencies
- FluentAssertions for readable, expressive assertions
- Test behavior, not implementation details

## Key Patterns

### Basic Test Structure

```csharp
namespace {Company}.{Domain}.Tests.Unit;

public sealed class OrderServiceTests
{
    private readonly IOrderRepository _repository = Substitute.For<IOrderRepository>();
    private readonly IUnitOfWork _unitOfWork = Substitute.For<IUnitOfWork>();
    private readonly OrderService _sut;

    public OrderServiceTests()
    {
        _sut = new OrderService(_repository, _unitOfWork);
    }

    [Fact]
    public async Task GetOrderAsync_WhenOrderExists_ShouldReturnOrder()
    {
        // Arrange
        var orderId = Guid.NewGuid();
        var expected = new Order { Id = orderId, CustomerName = "Test" };
        _repository.FindAsync(orderId, Arg.Any<CancellationToken>())
            .Returns(expected);

        // Act
        var result = await _sut.GetOrderAsync(orderId);

        // Assert
        result.Should().NotBeNull();
        result!.CustomerName.Should().Be("Test");
    }

    [Fact]
    public async Task GetOrderAsync_WhenOrderNotFound_ShouldReturnNull()
    {
        // Arrange
        _repository.FindAsync(Arg.Any<Guid>(), Arg.Any<CancellationToken>())
            .Returns((Order?)null);

        // Act
        var result = await _sut.GetOrderAsync(Guid.NewGuid());

        // Assert
        result.Should().BeNull();
    }
}
```

### Testing MediatR Handlers

```csharp
public sealed class CreateOrderHandlerTests
{
    private readonly ICommitEventService<OrderEventData> _commitService =
        Substitute.For<ICommitEventService<OrderEventData>>();
    private readonly CreateOrderHandler _sut;

    public CreateOrderHandlerTests()
    {
        _sut = new CreateOrderHandler(_commitService);
    }

    [Fact]
    public async Task Handle_ShouldCreateOrderAndCommitEvents()
    {
        // Arrange
        var command = new CreateOrderCommand("Test Customer", 100m, []);

        // Act
        var result = await _sut.Handle(command, CancellationToken.None);

        // Assert
        result.Id.Should().NotBeEmpty();
        result.Sequence.Should().Be(1);

        await _commitService.Received(1).CommitAsync(
            Arg.Any<Guid>(),
            Arg.Is<IReadOnlyList<Event<OrderEventData>>>(events =>
                events.Count == 1),
            Arg.Any<CancellationToken>());
    }
}
```

### FluentAssertions Patterns

```csharp
// Collection assertions
orders.Should().HaveCount(3);
orders.Should().Contain(o => o.CustomerName == "Test");
orders.Should().BeInDescendingOrder(o => o.Total);
orders.Should().AllSatisfy(o => o.Status.Should().Be(OrderStatus.Active));

// Object assertions
order.Should().BeEquivalentTo(expected, options =>
    options.Excluding(o => o.RowVersion));

// Exception assertions
var act = () => order.Complete();
act.Should().Throw<InvalidOperationException>()
    .WithMessage("*already completed*");

// Async exception assertions
var act = async () => await handler.Handle(command, CancellationToken.None);
await act.Should().ThrowAsync<OrderNotFoundException>();
```

### Parameterized Tests

```csharp
[Theory]
[InlineData("", false)]
[InlineData("Valid Name", true)]
[InlineData(null, false)]
public void Validate_CustomerName_ShouldReturnExpectedResult(
    string? name, bool expectedValid)
{
    // Arrange
    var validator = new CreateOrderValidator();
    var command = new CreateOrderCommand(name!, 100m, []);

    // Act
    var result = validator.Validate(command);

    // Assert
    result.IsValid.Should().Be(expectedValid);
}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Testing private methods directly | Test through public API |
| Multiple unrelated assertions | One logical assertion per test |
| Brittle mock verification order | Verify behavior, not call sequence |
| Test names like `Test1`, `TestCreate` | Descriptive: `MethodName_When_Should` |
| Sharing mutable state between tests | Fresh instances per test (constructor) |

## Detect Existing Patterns

```bash
# Find test projects
find . -name "*Tests*.csproj" -type f

# Find xUnit usage
grep -r "\[Fact\]\|\[Theory\]" --include="*.cs" tests/

# Find mocking framework
grep -r "Substitute.For\|Mock<\|new Mock" --include="*.cs" tests/

# Find FluentAssertions
grep -r "\.Should()" --include="*.cs" tests/
```

## Adding to Existing Project

1. **Match the existing mocking framework** — NSubstitute or Moq (don't mix)
2. **Follow test naming conventions** used in existing tests
3. **Use FluentAssertions** if already in the project
4. **Place tests in parallel structure**: `src/X/` maps to `tests/X.Tests/`
5. **One test class per production class** with matching name suffix `Tests`
