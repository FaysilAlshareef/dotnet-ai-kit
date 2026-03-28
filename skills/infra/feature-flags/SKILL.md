---
name: feature-flags
description: >
  Feature flag management with Microsoft.FeatureManagement — toggle patterns, percentage rollouts,
  time windows, custom filters, and Azure App Configuration integration.
  Trigger: feature flag, feature toggle, feature gate, FeatureManagement, feature rollout.
metadata:
  category: infra
  agent: dotnet-architect
---

# Feature Flags — Microsoft.FeatureManagement

## Core Principles

- **Decouple deployment from release** — ship code behind flags, enable when ready
- **Gradual rollout** — percentage-based filters expose features to a subset of users first
- **Kill switch** — disable a misbehaving feature instantly without redeployment
- **Short-lived by design** — every flag should have a planned removal date
- **Configuration-driven** — flags live in appsettings.json or Azure App Configuration, not in code

## When to Use

- Rolling out a new feature incrementally to production users
- A/B testing or canary releases controlled by targeting filters
- Providing an emergency kill switch for risky functionality
- Trunk-based development where incomplete features merge behind gates
- Time-boxed promotions or seasonal functionality with scheduled windows

## When NOT to Use

- Permanent application settings — use `IOptions<T>` and configuration instead
- Environment-specific behavior (dev vs prod) — use environment configuration
- Authorization and access control — use ASP.NET Core policies and claims
- Simple on/off toggles that never change at runtime — use compile-time constants

## Key Patterns

### NuGet Packages

```xml
<PackageReference Include="Microsoft.FeatureManagement.AspNetCore" Version="4.*" />
<!-- For Azure App Configuration integration -->
<PackageReference Include="Microsoft.Azure.AppConfiguration.AspNetCore" Version="8.*" />
```

### Feature Flag Names as Constants

```csharp
namespace {Company}.{Domain}.Infrastructure.Features;

/// <summary>
/// Centralized feature flag names. Every flag must have a removal target date in the summary.
/// </summary>
public static class FeatureFlags
{
    /// <summary>New dashboard UI. Target removal: 2026-Q2.</summary>
    public const string NewDashboard = "NewDashboard";

    /// <summary>Bulk export capability. Target removal: 2026-Q3.</summary>
    public const string BulkExport = "BulkExport";

    /// <summary>AI-powered recommendations. Target removal: 2026-Q2.</summary>
    public const string AiRecommendations = "AiRecommendations";
}
```

### Registration in Program.cs

```csharp
// Program.cs
builder.Services.AddFeatureManagement()
    .AddFeatureFilter<PercentageFilter>()
    .AddFeatureFilter<TimeWindowFilter>()
    .AddFeatureFilter<TargetingFilter>();
```

### IFeatureManager Injection

```csharp
namespace {Company}.{Domain}.Application.Orders;

public sealed class PlaceOrderHandler(
    IFeatureManager featureManager,
    IOrderRepository orders,
    IRecommendationEngine recommendations,
    ILogger<PlaceOrderHandler> logger)
{
    public async Task<OrderResult> HandleAsync(PlaceOrderCommand command, CancellationToken ct)
    {
        var order = Order.Create(command.CustomerId, command.Items);
        await orders.AddAsync(order, ct);

        if (await featureManager.IsEnabledAsync(FeatureFlags.AiRecommendations))
        {
            logger.LogInformation("AI recommendations enabled for order {OrderId}", order.Id);
            var suggestions = await recommendations.GetSuggestionsAsync(order, ct);
            order.AttachRecommendations(suggestions);
        }

        return new OrderResult(order.Id);
    }
}
```

### [FeatureGate] Attribute on Controllers

```csharp
namespace {Company}.{Domain}.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public sealed class ExportController(IExportService exportService) : ControllerBase
{
    [HttpPost("bulk")]
    [FeatureGate(FeatureFlags.BulkExport)]
    public async Task<IActionResult> BulkExportAsync(
        BulkExportRequest request, CancellationToken ct)
    {
        var result = await exportService.ExportAsync(request, ct);
        return Ok(result);
    }
}
```

### [FeatureGate] Attribute on Minimal API Endpoints

```csharp
// Program.cs — endpoint groups
var export = app.MapGroup("/api/export")
    .AddEndpointFilter<FeatureGateEndpointFilter>();

export.MapPost("/bulk", async (BulkExportRequest request, IExportService service, CancellationToken ct) =>
{
    var result = await service.ExportAsync(request, ct);
    return Results.Ok(result);
});
```

### appsettings.json Configuration

```json
{
  "FeatureManagement": {
    "NewDashboard": true,
    "BulkExport": false,
    "AiRecommendations": {
      "EnabledFor": [
        {
          "Name": "Percentage",
          "Parameters": {
            "Value": 25
          }
        }
      ]
    }
  }
}
```

Percentage rollout strategy: 10 -> 25 -> 50 -> 100 -> remove the flag.

### Time-Window Filter

```json
{
  "FeatureManagement": {
    "HolidayPromotion": {
      "EnabledFor": [
        {
          "Name": "TimeWindow",
          "Parameters": {
            "Start": "2026-12-20T00:00:00Z",
            "End": "2027-01-02T23:59:59Z"
          }
        }
      ]
    }
  }
}
```

### Targeting Filter (User/Group Rollout)

```json
{
  "FeatureManagement": {
    "NewDashboard": {
      "EnabledFor": [
        {
          "Name": "Targeting",
          "Parameters": {
            "Audience": {
              "Users": ["user-123", "user-456"],
              "Groups": [
                {
                  "Name": "BetaTesters",
                  "RolloutPercentage": 100
                },
                {
                  "Name": "InternalStaff",
                  "RolloutPercentage": 50
                }
              ],
              "DefaultRolloutPercentage": 5
            }
          }
        }
      ]
    }
  }
}
```

### Implement ITargetingContextAccessor

```csharp
namespace {Company}.{Domain}.Infrastructure.Features;

public sealed class HttpTargetingContextAccessor(
    IHttpContextAccessor httpContextAccessor) : ITargetingContextAccessor
{
    public ValueTask<TargetingContext> GetContextAsync()
    {
        var httpContext = httpContextAccessor.HttpContext
            ?? throw new InvalidOperationException("No active HTTP context.");

        var user = httpContext.User;
        var context = new TargetingContext
        {
            UserId = user.FindFirst(ClaimTypes.NameIdentifier)?.Value ?? "anonymous",
            Groups = user.FindAll("group").Select(c => c.Value).ToList()
        };

        return ValueTask.FromResult(context);
    }
}

// Register in Program.cs
builder.Services.AddSingleton<ITargetingContextAccessor, HttpTargetingContextAccessor>();
```

### Custom IFeatureFilter

```csharp
namespace {Company}.{Domain}.Infrastructure.Features;

[FilterAlias("TenantTier")]
public sealed class TenantTierFilter(
    ITenantContext tenantContext) : IFeatureFilter
{
    public Task<bool> EvaluateAsync(FeatureFilterEvaluationContext context)
    {
        var allowedTiers = context.Parameters
            .GetSection("AllowedTiers")
            .Get<string[]>() ?? [];

        var currentTier = tenantContext.CurrentTenant.Tier;
        return Task.FromResult(allowedTiers.Contains(currentTier, StringComparer.OrdinalIgnoreCase));
    }
}

// Registration
builder.Services.AddFeatureManagement()
    .AddFeatureFilter<TenantTierFilter>();
```

```json
{
  "FeatureManagement": {
    "AdvancedAnalytics": {
      "EnabledFor": [
        {
          "Name": "TenantTier",
          "Parameters": {
            "AllowedTiers": ["Premium", "Enterprise"]
          }
        }
      ]
    }
  }
}
```

### Azure App Configuration Integration

```csharp
// Program.cs
builder.Configuration.AddAzureAppConfiguration(options =>
{
    options.Connect(builder.Configuration.GetConnectionString("AppConfig"))
        .UseFeatureFlags(flagOptions =>
        {
            flagOptions.CacheExpirationInterval = TimeSpan.FromSeconds(30);
            flagOptions.Label = builder.Environment.EnvironmentName;
        });
});

builder.Services.AddAzureAppConfiguration();

// Middleware — must be early in pipeline
var app = builder.Build();
app.UseAzureAppConfiguration();
```

### Feature Flag Cleanup Strategy

```csharp
namespace {Company}.{Domain}.Infrastructure.Features;

/// <summary>
/// Run as a startup health check. Logs warnings for flags past their removal target.
/// </summary>
public sealed class FeatureFlagAuditService(
    IFeatureManager featureManager,
    ILogger<FeatureFlagAuditService> logger) : IHostedService
{
    private static readonly Dictionary<string, DateOnly> RemovalTargets = new()
    {
        [FeatureFlags.NewDashboard] = new DateOnly(2026, 6, 30),
        [FeatureFlags.BulkExport] = new DateOnly(2026, 9, 30),
        [FeatureFlags.AiRecommendations] = new DateOnly(2026, 6, 30),
    };

    public Task StartAsync(CancellationToken ct)
    {
        var today = DateOnly.FromDateTime(DateTime.UtcNow);

        foreach (var (flag, target) in RemovalTargets)
        {
            if (today > target)
            {
                logger.LogWarning(
                    "Feature flag '{Flag}' passed its removal target of {Target}. Schedule cleanup",
                    flag, target);
            }
        }

        return Task.CompletedTask;
    }

    public Task StopAsync(CancellationToken ct) => Task.CompletedTask;
}
```

## Decision Guide

| Scenario | Use Feature Flag | Use IOptions Config | Use Environment Variable |
|---|---|---|---|
| Gradual user rollout | Yes | No | No |
| Runtime on/off toggle | Yes | Possible | No |
| Per-environment behavior | No | Yes | Yes |
| Temporary A/B test | Yes | No | No |
| Connection strings / secrets | No | No | Yes (Key Vault) |
| Permanent business rule | No | Yes | No |
| Emergency kill switch | Yes | No | No |
| Seasonal / time-boxed feature | Yes (TimeWindow) | No | No |

## Anti-Patterns

| Anti-Pattern | Problem | Correct Approach |
|---|---|---|
| Permanent feature flags | Flag debt accumulates, dead code paths multiply | Set removal target date; audit with FeatureFlagAuditService |
| Flag names as magic strings | Typos cause silent failures | Centralize in a static FeatureFlags class with constants |
| Nested flag dependencies | Flag A depends on Flag B creates combinatorial complexity | Keep flags independent; compose at the feature level |
| Testing only the enabled path | Disabled path rots silently | Test both enabled and disabled paths in every flag scenario |
| Flags in domain logic | Domain layer couples to infrastructure | Evaluate flags in application/API layer, pass result to domain |
| No flag cleanup process | Codebase fills with obsolete gates | Track removal dates, run audit on startup, add to sprint hygiene |
| Using flags for authorization | Security decisions need proper policy enforcement | Use ASP.NET Core authorization policies and claims |
| Evaluating flags in tight loops | Repeated evaluation adds latency | Cache the result for the scope of the request |

## Detect Existing Patterns

```bash
# Find FeatureManagement usage
grep -r "IFeatureManager\|FeatureGate\|FeatureManagement" --include="*.cs" src/

# Find feature flag configuration
grep -r "FeatureManagement" --include="*.json" src/

# Find custom feature filters
grep -r ": IFeatureFilter" --include="*.cs" src/

# Find Azure App Configuration
grep -r "AddAzureAppConfiguration\|UseFeatureFlags" --include="*.cs" src/
```

## Adding to Existing Project

1. **Install the NuGet package** -- `Microsoft.FeatureManagement.AspNetCore`
2. **Create a FeatureFlags constants class** in Infrastructure/Features
3. **Register in Program.cs** with `AddFeatureManagement()` and required filters
4. **Add flag definitions** to appsettings.json under `FeatureManagement`
5. **For targeting**, implement `ITargetingContextAccessor` to resolve user/group context
6. **For Azure**, add `Microsoft.Azure.AppConfiguration.AspNetCore` and configure refresh
7. **Set removal targets** for every flag and wire up the audit hosted service
8. **Test both paths** -- verify behavior when flag is enabled and disabled
