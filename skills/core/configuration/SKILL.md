---
name: configuration
description: >
  IConfiguration, Options pattern, appsettings layering, user secrets,
  environment variables, and ValidateOnStart.
  Trigger: configuration, options, appsettings, secrets, IOptions, environment.
category: core
agent: dotnet-architect
---

# Configuration & Options Pattern

## Core Principles

- Use strongly-typed Options classes instead of reading IConfiguration directly
- Validate options at startup with `ValidateOnStart()` for fail-fast behavior
- Layer configuration: `appsettings.json` < `appsettings.{Environment}.json` < env vars < user secrets
- Never store secrets in `appsettings.json` — use user secrets (dev) or Key Vault (prod)
- Use `IOptions<T>` for singleton config, `IOptionsSnapshot<T>` for scoped reloading

## Patterns

### Options Class with Validation

```csharp
public sealed class DatabaseOptions
{
    public const string SectionName = "Database";

    [Required]
    public required string ConnectionString { get; init; }

    [Range(1, 100)]
    public int MaxRetryCount { get; init; } = 3;

    [Range(1, 3600)]
    public int CommandTimeoutSeconds { get; init; } = 30;
}

public sealed class JwtOptions
{
    public const string SectionName = "Jwt";

    [Required]
    public required string Issuer { get; init; }

    [Required]
    public required string Audience { get; init; }

    [Required, MinLength(32)]
    public required string Key { get; init; }

    [Range(1, 1440)]
    public int ExpiryMinutes { get; init; } = 60;
}
```

### Registration with ValidateOnStart

```csharp
// Program.cs — fail fast if configuration is invalid
builder.Services.AddOptions<DatabaseOptions>()
    .BindConfiguration(DatabaseOptions.SectionName)
    .ValidateDataAnnotations()
    .ValidateOnStart();

builder.Services.AddOptions<JwtOptions>()
    .BindConfiguration(JwtOptions.SectionName)
    .ValidateDataAnnotations()
    .ValidateOnStart();
```

### Complex Validation with IValidateOptions

```csharp
public sealed class DatabaseOptionsValidator : IValidateOptions<DatabaseOptions>
{
    public ValidateOptionsResult Validate(string? name, DatabaseOptions options)
    {
        var failures = new List<string>();

        if (options.ConnectionString.Contains("password=",
            StringComparison.OrdinalIgnoreCase)
            && !options.ConnectionString.Contains("Encrypt=true",
                StringComparison.OrdinalIgnoreCase))
        {
            failures.Add(
                "Connections with passwords must use Encrypt=true.");
        }

        return failures.Count > 0
            ? ValidateOptionsResult.Fail(failures)
            : ValidateOptionsResult.Success;
    }
}

// Register the validator
builder.Services.AddSingleton<
    IValidateOptions<DatabaseOptions>, DatabaseOptionsValidator>();
```

### IOptions vs IOptionsSnapshot vs IOptionsMonitor

```csharp
// Singleton — reads once at startup, never changes
public sealed class StartupService(IOptions<DatabaseOptions> options)
{
    private readonly DatabaseOptions _db = options.Value;
}

// Scoped — reloads per request when config changes (requires reloadOnChange)
public sealed class RequestService(IOptionsSnapshot<DatabaseOptions> options)
{
    private readonly DatabaseOptions _db = options.Value;
}

// Singleton — reloads and notifies on change
public sealed class MonitorService(IOptionsMonitor<DatabaseOptions> options)
{
    public MonitorService(IOptionsMonitor<DatabaseOptions> options)
    {
        options.OnChange(newOptions =>
        {
            // React to configuration changes
        });
    }
}
```

### appsettings Layering

```json
// appsettings.json — shared defaults
{
  "Database": {
    "MaxRetryCount": 3,
    "CommandTimeoutSeconds": 30
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information"
    }
  }
}
```

```json
// appsettings.Development.json — dev overrides
{
  "Database": {
    "ConnectionString": "Server=localhost;Database={Domain}Db;Trusted_Connection=true;TrustServerCertificate=true"
  }
}
```

### User Secrets (Development)

```bash
# Initialize user secrets
dotnet user-secrets init

# Set secrets
dotnet user-secrets set "Database:ConnectionString" "Server=localhost;..."
dotnet user-secrets set "Jwt:Key" "your-development-secret-key-min-32-chars"
```

### Environment Variables

```bash
# Environment variables use __ as section separator
Database__ConnectionString="Server=prod-server;..."
Jwt__Key="production-secret-key"
```

### Named Options

```csharp
// Multiple instances of the same options type
builder.Services.AddOptions<StorageOptions>("azure")
    .BindConfiguration("Storage:Azure")
    .ValidateDataAnnotations();

builder.Services.AddOptions<StorageOptions>("aws")
    .BindConfiguration("Storage:Aws")
    .ValidateDataAnnotations();

// Consuming named options
public sealed class StorageFactory(IOptionsSnapshot<StorageOptions> options)
{
    public IStorageClient Create(string provider)
    {
        var config = options.Get(provider);
        return provider switch
        {
            "azure" => new AzureBlobClient(config),
            "aws" => new S3Client(config),
            _ => throw new ArgumentException($"Unknown provider: {provider}")
        };
    }
}
```

## Anti-Patterns

```csharp
// BAD: Reading IConfiguration directly — not strongly typed
var connStr = configuration["Database:ConnectionString"];

// BAD: Secrets in appsettings.json
{
  "Jwt": { "Key": "super-secret-key-DO-NOT-COMMIT" }
}

// BAD: No validation — app fails at runtime with cryptic errors
services.Configure<DatabaseOptions>(
    configuration.GetSection("Database")); // no ValidateOnStart

// BAD: Using IOptions<T> when you need config reload
public class ReloadableService(IOptions<FeatureFlags> options) { }
// Should use IOptionsSnapshot or IOptionsMonitor
```

## Detect Existing Patterns

1. Search for `IOptions<`, `IOptionsSnapshot<`, `IOptionsMonitor<` in constructors
2. Check for `BindConfiguration` or `Bind` calls in `Program.cs`
3. Look for `ValidateOnStart` or `ValidateDataAnnotations` calls
4. Check `appsettings.json` for configuration sections
5. Look for direct `IConfiguration` reads (`configuration["Key"]`)
6. Check for `UserSecretsId` in `.csproj` (user secrets enabled)

## Adding to Existing Project

1. **Create Options classes** for each configuration section
2. **Replace direct IConfiguration reads** with `IOptions<T>` injection
3. **Add data annotation validation** and `ValidateOnStart()`
4. **Move secrets to user secrets** — `dotnet user-secrets init` then set values
5. **Add environment-specific appsettings** files if missing
6. **Add IValidateOptions** for complex cross-property validation

## Decision Guide

| Scenario | Interface | Notes |
|----------|-----------|-------|
| Singleton service needs config | `IOptions<T>` | Reads once |
| Scoped service needs live config | `IOptionsSnapshot<T>` | Reloads per scope |
| React to config changes | `IOptionsMonitor<T>` | Change callbacks |
| Multiple named configs | `IOptionsSnapshot<T>` with `.Get(name)` | Named options |
| Startup validation | `ValidateOnStart()` | Fail-fast |

## References

- https://learn.microsoft.com/en-us/dotnet/core/extensions/options
- https://learn.microsoft.com/en-us/aspnet/core/fundamentals/configuration/
- https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets
