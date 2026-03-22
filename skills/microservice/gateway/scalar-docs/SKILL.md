---
name: dotnet-ai-scalar-docs
description: >
  Scalar API documentation for gateway endpoints. Covers AddOpenApiDocumentation,
  AddBaseScalarApiDocumentation, OpenApiDocEntry, BearerSecuritySchemeTransformer,
  ScalarBasicAuthMiddleware, and Pentagon rate limiting.
  Trigger: Scalar, API docs, OpenAPI, documentation UI, Pentagon.
category: microservice/gateway
agent: gateway-architect
---

# Scalar Docs — API Documentation & Rate Limiting

## Core Principles

- Each gateway defines `AddOpenApiDocumentation(environment)` that calls the shared `AddBaseScalarApiDocumentation`
- `OpenApiDocEntry` records define versioned doc groups with environment-based visibility
- `ControllerBaseV1.GetDocEntry()` provides the doc entry for each API version
- Scalar UI is served at `/scalar` with BluePlanet theme, version dropdown, and server URL
- `ScalarBasicAuthMiddleware` protects `/scalar` and `/openapi` endpoints with Basic auth (bypassed for localhost)
- `BearerSecuritySchemeTransformer` adds JWT security scheme to all OpenAPI documents
- `PinNumberOperationTransformer` adds custom operation metadata
- `AddControllersWithConfigurations()` configures controllers with slug routing convention and global filters
- `AddPentagon()` registers Pentagon rate-limiting gRPC client and middleware

## Key Patterns

### Gateway-Specific Registration

Each gateway project defines a thin extension that passes its doc entries to the shared base.

```csharp
using {Company}.Gateways.{Domain}.Controllers.V1;
using {Company}.Gateways.Common.Scalar;
using {Company}.Gateways.Common.ServicesRegistration;
using System.Reflection;

namespace {Company}.Gateways.{Domain}.ServicesRegistration;

public static class ScalarRegistrationExtensions
{
    public static void AddOpenApiDocumentation(
        this IServiceCollection services, IWebHostEnvironment environment) =>
        services.AddBaseScalarApiDocumentation(new OpenApiConfigurations()
        {
            AppAssembly = Assembly.GetExecutingAssembly(),
            Environment = environment,
            DocEntries = GetOpenApiDocEntries()
        });

    public static void UseOpenApiDocumentation(
        this WebApplication app, IWebHostEnvironment environment) =>
        app.UseBaseScalarDocumentation(new OpenApiUIConfigurations()
        {
            Environment = environment,
            DocEntries = GetOpenApiDocEntries()
        });

    private static IEnumerable<OpenApiDocEntry> GetOpenApiDocEntries()
    {
        yield return ControllerBaseV1.GetDocEntry();
    }
}
```

### OpenApiDocEntry — Environment-Aware Doc Records

Doc entries have a `MinimumEnvironment` that controls visibility. `DevelopmentOpenApiDocEntry` is visible in all environments; `StagingOpenApiDocEntry` only in Staging and Production.

```csharp
namespace {Company}.Gateways.Common.Scalar;

public record OpenApiDocEntry(
    string Name, OpenApiInfo Info, MinimumEnvironment MinimumEnvironment)
{
    public bool MatchesEnvironment(string environment) =>
        MinimumEnvironment <= Enum.Parse<MinimumEnvironment>(environment);
}

public record DevelopmentOpenApiDocEntry(string Name, OpenApiInfo Info)
    : OpenApiDocEntry(Name, Info, MinimumEnvironment.Development);

public record StagingOpenApiDocEntry(string Name, OpenApiInfo Info)
    : OpenApiDocEntry(Name, Info, MinimumEnvironment.Staging);

public enum MinimumEnvironment
{
    Development,
    Staging,
    Production
}
```

### OpenApiConfigurations

```csharp
namespace {Company}.Gateways.Common.Scalar;

public class OpenApiConfigurations
{
    public required IWebHostEnvironment Environment { get; init; }
    public required Assembly AppAssembly { get; init; }
    public IEnumerable<OpenApiDocEntry> DocEntries { get; init; } = [];
}

public class OpenApiUIConfigurations
{
    public required IWebHostEnvironment Environment { get; init; }
    public IEnumerable<OpenApiDocEntry> DocEntries { get; init; } = [];
}
```

### AddBaseScalarApiDocumentation — Shared Registration

Registers Scalar auth options, server options, and creates OpenAPI documents for each environment-matching doc entry. Adds `BearerSecuritySchemeTransformer` and `PinNumberOperationTransformer` to every document.

```csharp
using {Company}.Gateways.Common.Scalar;
using Microsoft.AspNetCore.OpenApi;
using Microsoft.Extensions.Options;
using Scalar.AspNetCore;

namespace {Company}.Gateways.Common.ServicesRegistration;

public static class ScalarRegistrationExtensions
{
    public static void AddBaseScalarApiDocumentation(
        this IServiceCollection services, OpenApiConfigurations configurations)
    {
        services.AddOptions<ScalarAuthorizationOptions>()
            .BindConfiguration(ScalarAuthorizationOptions.Options)
            .ValidateDataAnnotations()
            .ValidateOnStart();

        services.AddOptions<ScalarServerOptions>()
            .BindConfiguration(ScalarServerOptions.Options)
            .ValidateDataAnnotations()
            .ValidateOnStart();

        foreach (var docEntry in configurations.DocEntries
            .Where(e => e.MatchesEnvironment(
                configurations.Environment.EnvironmentName)))
        {
            services.AddOpenApi(docEntry.Name, options =>
            {
                options.AddDocumentTransformer((document, context, ct) =>
                {
                    document.Info = docEntry.Info;
                    return Task.CompletedTask;
                });

                options.AddDocumentTransformer<BearerSecuritySchemeTransformer>();
                options.AddOperationTransformer<PinNumberOperationTransformer>();
            });
        }
    }

    public static void UseBaseScalarDocumentation(
        this WebApplication app, OpenApiUIConfigurations configurations)
    {
        app.UseMiddleware<ScalarBasicAuthMiddleware>();

        var docEntries = configurations.DocEntries
            .Where(e => e.MatchesEnvironment(
                configurations.Environment.EnvironmentName))
            .ToList();

        var serverOptions = app.Services
            .GetRequiredService<IOptions<ScalarServerOptions>>().Value;

        app.MapOpenApi();

        app.MapScalarApiReference("/scalar", options =>
        {
            options.WithTitle("API Documentation");
            options.WithTheme(ScalarTheme.BluePlanet);
            options.WithDefaultHttpClient(
                ScalarTarget.CSharp, ScalarClient.HttpClient);

            options.AddServer(serverOptions.ServerUrl);

            foreach (var doc in docEntries)
            {
                options.AddDocument(doc.Name, doc.Info.Title ?? doc.Name);
            }
        });
    }
}
```

### BearerSecuritySchemeTransformer

Adds JWT Bearer security scheme and requirement to every operation in every OpenAPI document.

```csharp
internal sealed class BearerSecuritySchemeTransformer : IOpenApiDocumentTransformer
{
    public Task TransformAsync(
        OpenApiDocument document,
        OpenApiDocumentTransformerContext context,
        CancellationToken cancellationToken)
    {
        var securityScheme = new OpenApiSecurityScheme
        {
            Type = SecuritySchemeType.Http,
            Name = "Authorization",
            Scheme = "bearer",
            BearerFormat = "JWT",
            In = ParameterLocation.Header,
            Description = "Please enter a valid JWT token"
        };

        document.Components ??= new OpenApiComponents();
        document.Components.SecuritySchemes ??=
            new Dictionary<string, IOpenApiSecurityScheme>();
        document.Components.SecuritySchemes["Bearer"] = securityScheme;

        var securityRequirement = new OpenApiSecurityRequirement
        {
            [new OpenApiSecuritySchemeReference("Bearer")] = []
        };

        if (document.Paths is not null)
        {
            foreach (var path in document.Paths)
            {
                if (path.Value?.Operations is not null)
                {
                    foreach (var operation in path.Value.Operations.Values)
                    {
                        operation.Security ??= [];
                        operation.Security.Add(securityRequirement);
                    }
                }
            }
        }

        return Task.CompletedTask;
    }
}
```

### ScalarBasicAuthMiddleware — Production Protection

Protects `/scalar` and `/openapi` paths with HTTP Basic authentication. Local (loopback) requests bypass the check.

```csharp
namespace {Company}.Gateways.Common.Scalar;

public class ScalarBasicAuthMiddleware(RequestDelegate next)
{
    public async Task InvokeAsync(HttpContext context)
    {
        if ((context.Request.Path.StartsWithSegments("/scalar") ||
             context.Request.Path.StartsWithSegments("/openapi")) &&
            !IsLocalRequest(context))
        {
            var authHeader = context.Request.Headers.Authorization.ToString();
            if (authHeader != null && authHeader.StartsWith("Basic "))
            {
                var encoded = authHeader.Split(' ', 2,
                    StringSplitOptions.RemoveEmptyEntries)[1]?.Trim();
                if (encoded is not null)
                {
                    var decoded = Encoding.UTF8.GetString(
                        Convert.FromBase64String(encoded));
                    var username = decoded.Split(':', 2)[0];
                    var password = decoded.Split(':', 2)[1];
                    var options = context.RequestServices
                        .GetRequiredService<IOptions<ScalarAuthorizationOptions>>()
                        .Value;

                    if (IsAuthorized(username, password, options))
                    {
                        await next.Invoke(context);
                        return;
                    }
                }
            }

            context.Response.Headers.WWWAuthenticate = "Basic";
            context.Response.StatusCode = (int)HttpStatusCode.Unauthorized;
        }
        else
        {
            await next.Invoke(context);
        }
    }

    private static bool IsAuthorized(
        string username, string password,
        ScalarAuthorizationOptions options) =>
        username.Equals(options.Username,
            StringComparison.InvariantCultureIgnoreCase)
        && password.Equals(options.Password);

    private static bool IsLocalRequest(HttpContext context) =>
        context.Connection.RemoteIpAddress is null
        || context.Connection.LocalIpAddress is null
        || context.Connection.RemoteIpAddress
            .Equals(context.Connection.LocalIpAddress)
        || IPAddress.IsLoopback(context.Connection.RemoteIpAddress);
}
```

### AddControllersWithConfigurations — Controller Setup

```csharp
namespace {Company}.Gateways.Common.ServicesRegistration;

public static partial class ControllersExtensions
{
    public static void AddControllersWithConfigurations(
        this IServiceCollection services)
    {
        services.AddControllers(options =>
        {
            options.Conventions
                .Add(new SlugifyControllerNamesConvention());

            options.Filters.Add<HttpResponseExceptionFilter>();
            options.Filters.Add<ValidateAccessFilter>();
        });
    }

    public static void MapControllersWithAuthorization(
        this IEndpointRouteBuilder endpoints) =>
        endpoints.MapControllers().RequireAuthorization();
}
```

### AddPentagon — Rate Limiting

Pentagon is a gRPC-based rate limiting and device validation service. It wraps requests with begin/end middleware.

```csharp
namespace Microsoft.Extensions.DependencyInjection;

public static class PentagonSetupExtensions
{
    public static void AddPentagon(this IServiceCollection services)
    {
        services.AddOptions<PentagonOptions>()
            .BindConfiguration(PentagonOptions.Options)
            .ValidateDataAnnotations()
            .ValidateOnStart();

        services.AddGrpcClient<Pentagon.PentagonClient>((provider, options) =>
        {
            var pentagonOptions = provider
                .GetRequiredService<IOptions<PentagonOptions>>().Value;

            options.Address = new Uri(pentagonOptions.Url);
            options.InterceptorRegistrations.Add(
                new InterceptorRegistration(
                    InterceptorScope.Client,
                    provider => new GlobalMetadataInterceptor()));
        });

        services.AddScoped<PentagonService>();
    }

    public static IApplicationBuilder UsePentagonBegin(
        this IApplicationBuilder builder) =>
        builder.UseMiddleware<PentagonBeginMiddleware>();

    public static IApplicationBuilder UsePentagonEnd(
        this IApplicationBuilder builder) =>
        builder.UseMiddleware<PentagonEndMiddleware>();
}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Using Swagger UI for new projects | Use Scalar with `AddBaseScalarApiDocumentation` |
| Exposing docs without auth in production | Use `ScalarBasicAuthMiddleware` (bypasses localhost) |
| Defining OpenAPI docs inline in Program.cs | Use `OpenApiDocEntry` from `ControllerBaseV1.GetDocEntry()` |
| Missing Pentagon rate limiting | Add `AddPentagon()` + `UsePentagonBegin/End` middleware |
| No `BearerSecuritySchemeTransformer` | Add to every OpenAPI document for JWT documentation |
| Hardcoded server URL in Scalar | Use `ScalarServerOptions` from configuration |

## Detect Existing Patterns

```bash
grep -r "AddBaseScalarApiDocumentation\|AddOpenApiDocumentation\|AddPentagon" --include="*.cs"
grep -r "ScalarBasicAuthMiddleware\|MapScalarApiReference" --include="*.cs"
```

## Adding to Existing Project

1. Define `AddOpenApiDocumentation` extension calling `AddBaseScalarApiDocumentation`
2. Yield doc entries from `ControllerBaseVx.GetDocEntry()` static methods
3. Call `UseOpenApiDocumentation` in pipeline after `UseHttpsRedirection`
4. Add `AddPentagon()` + `UsePentagonBegin/End` middleware for rate limiting
5. Use `AddControllersWithConfigurations()` and `MapControllersWithAuthorization()`
