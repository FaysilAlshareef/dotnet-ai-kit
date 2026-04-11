---
name: openapi-scalar
description: >
  Use when setting up OpenAPI spec generation or Scalar API documentation UI.
metadata:
  category: api
  agent: api-designer
  when-to-use: "When configuring OpenAPI spec generation or Scalar API documentation UI"
---

# OpenAPI & Scalar API Documentation

## Core Principles

- Use native `Microsoft.AspNetCore.OpenApi` (.NET 9+) instead of Swashbuckle
- Configure document transformers for metadata, security schemes, and customization
- Use Scalar as the modern API documentation UI replacement for Swagger UI
- Add OpenAPI metadata to every endpoint for accurate documentation
- Protect documentation endpoints in production

## Patterns

### Native OpenAPI Setup (.NET 9+)

```csharp
// Program.cs
builder.Services.AddOpenApi("v1", options =>
{
    options.AddDocumentTransformer((document, context, ct) =>
    {
        document.Info = new OpenApiInfo
        {
            Title = "{Domain} API",
            Version = "v1",
            Description = "API for {Company} {Domain} management"
        };
        return Task.CompletedTask;
    });

    // Add JWT security scheme
    options.AddDocumentTransformer<BearerSecuritySchemeTransformer>();
});
```

### Bearer Security Scheme Transformer

```csharp
internal sealed class BearerSecuritySchemeTransformer(
    IAuthenticationSchemeProvider schemeProvider)
    : IOpenApiDocumentTransformer
{
    public async Task TransformAsync(
        OpenApiDocument document,
        OpenApiDocumentTransformerContext context,
        CancellationToken ct)
    {
        var schemes = await schemeProvider.GetAllSchemesAsync();
        if (schemes.Any(s =>
            s.Name == JwtBearerDefaults.AuthenticationScheme))
        {
            document.Components ??= new OpenApiComponents();
            document.Components.SecuritySchemes["Bearer"] =
                new OpenApiSecurityScheme
                {
                    Type = SecuritySchemeType.Http,
                    Scheme = "bearer",
                    BearerFormat = "JWT",
                    Description = "Enter JWT token"
                };
        }
    }
}
```

### Scalar UI Configuration

```csharp
// Install: Scalar.AspNetCore

// Development setup
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
    app.MapScalarApiReference(options =>
    {
        options
            .WithTitle("{Domain} API")
            .WithTheme(ScalarTheme.BluePlanet)
            .WithDefaultHttpClient(
                ScalarTarget.CSharp, ScalarClient.HttpClient)
            .WithPreferredScheme("Bearer")
            .WithHttpBearerAuthentication(bearer =>
            {
                bearer.Token = "your-dev-token-here";
            });
    });
}

// Production with auth protection
if (!app.Environment.IsDevelopment())
{
    app.MapOpenApi()
        .RequireAuthorization("ApiDocAccess");
    app.MapScalarApiReference()
        .RequireAuthorization("ApiDocAccess");
}
```

### Versioned API Documents

```csharp
// Register multiple OpenAPI documents
builder.Services.AddOpenApi("v1", options =>
{
    options.AddDocumentTransformer((doc, _, _) =>
    {
        doc.Info.Title = "{Domain} API v1";
        doc.Info.Version = "1.0";
        return Task.CompletedTask;
    });
});

builder.Services.AddOpenApi("v2", options =>
{
    options.AddDocumentTransformer((doc, _, _) =>
    {
        doc.Info.Title = "{Domain} API v2";
        doc.Info.Version = "2.0";
        return Task.CompletedTask;
    });
});

// Map both documents
app.MapOpenApi(); // serves /openapi/v1.json and /openapi/v2.json
```

### Endpoint Metadata

```csharp
// Minimal API metadata
app.MapGet("/orders/{id}", GetOrder)
    .WithSummary("Get order by ID")
    .WithDescription("Returns full order details including line items")
    .Produces<OrderResponse>(StatusCodes.Status200OK)
    .Produces(StatusCodes.Status404NotFound)
    .WithTags("Orders");

// Controller metadata
[HttpGet("{id:guid}")]
[EndpointSummary("Get order by ID")]
[EndpointDescription("Returns full order details")]
[ProducesResponseType(typeof(OrderResponse), StatusCodes.Status200OK)]
[ProducesResponseType(StatusCodes.Status404NotFound)]
public async Task<ActionResult<OrderResponse>> GetOrder(Guid id) { }
```

### Build-Time Document Generation

```xml
<!-- Generate OpenAPI spec at build time for CI -->
<PackageReference Include="Microsoft.Extensions.ApiDescription.Server" />
```

```bash
# Generate OpenAPI document at build time
dotnet build
# Output: obj/ApiDescription/v1.json
```

## Anti-Patterns

- Using Swashbuckle with .NET 9+ (use native OpenAPI instead)
- Missing security scheme documentation
- No endpoint summaries or descriptions
- Exposing API docs without auth in production
- Hardcoding server URLs in OpenAPI document

## Detect Existing Patterns

1. Search for `AddOpenApi` in `Program.cs` (native .NET 9+)
2. Search for `AddSwaggerGen` (Swashbuckle — legacy, migration candidate)
3. Check for `Scalar.AspNetCore` package in `.csproj`
4. Look for `MapScalarApiReference` or `MapSwagger` calls
5. Check for `Microsoft.AspNetCore.OpenApi` package reference

## Adding to Existing Project

1. **Replace Swashbuckle** with `Microsoft.AspNetCore.OpenApi` (if on .NET 9+)
2. **Add Scalar** — `dotnet add package Scalar.AspNetCore`
3. **Configure OpenAPI** with document transformers for metadata
4. **Add security scheme** transformer for JWT/API key
5. **Add metadata** to all endpoints (`WithSummary`, `WithTags`)
6. **Protect docs** in production with authorization

## Migration from Swashbuckle

```csharp
// BEFORE (Swashbuckle)
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo { Title = "My API" });
});
app.UseSwagger();
app.UseSwaggerUI();

// AFTER (Native OpenAPI + Scalar)
builder.Services.AddOpenApi("v1", options =>
{
    options.AddDocumentTransformer((doc, _, _) =>
    {
        doc.Info.Title = "My API";
        return Task.CompletedTask;
    });
});
app.MapOpenApi();
app.MapScalarApiReference();
```

## References

- https://learn.microsoft.com/en-us/aspnet/core/fundamentals/openapi/overview
- https://github.com/scalar/scalar/tree/main/integrations/aspnetcore
