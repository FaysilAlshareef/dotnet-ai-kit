---
name: versioning
description: >
  Use when adding API versioning or managing multiple API versions in a .NET project.
metadata:
  category: api
  agent: api-designer
  when-to-use: "When configuring API versioning strategies or sunset policies"
---

# API Versioning

## Core Principles

- Version APIs from the start — retrofitting is painful
- URL segment versioning (`/api/v1/orders`) is the most common and recommended
- Report available and deprecated versions via response headers
- Maintain backward compatibility within a version
- Use sunset policies to communicate deprecation timelines

## Patterns

### URL Segment Versioning (Recommended)

```csharp
// Program.cs
builder.Services.AddApiVersioning(options =>
{
    options.DefaultApiVersion = new ApiVersion(1, 0);
    options.AssumeDefaultVersionWhenUnspecified = true;
    options.ReportApiVersions = true;
    options.ApiVersionReader = new UrlSegmentApiVersionReader();
})
.AddApiExplorer(options =>
{
    options.GroupNameFormat = "'v'VVV";
    options.SubstituteApiVersionInUrl = true;
});
```

### Controller Versioning

```csharp
[ApiController]
[Route("api/v{version:apiVersion}/orders")]
[ApiVersion("1.0")]
[ApiVersion("2.0")]
public sealed class OrdersController(ISender sender) : ControllerBase
{
    [HttpGet]
    [MapToApiVersion("1.0")]
    public async Task<ActionResult<List<OrderV1Response>>> GetOrdersV1(
        CancellationToken ct)
    {
        var result = await sender.Send(new ListOrdersV1Query(), ct);
        return Ok(result);
    }

    [HttpGet]
    [MapToApiVersion("2.0")]
    public async Task<ActionResult<PagedList<OrderV2Response>>> GetOrdersV2(
        [FromQuery] OrderFilter filter, CancellationToken ct)
    {
        var result = await sender.Send(new ListOrdersV2Query(filter), ct);
        return Ok(result);
    }
}

// Or separate controllers per version
[ApiController]
[Route("api/v{version:apiVersion}/orders")]
[ApiVersion("1.0", Deprecated = true)]
public sealed class OrdersV1Controller : ControllerBase { }

[ApiController]
[Route("api/v{version:apiVersion}/orders")]
[ApiVersion("2.0")]
public sealed class OrdersV2Controller : ControllerBase { }
```

### Minimal API Versioning

```csharp
var versionSet = app.NewApiVersionSet()
    .HasApiVersion(new ApiVersion(1, 0))
    .HasApiVersion(new ApiVersion(2, 0))
    .ReportApiVersions()
    .Build();

var v1 = app.MapGroup("/api/v{version:apiVersion}")
    .WithApiVersionSet(versionSet);

v1.MapGet("/orders", GetOrdersV1)
    .MapToApiVersion(new ApiVersion(1, 0));

v1.MapGet("/orders", GetOrdersV2)
    .MapToApiVersion(new ApiVersion(2, 0));
```

### Header Versioning (Alternative)

```csharp
builder.Services.AddApiVersioning(options =>
{
    options.ApiVersionReader = new HeaderApiVersionReader("X-Api-Version");
});

// Client sends: X-Api-Version: 2.0
```

### Query String Versioning (Alternative)

```csharp
builder.Services.AddApiVersioning(options =>
{
    options.ApiVersionReader = new QueryStringApiVersionReader("api-version");
});

// Client requests: /api/orders?api-version=2.0
```

### Combined Version Reader

```csharp
builder.Services.AddApiVersioning(options =>
{
    options.ApiVersionReader = ApiVersionReader.Combine(
        new UrlSegmentApiVersionReader(),
        new HeaderApiVersionReader("X-Api-Version"),
        new QueryStringApiVersionReader("api-version"));
});
```

### Sunset Policy

```csharp
builder.Services.AddApiVersioning(options =>
{
    options.Policies.Sunset(1.0)
        .Effective(new DateTimeOffset(2025, 6, 1, 0, 0, 0, TimeSpan.Zero))
        .Link("https://docs.{Company}.com/api/migration-guide")
            .Title("v1 to v2 Migration Guide")
            .Type("text/html");
});

// Response header: Sunset: Sat, 01 Jun 2025 00:00:00 GMT
// Response header: Link: <https://docs.{Company}.com/api/migration-guide>; ...
```

### OpenAPI Document Per Version

```csharp
builder.Services.AddOpenApi("v1");
builder.Services.AddOpenApi("v2");

// Each document at /openapi/v1.json and /openapi/v2.json
app.MapOpenApi();
```

## Anti-Patterns

- Not versioning from the start (forces breaking changes on clients)
- Using version in the response body instead of URL/header
- Major behavior changes within the same version
- Forgetting to deprecate old versions
- Different versioning strategies across the same API

## Detect Existing Patterns

1. Search for `Asp.Versioning` package reference in `.csproj`
2. Look for `AddApiVersioning` in `Program.cs`
3. Check for `[ApiVersion]` attributes on controllers
4. Look for `v{version:apiVersion}` in route templates
5. Check for version query parameters in existing URLs

## Adding to Existing Project

1. **Install** `Asp.Versioning.Http` (minimal API) or `Asp.Versioning.Mvc.ApiExplorer` (controllers)
2. **Configure** `AddApiVersioning` with default version and reader
3. **Add `[ApiVersion]`** to existing controllers (start with `"1.0"`)
4. **Update routes** to include version segment
5. **Create v2 endpoints** for new behavior; keep v1 for backward compat
6. **Add sunset policies** for deprecated versions

## Decision Guide

| Strategy | Pros | Cons | Use When |
|----------|------|------|----------|
| URL segment | Visible, cacheable, simple | Version in URL | Default choice |
| Header | Clean URLs | Hidden, harder to test | Internal APIs |
| Query string | Easy to add | Pollutes query params | Legacy compat |

## References

- https://github.com/dotnet/aspnet-api-versioning
- https://learn.microsoft.com/en-us/aspnet/core/web-api/advanced/custom-formatters
