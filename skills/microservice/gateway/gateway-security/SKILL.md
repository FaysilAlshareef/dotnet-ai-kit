---
name: gateway-security
description: >
  Use when configuring JWT auth, authorization policies, or role-based access on gateway endpoints.
metadata:
  category: microservice/gateway
  agent: gateway-architect
  when-to-use: "When configuring gateway JWT authentication, authorization policies, or role-based access"
---

# Gateway Security — Authentication & Authorization

## Core Principles

- `AddJwtAuthentication(configuration)` registers JWT Bearer from `Jwt` config section
- `AddPolicies(ApiScope)` registers all authorization policies and handlers
- `ApiScope` enum determines the scope claim value (`Consumer`, `PublicConsumer`, `Management`)
- `Policy` constants class defines policy names used in `[Authorize(Policy = ...)]`
- `Roles` constants class defines role names used in `[Authorize(Roles = ...)]`
- Custom `IAuthorizationRequirement` + `AuthorizationHandler<T>` for complex policies
- Authorization handlers are registered as `AddScoped<IAuthorizationHandler, T>()`
- Controllers apply `[Authorize]`, `[Authorize(Policy = ...)]`, or `[Authorize(Roles = ...)]`

## Key Patterns

### AddJwtAuthentication Extension

Simple extension that configures JWT Bearer using `Authority` and `Audience` from the `Jwt` configuration section.

```csharp
using Microsoft.AspNetCore.Authentication.JwtBearer;

namespace {Company}.Gateways.Common.ServicesRegistration;

public static class AuthenticationRegistrar
{
    public static void AddJwtAuthentication(
        this IServiceCollection services, IConfiguration configuration)
    {
        services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
            .AddJwtBearer(JwtBearerDefaults.AuthenticationScheme, options =>
            {
                var jwtConfiguration = configuration.GetSection("Jwt");
                options.Authority = jwtConfiguration["JwtAuthority"];
                options.Audience = jwtConfiguration["JwtAudience"];
            });
    }
}
```

### ApiScope Enum

Determines which scope claim value is required for the `Consumer` policy. Each gateway type passes its own `ApiScope` at startup.

```csharp
namespace {Company}.Gateways.Common.Policies;

public enum ApiScope
{
    Consumer = 1,
    PublicConsumer = 2,
    Management = 3
}
```

### AddPolicies Extension with ApiScope

Registers all policies using `AddAuthorizationBuilder()` fluent API. The `Consumer` policy scope claim varies by `ApiScope`. Other policies use custom `IAuthorizationRequirement` types.

```csharp
using {Company}.Gateways.Common.Constants;
using {Company}.Gateways.Common.Policies;
using {Company}.Gateways.Common.Policies.Handlers;
using {Company}.Gateways.Common.Policies.Requirements;
using Microsoft.AspNetCore.Authorization;

namespace {Company}.Gateways.Common.ServicesRegistration;

public static class PoliciesRegistrationExtensions
{
    public static void AddPolicies(
        this IServiceCollection services, ApiScope apiScope)
    {
        services.AddAuthorizationBuilder()
            .AddPolicy(Policy.Consumer, p => p.RequireClaim("scope", apiScope switch
            {
                ApiScope.Consumer => "consumer",
                ApiScope.PublicConsumer => "public_consumer",
                ApiScope.Management => "management_scope",
                _ => throw new ArgumentOutOfRangeException(
                    nameof(apiScope), "Invalid api scope selected."),
            }))
            .AddPolicy(Policy.Operator, p =>
                p.AddRequirements(new OperatorRequirement()))
            .AddPolicy(Policy.Reporter, p =>
                p.AddRequirements(new ReporterRequirement()))
            .AddPolicy(Policy.Manager, p =>
                p.AddRequirements(new ManagerRequirement()))
            .AddPolicy(Policy.ManagerOrReporter, p =>
                p.AddRequirements(new ManagerOrReporterRequirement()))
            .AddPolicy(Policy.OperatorOrReporter, p =>
                p.AddRequirements(new OperatorOrReporterRequirement()))
            .AddPolicy(Policy.FinancialManager, p =>
                p.AddRequirements(new FinancialManagerRequirement()));

        services.AddScoped<IAuthorizationHandler, OperatorHandler>();
        services.AddScoped<IAuthorizationHandler, ReporterHandler>();
        services.AddScoped<IAuthorizationHandler, ManagerHandler>();
        services.AddScoped<IAuthorizationHandler, ManagerOrReporterHandler>();
        services.AddScoped<IAuthorizationHandler, OperatorOrReporterHandler>();
        services.AddScoped<IAuthorizationHandler, FinancialManagerHandler>();
    }
}
```

### Policy Constants

String constants used in `[Authorize(Policy = ...)]` attributes on controllers.

```csharp
namespace {Company}.Gateways.Common.Constants;

public class Policy
{
    public const string Manager = "Manager";
    public const string Operator = "Operator";
    public const string Reporter = "Reporter";
    public const string ManagerOrReporter = "ManagerOrReporter";
    public const string OperatorOrReporter = "OperatorOrReporter";
    public const string FinancialManager = "FinancialManager";
    public const string Consumer = "Consumer";
    public const string PublicConsumer = "PublicConsumer";
}
```

### Roles Constants

String constants used in `[Authorize(Roles = ...)]` attributes. Multiple roles are combined with commas via string interpolation.

```csharp
namespace {Company}.Gateways.Common.Constants;

public static class Roles
{
    public const string SuperAdmin = "SuperAdmin";
    public const string Admin = "Admin";
    public const string Manager = "Manager";
    public const string Reporter = "Reporter";
    public const string FinancialManager = "FinancialManager";
    public const string Developer = "Developer";
    public const string LeadDeveloper = "LeadDeveloper";
}
```

### Custom Authorization Requirement + Handler

Requirements are empty marker classes. Handlers resolve services from DI to perform complex authorization logic (e.g., checking subscriptions via gRPC).

```csharp
namespace {Company}.Gateways.Common.Policies.Requirements;

public class OperatorRequirement : IAuthorizationRequirement { }
```

```csharp
using {Company}.Gateways.Common.Constants;
using {Company}.Gateways.Common.Policies.Requirements;
using Microsoft.AspNetCore.Authorization;

namespace {Company}.Gateways.Common.Policies.Handlers;

public class OperatorHandler(
    SomeGrpcService grpcService) : AuthorizationHandler<OperatorRequirement>
{
    private readonly SomeGrpcService _grpcService = grpcService;

    protected override async Task HandleRequirementAsync(
        AuthorizationHandlerContext context, OperatorRequirement requirement)
    {
        if (context.User.IsInRole(Roles.Admin))
        {
            context.Succeed(requirement);
        }
        else
        {
            var isOperator = await _grpcService.HasPermissionAsync(
                userId: context.User.FindFirstValue(ClaimTypes.NameIdentifier));

            if (isOperator)
                context.Succeed(requirement);
        }
    }
}
```

### Controller Authorization — Three Patterns

```csharp
// Pattern 1: Default [Authorize] — requires authenticated user (from ControllerBaseV1)
[Route(DefaultRoute)]
[Authorize]
public class ProductsController(...) : ControllerBaseV1

// Pattern 2: Policy-based — requires specific policy
[Route(DefaultRoute)]
[Authorize(Policy = Policy.Operator)]
public class OrdersController(...) : ControllerBaseV1

// Pattern 3: Role-based — requires specific roles (comma-separated)
[Route(DefaultRoute)]
[Authorize(Roles = $"{Roles.SuperAdmin},{Roles.Admin}")]
public class AdminController(...) : ControllerBaseV1
```

### Program.cs Usage

```csharp
builder.Services.AddPolicies(ApiScope.Management);
builder.Services.AddJwtAuthentication(builder.Configuration);

// ...

app.UseAuthentication();
app.UseAuthorization();
```

### appsettings.json

```json
{
  "Jwt": {
    "JwtAuthority": "https://identity.example.com",
    "JwtAudience": "gateway-api"
  }
}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Hardcoded roles in `[Authorize]` strings | Use `Roles` constants class |
| Hardcoded policy names in attributes | Use `Policy` constants class |
| Combining auth setup in one method | Separate `AddJwtAuthentication` and `AddPolicies` |
| Registering handlers as Singleton | Register as `AddScoped` (handlers may use scoped services) |
| Missing `UseAuthentication` before `UseAuthorization` | Order matters in middleware pipeline |
| Complex logic in controller actions | Move to `AuthorizationHandler<T>` |

## Detect Existing Patterns

```bash
# Find authentication setup
grep -r "AddJwtAuthentication\|AddAuthentication" --include="*.cs"

# Find policy registration
grep -r "AddPolicies\|AddAuthorizationBuilder" --include="*.cs"

# Find Authorize attributes
grep -r "\[Authorize" --include="*.cs" Controllers/

# Find policy/role constants
grep -r "class Policy\|class Roles" --include="*.cs"

# Find authorization handlers
grep -r "AuthorizationHandler<" --include="*.cs"
```

## Adding to Existing Project

1. **Check `ApiScope`** passed in `AddPolicies` to understand the gateway type
2. **Add new policy** in `AddPolicies` with a new `IAuthorizationRequirement`
3. **Create handler** inheriting `AuthorizationHandler<TRequirement>`
4. **Register handler** as `AddScoped<IAuthorizationHandler, THandler>()`
5. **Add constant** to `Policy` class for the new policy name
6. **Apply `[Authorize(Policy = ...)]`** on controller or action
7. **For role-based**: add constant to `Roles` class and use `[Authorize(Roles = ...)]`
