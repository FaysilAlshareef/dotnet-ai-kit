---
name: dotnet-ai-auth-policies
description: >
  Policy-based authorization with custom requirements, handlers,
  and permission-based access control.
  Trigger: authorization, policy, permission, HasPermission, requirement, handler.
category: security
agent: api-designer
---

# Policy-Based Authorization

## Core Principles

- Use policies for fine-grained authorization beyond simple roles
- Create custom `IAuthorizationRequirement` and `IAuthorizationHandler` pairs
- Dynamic policy creation via `IAuthorizationPolicyProvider` for permission-based auth
- Permissions stored in JWT claims or loaded from database
- Resource-based authorization for entity-level access control

## Patterns

### Permission Constants

```csharp
public static class Permissions
{
    public const string OrdersRead = "orders:read";
    public const string OrdersCreate = "orders:create";
    public const string OrdersUpdate = "orders:update";
    public const string OrdersDelete = "orders:delete";
    public const string ReportsView = "reports:view";
    public const string UsersManage = "users:manage";
    public const string SettingsManage = "settings:manage";
}
```

### HasPermission Attribute

```csharp
[AttributeUsage(AttributeTargets.Class | AttributeTargets.Method)]
public sealed class HasPermissionAttribute(string permission)
    : AuthorizeAttribute(permission)
{
    public string Permission { get; } = permission;
}
```

### Permission Requirement

```csharp
public sealed class PermissionRequirement(string permission)
    : IAuthorizationRequirement
{
    public string Permission { get; } = permission;
}
```

### Permission Authorization Handler

```csharp
public sealed class PermissionAuthorizationHandler
    : AuthorizationHandler<PermissionRequirement>
{
    protected override Task HandleRequirementAsync(
        AuthorizationHandlerContext context,
        PermissionRequirement requirement)
    {
        var permissions = context.User
            .FindFirstValue("permissions")?
            .Split(',', StringSplitOptions.RemoveEmptyEntries)
            ?? [];

        if (permissions.Contains(requirement.Permission))
            context.Succeed(requirement);

        return Task.CompletedTask;
    }
}
```

### Dynamic Policy Provider

```csharp
public sealed class PermissionAuthorizationPolicyProvider(
    IOptions<AuthorizationOptions> options)
    : DefaultAuthorizationPolicyProvider(options)
{
    public override async Task<AuthorizationPolicy?> GetPolicyAsync(
        string policyName)
    {
        // Check for pre-defined policies first
        var policy = await base.GetPolicyAsync(policyName);
        if (policy is not null)
            return policy;

        // Create dynamic policy for permission strings
        return new AuthorizationPolicyBuilder()
            .AddRequirements(new PermissionRequirement(policyName))
            .Build();
    }
}
```

### Registration

```csharp
// Program.cs
builder.Services.AddSingleton<IAuthorizationPolicyProvider,
    PermissionAuthorizationPolicyProvider>();
builder.Services.AddSingleton<IAuthorizationHandler,
    PermissionAuthorizationHandler>();

// Pre-defined policies (optional, for complex requirements)
builder.Services.AddAuthorizationBuilder()
    .AddPolicy("AdminOnly", policy =>
        policy.RequireRole("Admin"))
    .AddPolicy("OrderManager", policy =>
        policy.RequireAssertion(context =>
            context.User.HasClaim("permissions", Permissions.OrdersCreate) &&
            context.User.HasClaim("permissions", Permissions.OrdersUpdate)));
```

### Usage on Endpoints

```csharp
// Minimal API
app.MapGet("/orders", GetOrders)
    .RequireAuthorization(Permissions.OrdersRead);

app.MapPost("/orders", CreateOrder)
    .RequireAuthorization(Permissions.OrdersCreate);

app.MapDelete("/orders/{id}", DeleteOrder)
    .RequireAuthorization(Permissions.OrdersDelete);

// Controller
[ApiController]
[Route("api/orders")]
public sealed class OrdersController : ControllerBase
{
    [HttpGet]
    [HasPermission(Permissions.OrdersRead)]
    public async Task<IActionResult> GetOrders() { /* ... */ }

    [HttpPost]
    [HasPermission(Permissions.OrdersCreate)]
    public async Task<IActionResult> CreateOrder() { /* ... */ }

    [HttpDelete("{id}")]
    [HasPermission(Permissions.OrdersDelete)]
    public async Task<IActionResult> DeleteOrder(Guid id) { /* ... */ }
}
```

### Resource-Based Authorization

```csharp
// Requirement for resource ownership
public sealed class OrderOwnerRequirement : IAuthorizationRequirement { }

// Handler checks if user owns the resource
public sealed class OrderOwnerAuthorizationHandler
    : AuthorizationHandler<OrderOwnerRequirement, Order>
{
    protected override Task HandleRequirementAsync(
        AuthorizationHandlerContext context,
        OrderOwnerRequirement requirement,
        Order resource)
    {
        var userId = context.User
            .FindFirstValue(JwtRegisteredClaimNames.Sub);

        if (resource.CreatedBy == userId)
            context.Succeed(requirement);

        return Task.CompletedTask;
    }
}

// Usage in handler
internal sealed class UpdateOrderHandler(
    IOrderRepository repository,
    IAuthorizationService authorizationService,
    IHttpContextAccessor httpContextAccessor)
    : IRequestHandler<UpdateOrderCommand, Result>
{
    public async Task<Result> Handle(
        UpdateOrderCommand request, CancellationToken ct)
    {
        var order = await repository.FindAsync(request.OrderId, ct);
        if (order is null)
            return Result.Failure(Error.NotFound("Order.NotFound",
                "Order not found"));

        var user = httpContextAccessor.HttpContext!.User;
        var authResult = await authorizationService.AuthorizeAsync(
            user, order, new OrderOwnerRequirement());

        if (!authResult.Succeeded)
            return Result.Failure(Error.Forbidden("Order.Forbidden",
                "You can only update your own orders"));

        // Update order...
        return Result.Success();
    }
}
```

### Loading Permissions from Database

```csharp
// Alternative: load permissions from DB instead of JWT claims
public sealed class DbPermissionAuthorizationHandler(
    IServiceScopeFactory scopeFactory)
    : AuthorizationHandler<PermissionRequirement>
{
    protected override async Task HandleRequirementAsync(
        AuthorizationHandlerContext context,
        PermissionRequirement requirement)
    {
        var userId = context.User
            .FindFirstValue(JwtRegisteredClaimNames.Sub);
        if (userId is null) return;

        using var scope = scopeFactory.CreateScope();
        var db = scope.ServiceProvider
            .GetRequiredService<AppDbContext>();

        var hasPermission = await db.UserPermissions
            .AnyAsync(p =>
                p.UserId == Guid.Parse(userId) &&
                p.Permission == requirement.Permission);

        if (hasPermission)
            context.Succeed(requirement);
    }
}
```

## Anti-Patterns

- Hardcoding role checks everywhere (`User.IsInRole("Admin")`)
- Checking permissions in controllers instead of using policies
- Not registering `IAuthorizationPolicyProvider` for dynamic policies
- Storing all permissions in JWT (bloats token — consider DB lookup for large sets)
- Missing authorization on endpoints (default should be authenticated)

## Detect Existing Patterns

1. Search for custom `AuthorizeAttribute` subclasses
2. Look for `IAuthorizationPolicyProvider` implementations
3. Check for `IAuthorizationHandler` implementations
4. Search for `"permissions"` claim in token generation
5. Look for `RequireAuthorization` calls on endpoints

## Adding to Existing Project

1. **Define permission constants** for all protected operations
2. **Create `HasPermissionAttribute`** and requirement/handler pair
3. **Register dynamic policy provider** for permission-based auth
4. **Add permissions to JWT claims** or implement DB-based permission lookup
5. **Apply `[HasPermission]`** or `RequireAuthorization` to all endpoints
6. **Add resource-based authorization** for entity ownership checks

## References

- https://learn.microsoft.com/en-us/aspnet/core/security/authorization/policies
- https://learn.microsoft.com/en-us/aspnet/core/security/authorization/resourcebased
