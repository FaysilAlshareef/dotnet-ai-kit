---
name: graphql-hotchocolate
description: "Builds a GraphQL API with HotChocolate v15 — code-first queries, mutations, subscriptions, DataLoader batching to defeat N+1, and the @authorize directive. Use when clients need to shape responses, subscribe to live data, or traverse a graph in one round-trip. Do NOT use for resource-oriented REST (use minimal-api), high-throughput binary RPC (use grpc-design), or raw bidirectional hub messaging (use signalr-realtime)."
---
# GraphQL with HotChocolate v15

## Core Principles

- HotChocolate is **code-first**: annotate plain C# types; the schema is generated. Register with `AddGraphQLServer()` and map `MapGraphQL()`.
- One root per operation: `[QueryType]`, `[MutationType]`, `[SubscriptionType]` (or `AddQueryType<>` etc.). Keep resolvers thin — delegate to MediatR/services.
- **DataLoader** is mandatory to avoid N+1: batch child lookups by key (`[DataLoader]` source-gen or `BatchDataLoader<TKey,TValue>`). Resolving a per-item DB call inside a list resolver is the classic GraphQL footgun.
- Secure fields/types with the `[Authorize]` directive (`AddAuthorization()`), which maps to ASP.NET Core policies — not a separate auth system.
- Subscriptions need a transport: in-memory for dev, Redis for scale-out; the resolver pushes via `ITopicEventSender`.
- Inject scoped services with `[Service]`; never capture a `DbContext` in a field — use `IDbContextFactory` / `RegisterDbContextFactory` for resolver-safe contexts.

## Example

```csharp
// Program.cs
builder.Services
    .AddGraphQLServer()
    .AddAuthorization()
    .AddQueryType<Query>()
    .AddMutationType<Mutation>()
    .AddSubscriptionType<Subscription>()
    .AddInMemorySubscriptions();

var app = builder.Build();
app.UseAuthentication();
app.UseAuthorization();
app.MapGraphQL();
```

```csharp
public sealed class Query
{
    // DataLoader batches all author lookups in this request into one query.
    [Authorize(Policy = "read:orders")]
    public async Task<IEnumerable<Order>> GetOrders(
        [Service] ISender sender, CancellationToken ct)
        => await sender.Send(new ListOrdersQuery(), ct);
}

public sealed class Mutation
{
    public async Task<Order> CreateOrder(
        CreateOrderInput input,
        [Service] ISender sender,
        [Service] ITopicEventSender events,
        CancellationToken ct)
    {
        var order = await sender.Send(new CreateOrderCommand(input.Customer), ct);
        await events.SendAsync(nameof(Subscription.OnOrderCreated), order, ct);
        return order;
    }
}

public sealed class Subscription
{
    [Subscribe]
    public Order OnOrderCreated([EventMessage] Order order) => order;
}

// Source-generated batch DataLoader — keyed lookup, one round-trip per request.
internal static class CustomerDataLoader
{
    [DataLoader]
    public static async Task<IReadOnlyDictionary<Guid, Customer>> GetCustomersByIdAsync(
        IReadOnlyList<Guid> ids, AppDbContext db, CancellationToken ct)
        => await db.Customers.Where(c => ids.Contains(c.Id))
            .ToDictionaryAsync(c => c.Id, ct);
}
```

## Gotchas

- A resolver that opens a `DbContext` per list element re-introduces N+1 even with GraphQL — push the batched fetch into a DataLoader keyed by ID.
- `[Authorize]` requires `AddAuthorization()` on the GraphQL server *and* the ASP.NET Core auth middleware; missing either makes the directive a no-op.
- Cap query depth/complexity (`AddMaxExecutionDepthRule`, cost analysis) — GraphQL lets a client request an arbitrarily deep graph.
- Subscriptions over WebSockets need the WebSocket middleware enabled; behind multiple instances, swap the in-memory provider for Redis.

## References

- https://chillicream.com/docs/hotchocolate/v15
- https://chillicream.com/docs/hotchocolate/v15/fetching-data/dataloader
