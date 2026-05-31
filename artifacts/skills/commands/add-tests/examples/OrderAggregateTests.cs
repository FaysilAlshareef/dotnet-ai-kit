using FluentAssertions;
using Sample.Domain.Aggregates;
using Xunit;

namespace Sample.Domain.Tests;

// xUnit tests for the Order aggregate. Each test follows Arrange / Act / Assert
// and verifies state transitions plus invariant enforcement.
public class OrderAggregateTests
{
    [Fact]
    public void Place_WithValidTotal_StartsPending()
    {
        // Arrange
        var id = Guid.NewGuid();

        // Act
        var order = Order.Place(id, "Ada Lovelace", total: 49.99m);

        // Assert
        order.Id.Should().Be(id);
        order.CustomerName.Should().Be("Ada Lovelace");
        order.Status.Should().Be(OrderStatus.Pending);
    }

    [Fact]
    public void Place_WithNonPositiveTotal_Throws()
    {
        // Act
        var act = () => Order.Place(Guid.NewGuid(), "Ada Lovelace", total: 0m);

        // Assert
        act.Should().Throw<ArgumentOutOfRangeException>();
    }

    [Fact]
    public void Complete_WhenPending_TransitionsToCompleted()
    {
        // Arrange
        var order = Order.Place(Guid.NewGuid(), "Grace Hopper", total: 10m);

        // Act
        order.Complete();

        // Assert (plain xUnit assertion alongside FluentAssertions)
        Assert.Equal(OrderStatus.Completed, order.Status);
    }

    [Fact]
    public void Complete_WhenAlreadyCompleted_Throws()
    {
        // Arrange
        var order = Order.Place(Guid.NewGuid(), "Grace Hopper", total: 10m);
        order.Complete();

        // Act
        var act = () => order.Complete();

        // Assert
        act.Should().Throw<InvalidOperationException>();
    }
}
