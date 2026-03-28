---
alwaysApply: true
description: Enforces strongly-typed configuration via the Options pattern with startup validation.
---

# Configuration Rules

Use strongly-typed Options classes for ALL configuration. Fail fast on invalid config.

## MUST

- Inject `IOptions<T>`, `IOptionsSnapshot<T>`, or `IOptionsMonitor<T>` — NEVER inject `IConfiguration` directly into services
- All options classes MUST call `ValidateDataAnnotations()` and `ValidateOnStart()`
- Options classes must declare `public const string SectionName` for the config section key
- Bind via `services.AddOptions<T>().BindConfiguration(T.SectionName)`
- Connection strings: wrap in an options class with `IOptions<T>` — do NOT use `GetConnectionString()` directly
- Default values must be set in the options class properties, not in appsettings.json

## MUST NOT

- Do not inject `IConfiguration` into service constructors — use `IOptions<T>` instead
- Do not use `configuration["Key"]` or `configuration.GetSection("Key")` in services
- Do not use hardcoded fallback values (e.g., `?? "https://localhost:5097"`) — fail fast on missing config
- Do not use `services.Configure<T>(configuration.GetSection(...))` without `ValidateOnStart()`
- Do not read `GetConnectionString()` directly — wrap in a typed options class
- Do not store secrets in `appsettings.json` — use user secrets (dev) or Key Vault (prod)

## Options Class Pattern

```csharp
public sealed class ServiceBusOptions
{
    public const string SectionName = "ServiceBus";

    [Required]
    public required string ConnectionString { get; init; }

    [Required]
    public required string TopicName { get; init; }

    [Range(1, 50)]
    public int MaxConcurrentCalls { get; init; } = 10;
}
```

## Registration Pattern

```csharp
builder.Services.AddOptions<ServiceBusOptions>()
    .BindConfiguration(ServiceBusOptions.SectionName)
    .ValidateDataAnnotations()
    .ValidateOnStart();
```

## Interface Selection

| Scenario | Interface |
|----------|-----------|
| Singleton service, read-once config | `IOptions<T>` |
| Scoped service, reload per request | `IOptionsSnapshot<T>` |
| Singleton that reacts to changes | `IOptionsMonitor<T>` |

## Detection Instructions

1. Search for `IConfiguration` injected into service constructors — replace with `IOptions<T>`
2. Check for `ValidateOnStart()` on all `AddOptions` calls — add if missing
3. Verify all options classes have `public const string SectionName`
4. Look for `?? "fallback"` patterns on config reads — remove and require config
5. Check for raw `GetConnectionString()` calls — wrap in typed options

## Related Skills
- `skills/core/dependency-injection/SKILL.md` — DI lifetimes, Options pattern integration
