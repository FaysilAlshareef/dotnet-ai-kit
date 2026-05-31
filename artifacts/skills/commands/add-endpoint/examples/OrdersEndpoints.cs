using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.AspNetCore.Routing;

namespace Sample.Api.Endpoints;

// Minimal API endpoint group. Routes are grouped under a common prefix and
// return TypedResults so the response contract is checked at compile time.
public static class OrdersEndpoints
{
    public static IEndpointRouteBuilder MapOrders(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/orders")
            .WithTags("Orders");

        group.MapGet("/{id:guid}", GetOrder)
            .WithSummary("Get an order by id");

        group.MapPost("/", CreateOrder)
            .WithSummary("Create a new order");

        return app;
    }

    private static Results<Ok<OrderResponse>, NotFound> GetOrder(Guid id, IOrderService orders)
    {
        var order = orders.Find(id);
        return order is not null
            ? TypedResults.Ok(order)
            : TypedResults.NotFound();
    }

    private static Results<Created<OrderResponse>, BadRequest<string>> CreateOrder(
        CreateOrderRequest request,
        IOrderService orders)
    {
        if (request.Total <= 0m)
            return TypedResults.BadRequest("Total must be positive.");

        var created = orders.Create(request.CustomerName, request.Total);
        return TypedResults.Created($"/orders/{created.Id}", created);
    }
}

public sealed record CreateOrderRequest(string CustomerName, decimal Total);

public sealed record OrderResponse(Guid Id, string CustomerName, decimal Total, string Status);

public interface IOrderService
{
    OrderResponse? Find(Guid id);
    OrderResponse Create(string customerName, decimal total);
}
