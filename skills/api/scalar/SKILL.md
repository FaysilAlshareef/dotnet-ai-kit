---
name: dotnet-ai-scalar-api-docs
description: >
  Scalar API documentation setup for .NET. OpenAPI doc generation,
  Scalar UI configuration, basic auth protection, theme customization.
category: api
agent: api-designer
---

# Scalar API Documentation

## Setup (.NET 9+)

```csharp
namespace {Company}.{Domain}.Api.Extensions;

public static class OpenApiExtensions
{
    public static IServiceCollection AddOpenApiDocumentation(
        this IServiceCollection services, IWebHostEnvironment environment)
    {
        services.AddOpenApi("v1", options =>
        {
            options.AddDocumentTransformer<BearerSecuritySchemeTransformer>();
        });

        return services;
    }

    public static IApplicationBuilder UseOpenApiDocumentation(
        this IApplicationBuilder app, IWebHostEnvironment environment)
    {
        app.MapOpenApi();
        app.MapScalarApiReference(options =>
        {
            options
                .WithTitle("{Company} {Domain} API")
                .WithTheme(ScalarTheme.BluePlanet)
                .WithDefaultHttpClient(ScalarTarget.CSharp, ScalarClient.HttpClient);
        });

        return app;
    }
}
```

## Bearer Security Scheme Transformer

```csharp
internal sealed class BearerSecuritySchemeTransformer(
    IAuthenticationSchemeProvider provider)
    : IOpenApiDocumentTransformer
{
    public async Task TransformAsync(
        OpenApiDocument document,
        OpenApiDocumentTransformerContext context,
        CancellationToken ct)
    {
        var schemes = await provider.GetAllSchemesAsync();
        if (schemes.Any(s => s.Name == "Bearer"))
        {
            var requirements = new Dictionary<string, OpenApiSecurityScheme>
            {
                ["Bearer"] = new()
                {
                    Type = SecuritySchemeType.Http,
                    Scheme = "bearer",
                    BearerFormat = "JWT"
                }
            };
            document.Components ??= new();
            document.Components.SecuritySchemes = requirements;
        }
    }
}
```

## Basic Auth Protection (Production)

```csharp
namespace {Company}.Gateways.Common.Scalar;

public sealed class ScalarBasicAuthMiddleware(
    RequestDelegate next,
    IOptions<ScalarAuthorizationOptions> options)
{
    public async Task InvokeAsync(HttpContext context)
    {
        if (IsLocalRequest(context))
        {
            await next(context);
            return;
        }

        var authHeader = context.Request.Headers.Authorization.ToString();
        if (!ValidateBasicAuth(authHeader, options.Value))
        {
            context.Response.StatusCode = 401;
            context.Response.Headers.WWWAuthenticate = "Basic realm=\"API Docs\"";
            return;
        }

        await next(context);
    }

    private static bool IsLocalRequest(HttpContext context) =>
        IPAddress.IsLoopback(context.Connection.RemoteIpAddress!);
}
```

## Program.cs Integration

```csharp
builder.Services.AddOpenApiDocumentation(builder.Environment);

var app = builder.Build();
app.UseOpenApiDocumentation(app.Environment);
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Swagger UI for new projects | Use Scalar with `MapScalarApiReference` |
| Exposing docs without auth | Use `ScalarBasicAuthMiddleware` |
| Missing Bearer scheme | Add `BearerSecuritySchemeTransformer` |

## Detect Existing Patterns

```bash
grep -r "MapScalarApiReference\|AddOpenApi\|MapOpenApi" --include="*.cs"
grep -r "SwaggerUI\|UseSwagger" --include="*.cs"  # Legacy check
```

## Adding to Existing Project

1. If project uses Swagger, migrate to Scalar (or keep Swagger if team prefers)
2. Add `AddOpenApi()` in services and `MapScalarApiReference()` in pipeline
3. Add `BearerSecuritySchemeTransformer` if JWT auth is used
