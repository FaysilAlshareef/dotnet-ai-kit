---
name: signalr-realtime
description: >
  SignalR real-time communication — hub design, typed clients, group management,
  authentication, Redis backplane scaling, and JavaScript/.NET client integration.
  Trigger: SignalR, real-time, WebSocket, hub, push notification, live update.
metadata:
  category: api
  agent: api-designer
  when-to-use: "When implementing real-time communication with SignalR hubs or WebSocket connections"
---

# SignalR Real-Time Communication

## Core Principles

- Use **typed hubs** (`Hub<T>`) with a client interface for compile-time safety
- Prefer **persistent connections** over polling — SignalR negotiates the best transport (WebSocket > SSE > Long Polling)
- Organize messaging around **groups** — send to logical sets of connections, not individual connection IDs
- Keep hub methods thin — delegate business logic to services, just like controllers
- Track connection lifecycle (`OnConnectedAsync` / `OnDisconnectedAsync`) for presence and cleanup

## When to Use

- **Push notifications** — order status changes, alerts, system announcements
- **Live dashboards** — real-time metrics, stock tickers, monitoring panels
- **Chat and messaging** — direct messages, group conversations, typing indicators
- **Collaborative editing** — shared cursors, live document updates, whiteboard sync
- **Live feeds** — activity streams, auction bidding, sports scores

## When NOT to Use

- **Standard request-response** — use REST or Minimal API endpoints instead
- **Batch processing** — use background jobs (Hangfire, MassTransit) instead
- **Fire-and-forget messaging** — use a message queue (RabbitMQ, Azure Service Bus)
- **File uploads/downloads** — use HTTP endpoints with streaming
- **Infrequent updates** — polling or server-sent events may be simpler

## Patterns

### Hub Design

Define a typed client interface and a strongly-typed hub:

```csharp
// Contracts/INotificationClient.cs
public interface INotificationClient
{
    Task ReceiveNotification(NotificationMessage message);
    Task OrderStatusChanged(Guid orderId, string status);
    Task UserJoined(string userName);
    Task UserLeft(string userName);
}

public sealed record NotificationMessage(
    string Title,
    string Body,
    string Severity,
    DateTimeOffset Timestamp);
```

```csharp
// Hubs/NotificationHub.cs
[Authorize]
public sealed class NotificationHub(
    ILogger<NotificationHub> logger)
    : Hub<INotificationClient>
{
    public async Task SendToGroup(string groupName,
        NotificationMessage message)
    {
        logger.LogInformation(
            "Sending notification to group {Group}", groupName);
        await Clients.Group(groupName)
            .ReceiveNotification(message);
    }

    public async Task SendToUser(string userId,
        NotificationMessage message)
    {
        await Clients.User(userId)
            .ReceiveNotification(message);
    }

    public override async Task OnConnectedAsync()
    {
        var userId = Context.UserIdentifier;
        logger.LogInformation(
            "User {UserId} connected: {ConnectionId}",
            userId, Context.ConnectionId);
        await base.OnConnectedAsync();
    }

    public override async Task OnDisconnectedAsync(
        Exception? exception)
    {
        logger.LogInformation(
            "User {UserId} disconnected: {ConnectionId}",
            Context.UserIdentifier, Context.ConnectionId);
        await base.OnDisconnectedAsync(exception);
    }
}
```

```csharp
// Program.cs
builder.Services.AddSignalR();

var app = builder.Build();
app.MapHub<NotificationHub>("/hubs/notifications");
```

### Group Management

Use groups to target messages to logical sets of users:

```csharp
public sealed class OrderHub(
    ILogger<OrderHub> logger)
    : Hub<IOrderClient>
{
    public async Task JoinOrderGroup(Guid orderId)
    {
        var groupName = $"order-{orderId}";
        await Groups.AddToGroupAsync(
            Context.ConnectionId, groupName);
        logger.LogInformation(
            "Connection {ConnectionId} joined group {Group}",
            Context.ConnectionId, groupName);
    }

    public async Task LeaveOrderGroup(Guid orderId)
    {
        var groupName = $"order-{orderId}";
        await Groups.RemoveFromGroupAsync(
            Context.ConnectionId, groupName);
    }
}

// Sending from a service using IHubContext
public sealed class OrderService(
    IHubContext<OrderHub, IOrderClient> hubContext)
{
    public async Task UpdateOrderStatus(
        Guid orderId, string status)
    {
        // Business logic here...

        await hubContext.Clients
            .Group($"order-{orderId}")
            .OrderStatusChanged(orderId, status);
    }
}
```

### Authentication

Apply `[Authorize]` on the hub and pass bearer tokens via query string for WebSocket transport:

```csharp
// Program.cs — configure JWT to read token from query string
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidIssuer = builder.Configuration["Jwt:Issuer"],
            ValidAudience = builder.Configuration["Jwt:Audience"],
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(
                    builder.Configuration["Jwt:Key"]!))
        };

        // SignalR sends token as query string for WebSocket
        options.Events = new JwtBearerEvents
        {
            OnMessageReceived = context =>
            {
                var accessToken = context.Request
                    .Query["access_token"];
                var path = context.HttpContext.Request.Path;

                if (!string.IsNullOrEmpty(accessToken)
                    && path.StartsWithSegments("/hubs"))
                {
                    context.Token = accessToken;
                }

                return Task.CompletedTask;
            }
        };
    });
```

```csharp
// Hub with role-based authorization
[Authorize(Roles = "Admin,Manager")]
public sealed class AdminHub : Hub<IAdminClient>
{
    [Authorize(Policy = "CanManageUsers")]
    public async Task BroadcastAlert(string message)
    {
        await Clients.All.AlertReceived(message);
    }
}
```

### Connection Lifecycle

Track connections for presence features and cleanup:

```csharp
public sealed class PresenceHub(
    IConnectionTracker tracker)
    : Hub<IPresenceClient>
{
    public override async Task OnConnectedAsync()
    {
        var userId = Context.UserIdentifier
            ?? throw new HubException("User not authenticated");
        await tracker.AddConnectionAsync(
            userId, Context.ConnectionId);
        await Clients.All.OnlineUsersUpdated(
            await tracker.GetOnlineUsersAsync());
        await base.OnConnectedAsync();
    }

    public override async Task OnDisconnectedAsync(
        Exception? exception)
    {
        var userId = Context.UserIdentifier!;
        await tracker.RemoveConnectionAsync(
            userId, Context.ConnectionId);
        if (!await tracker.IsOnlineAsync(userId))
            await Clients.Others.UserLeft(userId);
        await base.OnDisconnectedAsync(exception);
    }
}
```

Implement `IConnectionTracker` with a `ConcurrentDictionary<string, HashSet<string>>` mapping user IDs to connection IDs. Use an external store (Redis) for multi-server deployments.

### JavaScript Client

```javascript
// npm install @microsoft/signalr
import * as signalR from "@microsoft/signalr";

const connection = new signalR.HubConnectionBuilder()
    .withUrl("/hubs/notifications", {
        accessTokenFactory: () => localStorage.getItem("token")
    })
    .withAutomaticReconnect([0, 2000, 5000, 10000, 30000])
    .configureLogging(signalR.LogLevel.Information)
    .build();

// Register handlers before starting
connection.on("ReceiveNotification", (message) => {
    console.log(`${message.title}: ${message.body}`);
});

connection.onreconnecting(() => console.warn("Reconnecting..."));
connection.onclose((err) => console.error("Connection closed:", err));

async function start() {
    try {
        await connection.start();
        await connection.invoke("JoinOrderGroup", orderId);
    } catch (err) {
        console.error("Connection failed:", err);
        setTimeout(start, 5000);
    }
}

start();
```

### .NET Client

```csharp
// Install: Microsoft.AspNetCore.SignalR.Client
var connection = new HubConnectionBuilder()
    .WithUrl("https://localhost:5001/hubs/notifications",
        options =>
        {
            options.AccessTokenProvider =
                () => Task.FromResult(token);
        })
    .WithAutomaticReconnect()
    .Build();

connection.On<NotificationMessage>(
    "ReceiveNotification", message =>
    Console.WriteLine($"{message.Title}: {message.Body}"));

connection.Closed += async _ =>
{
    await Task.Delay(Random.Shared.Next(0, 5) * 1000);
    await connection.StartAsync();
};

await connection.StartAsync();
await connection.InvokeAsync("SendToGroup", "admins",
    new NotificationMessage("Alert", "Server load high",
        "Warning", DateTimeOffset.UtcNow));
```

### Redis Backplane

Scale SignalR across multiple servers with a Redis backplane:

```csharp
// Install: Microsoft.AspNetCore.SignalR.StackExchangeRedis
builder.Services.AddSignalR()
    .AddStackExchangeRedis(
        builder.Configuration
            .GetConnectionString("Redis")!,
        options =>
        {
            options.Configuration.ChannelPrefix =
                RedisChannel.Literal("MyApp");
        });
```

For Azure deployments, use the Azure SignalR Service:

```csharp
// Install: Microsoft.Azure.SignalR
builder.Services.AddSignalR()
    .AddAzureSignalR(
        builder.Configuration
            .GetConnectionString("AzureSignalR")!);
```

## Decision Guide

| Scenario | Recommendation |
|----------|---------------|
| Single server, few clients | In-process SignalR, no backplane needed |
| Multi-server deployment | Add Redis backplane or Azure SignalR Service |
| Public-facing, high scale | Azure SignalR Service (serverless or default mode) |
| Authenticated users only | `[Authorize]` on hub + JWT via query string |
| Targeting specific users | Use `Clients.User(userId)` with `IUserIdProvider` |
| Targeting logical groups | Use `Groups.AddToGroupAsync` + `Clients.Group()` |
| Broadcasting from services | Inject `IHubContext<THub, TClient>` |
| Client is a browser SPA | `@microsoft/signalr` npm package with auto-reconnect |
| Client is another .NET app | `Microsoft.AspNetCore.SignalR.Client` NuGet |

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Untyped `Hub` with magic strings | Runtime errors, no IntelliSense | Use `Hub<T>` with typed client interface |
| Storing state in hub fields | Hubs are transient, state lost per call | Use `IConnectionTracker` or external store |
| Blocking calls in hub methods | Starves SignalR thread pool | Always use `async`/`await` |
| Missing `[Authorize]` on hub | Unauthenticated access to real-time data | Add `[Authorize]` and configure JWT |
| No reconnect on client | Silent disconnection, missed messages | Use `withAutomaticReconnect()` |
| Sending large payloads | WebSocket frame limits, slow clients | Send notification + fetch data via REST |
| Not using groups for multi-tenant | Cross-tenant data leaks | Assign users to tenant groups on connect |
| Calling `Clients.All` for targeted messages | Unnecessary traffic to unrelated clients | Use `Clients.Group()` or `Clients.User()` |

## Detect Existing Patterns

1. Search for `Hub<` or `: Hub` class inheritance in hub files
2. Look for `MapHub<` in `Program.cs`
3. Check for `AddSignalR()` in service registration
4. Look for `@microsoft/signalr` in `package.json`
5. Check for `IHubContext<` injections in services
6. Search for `AddStackExchangeRedis` or `AddAzureSignalR` for scaling config

## Adding to Existing Project

1. **Install** `Microsoft.AspNetCore.SignalR` (included in ASP.NET Core shared framework)
2. **Define typed client interface** with methods matching client-side handlers
3. **Create hub class** inheriting `Hub<TClient>` with `[Authorize]`
4. **Register** `builder.Services.AddSignalR()` and `app.MapHub<THub>("/hubs/...")`
5. **Configure JWT** `OnMessageReceived` to read `access_token` from query string
6. **Add client library** — `@microsoft/signalr` for JS or `SignalR.Client` NuGet for .NET
7. **Add Redis backplane** if deploying to multiple servers

## References

- https://learn.microsoft.com/en-us/aspnet/core/signalr/introduction
- https://learn.microsoft.com/en-us/aspnet/core/signalr/hubs
- https://learn.microsoft.com/en-us/aspnet/core/signalr/groups
- https://learn.microsoft.com/en-us/aspnet/core/signalr/authn-and-authz
- https://learn.microsoft.com/en-us/aspnet/core/signalr/scale
