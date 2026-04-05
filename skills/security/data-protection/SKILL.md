---
name: data-protection
description: >
  ASP.NET Core Data Protection API for encryption at rest, key management,
  secure cookie protection, and sensitive data handling.
  Trigger: data protection, encryption, protect, unprotect, key management, DPAPI.
metadata:
  category: security
  agent: api-designer
  when-to-use: "When implementing data encryption, key management, or Data Protection API"
---

# Data Protection API

## Core Principles

- Use the Data Protection API for encrypting sensitive data at rest
- Keys are automatically managed (rotation, expiration) by the framework
- Purpose strings isolate protected data between different components
- Configure key storage for distributed environments (shared file, Redis, Azure)
- Use time-limited protection for tokens and links with automatic expiration

## Patterns

### Basic Data Protection

```csharp
// Program.cs — configure data protection
builder.Services.AddDataProtection()
    .SetApplicationName("{Company}.{Domain}")
    .SetDefaultKeyLifetime(TimeSpan.FromDays(90));

// Injecting and using
public sealed class SensitiveDataService(
    IDataProtectionProvider protectionProvider)
{
    private readonly IDataProtector _protector =
        protectionProvider.CreateProtector("SensitiveData.v1");

    public string Protect(string plainText)
        => _protector.Protect(plainText);

    public string Unprotect(string protectedText)
        => _protector.Unprotect(protectedText);
}
```

### Purpose-Isolated Protectors

```csharp
public sealed class TokenProtectionService(
    IDataProtectionProvider provider)
{
    // Each purpose creates an isolated encryption scope
    private readonly IDataProtector _emailConfirmation =
        provider.CreateProtector("EmailConfirmation");

    private readonly IDataProtector _passwordReset =
        provider.CreateProtector("PasswordReset");

    private readonly IDataProtector _apiKeys =
        provider.CreateProtector("ApiKeys.v1");

    public string ProtectEmailToken(string userId)
        => _emailConfirmation.Protect(userId);

    public string UnprotectEmailToken(string token)
        => _emailConfirmation.Unprotect(token);

    public string ProtectApiKey(string keyData)
        => _apiKeys.Protect(keyData);
}
```

### Time-Limited Protection

```csharp
public sealed class TimeLimitedTokenService(
    IDataProtectionProvider provider)
{
    private readonly ITimeLimitedDataProtector _protector =
        provider.CreateProtector("TimeLimitedTokens")
            .ToTimeLimitedDataProtector();

    // Token expires after specified duration
    public string CreatePasswordResetToken(Guid userId)
    {
        var payload = userId.ToString();
        return _protector.Protect(
            payload,
            lifetime: TimeSpan.FromHours(1));
    }

    public Guid? ValidatePasswordResetToken(string token)
    {
        try
        {
            var payload = _protector.Unprotect(token);
            return Guid.Parse(payload);
        }
        catch (CryptographicException)
        {
            // Token is invalid or expired
            return null;
        }
    }

    public string CreateEmailConfirmationToken(string email)
    {
        return _protector.Protect(
            email,
            lifetime: TimeSpan.FromDays(7));
    }
}
```

### Distributed Key Storage

```csharp
// File system (shared network drive for web farm)
builder.Services.AddDataProtection()
    .SetApplicationName("{Company}.{Domain}")
    .PersistKeysToFileSystem(
        new DirectoryInfo(@"\\server\share\keys"));

// Redis
builder.Services.AddDataProtection()
    .SetApplicationName("{Company}.{Domain}")
    .PersistKeysToStackExchangeRedis(
        ConnectionMultiplexer.Connect(
            builder.Configuration.GetConnectionString("Redis")!),
        "DataProtection-Keys");

// Azure Blob Storage + Key Vault
builder.Services.AddDataProtection()
    .SetApplicationName("{Company}.{Domain}")
    .PersistKeysToAzureBlobStorage(blobUri)
    .ProtectKeysWithAzureKeyVault(keyIdentifier, credential);
```

### Encrypting Sensitive Database Fields

```csharp
public sealed class EncryptedFieldConverter(
    IDataProtector protector) : ValueConverter<string, string>(
        v => protector.Protect(v),
        v => protector.Unprotect(v))
{
}

// Entity configuration
internal sealed class CustomerConfiguration
    : IEntityTypeConfiguration<Customer>
{
    private readonly IDataProtector _protector;

    public CustomerConfiguration(IDataProtectionProvider provider)
    {
        _protector = provider.CreateProtector("Customer.SSN");
    }

    public void Configure(EntityTypeBuilder<Customer> builder)
    {
        builder.Property(c => c.SocialSecurityNumber)
            .HasConversion(
                v => _protector.Protect(v),
                v => _protector.Unprotect(v))
            .HasMaxLength(500); // encrypted value is longer
    }
}
```

### Protecting Cookies and Antiforgery

```csharp
// Data protection automatically protects:
// - Authentication cookies
// - Session cookies
// - Antiforgery tokens
// - TempData

// Custom cookie protection
builder.Services.AddAuthentication(
    CookieAuthenticationDefaults.AuthenticationScheme)
    .AddCookie(options =>
    {
        options.Cookie.Name = ".{Company}.Auth";
        options.Cookie.HttpOnly = true;
        options.Cookie.SecurePolicy = CookieSecurePolicy.Always;
        options.Cookie.SameSite = SameSiteMode.Strict;
    });
```

### Security Headers Middleware

```csharp
// Additional security hardening
app.UseHsts();
app.UseHttpsRedirection();

app.Use(async (context, next) =>
{
    context.Response.Headers.Append(
        "X-Content-Type-Options", "nosniff");
    context.Response.Headers.Append(
        "X-Frame-Options", "DENY");
    context.Response.Headers.Append(
        "Referrer-Policy", "strict-origin-when-cross-origin");
    context.Response.Headers.Append(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=()");
    await next();
});
```

## Anti-Patterns

- Rolling your own encryption (use Data Protection API)
- Storing unencrypted sensitive data (SSN, PII) in the database
- Sharing data protection keys across unrelated applications
- Not configuring key storage in distributed environments (keys are lost on restart)
- Ignoring `CryptographicException` from `Unprotect` (means tampering or expiry)
- Using the same purpose string for different protection contexts

## Detect Existing Patterns

1. Search for `AddDataProtection` in `Program.cs`
2. Look for `IDataProtectionProvider` or `IDataProtector` injection
3. Check for `PersistKeysToFileSystem` or `PersistKeysToStackExchangeRedis`
4. Look for `CryptographicException` handling
5. Check for `ToTimeLimitedDataProtector` usage

## Adding to Existing Project

1. **Configure Data Protection** in `Program.cs` with application name
2. **Set up key storage** appropriate to deployment (file, Redis, Azure)
3. **Create protection services** for each sensitive data category
4. **Use time-limited protection** for tokens and confirmation links
5. **Encrypt sensitive DB fields** using value converters
6. **Add security headers** middleware

## Decision Guide

| Scenario | Approach |
|----------|----------|
| Password reset tokens | Time-limited data protection |
| API key storage | Purpose-isolated data protector |
| Sensitive DB fields | Value converter with data protector |
| Distributed web farm | Redis or Azure key storage |
| Single server | File system key storage |

## References

- https://learn.microsoft.com/en-us/aspnet/core/security/data-protection/introduction
- https://learn.microsoft.com/en-us/aspnet/core/security/data-protection/configuration/
