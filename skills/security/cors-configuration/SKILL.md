---
name: cors-configuration
description: >
  CORS policy configuration for .NET APIs — named policies, origin/method/header control,
  credentials handling, per-endpoint CORS, preflight caching, and common mistakes.
  Trigger: CORS, cross-origin, AddCors, AllowOrigins, preflight, Access-Control.
metadata:
  category: security
  agent: api-designer
  when-to-use: "When configuring CORS policies, allowed origins, or preflight request handling"
---

# CORS Configuration

## Core Principles

- **Least privilege**: only allow the origins, methods, and headers your clients actually need
- **Explicit origins**: list specific origins instead of wildcards — `AllowAnyOrigin()` disables the browser's same-origin protection
- **Never wildcard with credentials**: the CORS spec forbids `Access-Control-Allow-Origin: *` when `Access-Control-Allow-Credentials: true` — browsers will block the response
- **Defense in depth**: CORS is a browser-enforced mechanism, not a server-side security boundary — always validate and authorize on the server regardless
- **Middleware order matters**: `UseCors()` must appear after `UseRouting()` and before `UseAuthentication()` / `UseAuthorization()`

## When to Use

- Your API is consumed by a browser-based SPA hosted on a different origin
- You expose public endpoints that third-party front-ends call
- Your development server runs on a different port than the API (e.g., Vite on `:5173`, API on `:5000`)
- You need to allow cross-origin file uploads or custom headers

## When NOT to Use

- Server-to-server communication (CORS is browser-only; it adds no value)
- Your SPA and API share the same origin (same scheme + host + port)
- You use a reverse proxy / API gateway that already handles CORS headers before traffic reaches .NET
- Mobile apps or desktop clients (they do not enforce CORS)

## Patterns

### Basic Setup

```csharp
// Program.cs
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy
            .WithOrigins("https://app.example.com")
            .WithMethods("GET", "POST", "PUT", "DELETE")
            .WithHeaders("Content-Type", "Authorization");
    });
});

var app = builder.Build();

app.UseRouting();
app.UseCors();          // after UseRouting, before UseAuth
app.UseAuthentication();
app.UseAuthorization();
```

### Named Policies

Use named policies when different endpoint groups need different CORS rules.

```csharp
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowSPA", policy =>
        policy
            .WithOrigins(
                "https://app.example.com",
                "https://staging.example.com")
            .WithMethods("GET", "POST", "PUT", "DELETE")
            .WithHeaders(
                "Content-Type",
                "Authorization",
                "X-Request-Id"));

    options.AddPolicy("AllowReporting", policy =>
        policy
            .WithOrigins("https://reports.example.com")
            .WithMethods("GET")
            .WithHeaders("Authorization"));

    options.AddPolicy("AllowPublic", policy =>
        policy
            .AllowAnyOrigin()
            .WithMethods("GET")
            .WithHeaders("Content-Type"));
});
```

### Credentials

When your SPA sends cookies or `Authorization` headers with `credentials: "include"`, you must explicitly allow credentials. This is **incompatible** with `AllowAnyOrigin()`.

```csharp
options.AddPolicy("AllowSPAWithCredentials", policy =>
    policy
        .WithOrigins("https://app.example.com")
        .WithMethods("GET", "POST", "PUT", "DELETE")
        .WithHeaders("Content-Type", "Authorization")
        .AllowCredentials());
```

If you need to support multiple subdomains dynamically while still using credentials, use `SetIsOriginAllowed`:

```csharp
options.AddPolicy("AllowSubdomains", policy =>
    policy
        .SetIsOriginAllowed(origin =>
        {
            var host = new Uri(origin).Host;
            return host == "example.com"
                || host.EndsWith(".example.com",
                    StringComparison.OrdinalIgnoreCase);
        })
        .AllowCredentials()
        .WithMethods("GET", "POST", "PUT", "DELETE")
        .WithHeaders("Content-Type", "Authorization"));
```

### Per-Endpoint CORS

Apply named policies to specific endpoint groups instead of globally.

```csharp
// Minimal API — RequireCors on a group
var api = app.MapGroup("/api")
    .RequireCors("AllowSPA");

api.MapGet("/orders", GetOrders);
api.MapPost("/orders", CreateOrder);

// Public health check — different policy
app.MapGet("/health", () => Results.Ok("Healthy"))
    .RequireCors("AllowPublic");
```

With controllers, use the `[EnableCors]` attribute:

```csharp
[ApiController]
[Route("api/[controller]")]
[EnableCors("AllowSPA")]
public class OrdersController : ControllerBase
{
    // All actions inherit "AllowSPA"

    [DisableCors]
    [HttpGet("internal-status")]
    public IActionResult InternalStatus() => Ok();
}
```

### Preflight Caching

Browsers send an `OPTIONS` preflight request before non-simple cross-origin requests. Cache the preflight response to avoid redundant round-trips.

```csharp
options.AddPolicy("AllowSPA", policy =>
    policy
        .WithOrigins("https://app.example.com")
        .WithMethods("GET", "POST", "PUT", "DELETE")
        .WithHeaders("Content-Type", "Authorization")
        .SetPreflightMaxAge(TimeSpan.FromHours(1)));
```

- Default browser preflight cache: 5 seconds
- Recommended: 1-2 hours for stable APIs
- Maximum respected by most browsers: ~2 hours (Chrome caps at 7200s)

### Development vs Production

Use environment-specific CORS configuration so development is convenient while production stays locked down.

```csharp
if (builder.Environment.IsDevelopment())
{
    builder.Services.AddCors(options =>
    {
        options.AddDefaultPolicy(policy =>
            policy
                .WithOrigins(
                    "https://localhost:5173",
                    "http://localhost:5173",
                    "https://localhost:3000")
                .AllowAnyMethod()
                .AllowAnyHeader()
                .AllowCredentials());
    });
}
else
{
    var allowedOrigins = builder.Configuration
        .GetSection("Cors:AllowedOrigins")
        .Get<string[]>() ?? [];

    builder.Services.AddCors(options =>
    {
        options.AddDefaultPolicy(policy =>
            policy
                .WithOrigins(allowedOrigins)
                .WithMethods("GET", "POST", "PUT", "DELETE")
                .WithHeaders(
                    "Content-Type",
                    "Authorization",
                    "X-Request-Id")
                .AllowCredentials()
                .SetPreflightMaxAge(
                    TimeSpan.FromHours(1)));
    });
}
```

```json
// appsettings.Production.json
{
  "Cors": {
    "AllowedOrigins": [
      "https://app.example.com",
      "https://admin.example.com"
    ]
  }
}
```

### CORS Options Class

For complex projects, bind CORS configuration to a strongly-typed options class.

```csharp
public sealed class CorsOptions
{
    public const string SectionName = "Cors";

    public string[] AllowedOrigins { get; init; } = [];
    public string[] AllowedMethods { get; init; } =
        ["GET", "POST", "PUT", "DELETE"];
    public string[] AllowedHeaders { get; init; } =
        ["Content-Type", "Authorization"];
    public bool AllowCredentials { get; init; } = true;
    public int PreflightMaxAgeSeconds { get; init; } = 3600;
}

// Registration
var corsConfig = builder.Configuration
    .GetSection(CorsOptions.SectionName)
    .Get<CorsOptions>() ?? new CorsOptions();

builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy
            .WithOrigins(corsConfig.AllowedOrigins)
            .WithMethods(corsConfig.AllowedMethods)
            .WithHeaders(corsConfig.AllowedHeaders)
            .SetPreflightMaxAge(
                TimeSpan.FromSeconds(
                    corsConfig.PreflightMaxAgeSeconds));

        if (corsConfig.AllowCredentials)
            policy.AllowCredentials();
    });
});
```

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| `AllowAnyOrigin()` + `AllowCredentials()` | CORS spec violation — browsers block the response | Use `WithOrigins(...)` with explicit origins when credentials are needed |
| `UseCors()` after `UseAuthorization()` | CORS middleware never runs for unauthorized preflight requests, returning 401 | Place `UseCors()` before `UseAuthentication()` and `UseAuthorization()` |
| Origins with trailing slash | `https://app.example.com/` does not match `https://app.example.com` | Remove trailing slashes from all origin strings |
| Hardcoded `localhost` origins in production | Opens your API to any local dev machine | Use environment-conditional configuration (see Development vs Production) |
| Missing `OPTIONS` method in `WithMethods()` | Not needed — the CORS middleware handles preflight `OPTIONS` automatically | Do not add `OPTIONS` to `WithMethods()`; it is implicit |
| `AllowAnyOrigin()` on authenticated endpoints | Any website can make authenticated requests on behalf of your users | Restrict to known origins |
| Wildcard headers with `AllowAnyHeader()` | Exposes your API to unexpected custom headers | List only the headers your clients actually send |
| Not exposing response headers | Client JavaScript cannot read custom response headers unless exposed | Use `WithExposedHeaders("X-Pagination", "X-Request-Id")` |
| Duplicating CORS headers in both middleware and reverse proxy | Browsers reject responses with duplicate `Access-Control-Allow-Origin` | Configure CORS in exactly one layer |

## Decision Guide

| Scenario | Policy Configuration |
|----------|---------------------|
| Single SPA, same domain, different port (dev) | Default policy, `WithOrigins("https://localhost:PORT")`, `AllowCredentials()` |
| Single SPA, different domain (prod) | Default policy, `WithOrigins("https://app.example.com")`, `AllowCredentials()` |
| Multiple SPAs, different domains | Named policies per SPA group, `RequireCors("PolicyName")` per endpoint group |
| Public read-only API | `AllowAnyOrigin()`, `WithMethods("GET")`, no credentials |
| Subdomain wildcard | `SetIsOriginAllowed()` with domain suffix check, `AllowCredentials()` |
| Server-to-server only | No CORS configuration needed |
| API gateway handles CORS | No CORS in .NET — configure at the gateway layer only |
| Mixed public + authenticated endpoints | Named policies: one restrictive with credentials, one permissive without |

## Anti-Patterns

| Anti-Pattern | Why It Is Harmful | Better Approach |
|-------------|-------------------|-----------------|
| `AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader()` | Effectively disables CORS protection entirely | Specify exact origins, methods, and headers |
| `SetIsOriginAllowed(_ => true)` | Equivalent to `AllowAnyOrigin()` but bypasses the wildcard-credentials check — worst of both worlds | Validate the origin against an allowlist or domain pattern |
| Copying CORS config from Stack Overflow without reviewing | Most SO answers use `AllowAny*` for simplicity — not production-safe | Follow least-privilege principle for each policy |
| One global permissive policy for all endpoints | Public endpoints and authenticated endpoints have different threat models | Use named policies and apply per-group |
| Relying on CORS as an authentication mechanism | CORS is browser-enforced only — curl, Postman, and servers ignore it | Always enforce server-side authentication and authorization |
| Adding CORS headers manually via middleware | Bypasses the built-in CORS negotiation logic and is error-prone | Use `AddCors()` and `UseCors()` exclusively |

## Detect Existing Patterns

1. Search for `AddCors` in `Program.cs` or `Startup.cs`
2. Look for `UseCors` in the middleware pipeline
3. Check for `[EnableCors]` or `[DisableCors]` attributes on controllers
4. Search for `RequireCors` on minimal API endpoint groups
5. Look for manual `Access-Control-Allow-Origin` header manipulation
6. Check reverse proxy config (nginx, YARP, Azure Front Door) for existing CORS headers

## Adding to Existing Project

1. **Audit current origins**: identify every front-end domain that calls the API
2. **Add `AddCors()`** with named policies matching your endpoint groups
3. **Place `UseCors()`** in the correct middleware position (after routing, before auth)
4. **Apply per-endpoint policies** using `RequireCors()` or `[EnableCors()]`
5. **Set preflight cache** with `SetPreflightMaxAge` to reduce OPTIONS traffic
6. **Move allowed origins to configuration** so they differ between environments
7. **Verify with browser DevTools**: check the `Access-Control-*` response headers on preflight and actual requests

## References

- https://learn.microsoft.com/en-us/aspnet/core/security/cors
- https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
- https://fetch.spec.whatwg.org/#http-cors-protocol
