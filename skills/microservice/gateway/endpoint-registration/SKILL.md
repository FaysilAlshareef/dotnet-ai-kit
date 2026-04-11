---
name: endpoint-registration
description: >
  Use when registering gRPC client factories and service URLs in the gateway.
metadata:
  category: microservice/gateway
  agent: gateway-architect
  when-to-use: "When configuring gateway gRPC client registration or ServicesURLsOptions"
---

# Endpoint Registration — gRPC Client Factory Setup

## Core Principles

- `ServicesURLsOptions` holds all backend service URLs as `[Required, Url]` properties
- A static `AddGrpcClients` extension method registers all gRPC clients
- `AddServicesURLsOptions` binds configuration, validates annotations, and validates on start
- Each client uses `AddGrpcClient<T>((provider, options) => RegisterUrl(...))` pattern
- `RegisterUrl` resolves `IOptions<ServicesURLsOptions>` from the provider and calls `RegisterInterceptors`
- `RegisterInterceptors` sets the `Address` and adds a `GlobalMetadataInterceptor` for culture/claims forwarding
- Proto files are referenced in `.csproj` with `GrpcServices="Client"`

## Key Patterns

### ServicesURLsOptions — Validated URL Configuration

Each backend service URL is a `[Required, Url]` property. Multiple services may share the same URL (e.g., commands and queries on the same host).

```csharp
using System.ComponentModel.DataAnnotations;

namespace {Company}.Gateways.{Domain}.GrpcClients;

public class ServicesURLsOptions
{
    public const string ServicesURLs = "ServicesURLs";

    [Required, Url]
    public required string OrderCommand { get; set; }

    [Required, Url]
    public required string OrderQuery { get; set; }

    [Required, Url]
    public required string ProductCommand { get; set; }

    [Required, Url]
    public required string ProductQuery { get; set; }

    [Required, Url]
    public required string ReportQueries { get; set; }

    [Required, Url]
    public required string FileStorage { get; set; }
}
```

### GrpcClientRegistrationExtension — Full Registration

The static extension method registers all gRPC clients. The `AddServicesURLsOptions` helper binds the configuration section and enables startup validation. The `RegisterUrl` helper resolves the options from DI and delegates to `RegisterInterceptors`.

```csharp
using {Company}.Gateways.Common.Extensions;
using Grpc.Net.ClientFactory;
using Microsoft.Extensions.Options;

namespace {Company}.Gateways.{Domain}.GrpcClients;

public static class GrpcClientRegistrationExtension
{
    public static void AddGrpcClients(
        this IServiceCollection services, IConfiguration configuration)
    {
        AddServicesURLsOptions(services, configuration);

        // Order Commands
        services.AddGrpcClient<OrderCommands.OrderCommandsClient>(
            (provider, options) =>
                RegisterUrl(provider, o => o.OrderCommand, options));

        // Order Queries
        services.AddGrpcClient<OrderManagementQueries.OrderManagementQueriesClient>(
            (provider, options) =>
                RegisterUrl(provider, o => o.OrderQuery, options));

        // Product Commands
        services.AddGrpcClient<ProductCommands.ProductCommandsClient>(
            (provider, options) =>
                RegisterUrl(provider, o => o.ProductCommand, options));

        // Product Queries (multiple clients sharing same URL)
        services.AddGrpcClient<ProductQueries.ProductQueriesClient>(
            (provider, options) =>
                RegisterUrl(provider, o => o.ProductQuery, options));
        services.AddGrpcClient<ProductReports.ProductReportsClient>(
            (provider, options) =>
                RegisterUrl(provider, o => o.ProductQuery, options));

        // File Storage
        services.AddGrpcClient<FileStorageUploader.FileStorageUploaderClient>(
            (provider, options) =>
                RegisterUrl(provider, o => o.FileStorage, options));
    }

    private static void AddServicesURLsOptions(
        IServiceCollection services, IConfiguration configuration)
    {
        services.AddOptions<ServicesURLsOptions>()
            .Bind(configuration.GetSection(ServicesURLsOptions.ServicesURLs))
            .ValidateDataAnnotations()
            .ValidateOnStart();
    }

    private static void RegisterUrl(
        IServiceProvider provider,
        Func<ServicesURLsOptions, string> getUrl,
        GrpcClientFactoryOptions options)
    {
        var servicesURLs = provider
            .GetRequiredService<IOptions<ServicesURLsOptions>>().Value;
        options.RegisterInterceptors(getUrl(servicesURLs));
    }
}
```

### RegisterInterceptors — Common Extension (Shared Library)

This lives in the shared `{Company}.Gateways.Common` library. It sets the gRPC channel address and adds a `GlobalMetadataInterceptor` that forwards culture and access claims to every gRPC call.

```csharp
using Grpc.Core;
using Grpc.Core.Interceptors;
using Grpc.Net.ClientFactory;
using System.Globalization;

namespace {Company}.Gateways.Common.Extensions;

public static class GrpcClientRegistrationExtension
{
    public static void RegisterInterceptors(
        this GrpcClientFactoryOptions options, string address)
    {
        options.Address = new Uri(address);
        options.InterceptorRegistrations.Add(
            new InterceptorRegistration(
                InterceptorScope.Client,
                provider => new GlobalMetadataInterceptor(provider)));
    }

    class GlobalMetadataInterceptor(IServiceProvider provider) : Interceptor
    {
        private readonly IServiceProvider _provider = provider;

        public override AsyncUnaryCall<TResponse> AsyncUnaryCall<TRequest, TResponse>(
            TRequest request,
            ClientInterceptorContext<TRequest, TResponse> context,
            AsyncUnaryCallContinuation<TRequest, TResponse> continuation)
        {
            var culture = CultureInfo.CurrentCulture;
            var options = context.Options.WithHeaders(
            [
                new("language", culture.Name)
            ]);

            var claimsProvider = _provider
                .GetRequiredService<AccessClaimsProvider>();
            var accessClaims = claimsProvider.GetAccessClaims();

            if (accessClaims != null)
                options.Headers!.Add("access-claims-bin", accessClaims);

            return base.AsyncUnaryCall(
                request,
                new ClientInterceptorContext<TRequest, TResponse>(
                    context.Method, context.Host, options),
                continuation);
        }
    }
}
```

### Proto File Configuration (.csproj)

```xml
<ItemGroup>
  <Protobuf Include="Protos\order-commands.proto" GrpcServices="Client" />
  <Protobuf Include="Protos\order-queries.proto" GrpcServices="Client" />
  <Protobuf Include="Protos\product-commands.proto" GrpcServices="Client" />
  <Protobuf Include="Protos\product-queries.proto" GrpcServices="Client" />
</ItemGroup>

<ItemGroup>
  <PackageReference Include="Google.Protobuf" />
  <PackageReference Include="Grpc.Net.ClientFactory" />
  <PackageReference Include="Grpc.Tools" PrivateAssets="All" />
</ItemGroup>
```

### appsettings.json

```json
{
  "ServicesURLs": {
    "OrderCommand": "https://order-command:8081",
    "OrderQuery": "https://order-query:8081",
    "ProductCommand": "https://product-command:8081",
    "ProductQuery": "https://product-query:8081",
    "ReportQueries": "https://report-query:8081",
    "FileStorage": "https://file-storage:8081"
  }
}
```

### Program.cs Usage

```csharp
builder.Services.AddGrpcClients(builder.Configuration);
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Hardcoded URLs in code | Use `ServicesURLsOptions` from configuration |
| Missing `ValidateOnStart` | Fail fast on misconfigured URLs at startup |
| Resolving URLs from config at registration time | Use `(provider, options) =>` callback to resolve at runtime |
| Missing interceptors on gRPC clients | Use `RegisterInterceptors` to add language/claims forwarding |
| No `[Required, Url]` on URL properties | Always validate with data annotations |
| Creating new options class per client | Share one `ServicesURLsOptions` with all URLs |

## Detect Existing Patterns

```bash
# Find service URL options
grep -r "ServicesURLsOptions\|ServicesURLs" --include="*.cs"

# Find AddGrpcClient registrations
grep -r "AddGrpcClient<" --include="*.cs"

# Find RegisterUrl / RegisterInterceptors
grep -r "RegisterUrl\|RegisterInterceptors" --include="*.cs"

# Find proto references
grep -r "GrpcServices" --include="*.csproj"

# Find ValidateOnStart
grep -r "ValidateOnStart" --include="*.cs"
```

## Adding to Existing Project

1. **Add URL property** to `ServicesURLsOptions` with `[Required, Url]`
2. **Add `AddGrpcClient<T>` call** in `AddGrpcClients` using `RegisterUrl` helper
3. **Multiple clients can share one URL** if they connect to the same service host
4. **Copy proto file** to `Protos/` directory
5. **Add `<Protobuf>` item** in `.csproj` with `GrpcServices="Client"`
6. **Add service URL** to `appsettings.json` under `ServicesURLs` section
7. **Update K8s manifest** with environment variable for the new URL
