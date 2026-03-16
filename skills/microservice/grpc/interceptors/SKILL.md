---
name: interceptors
description: >
  gRPC server and client interceptors for cross-cutting concerns. Covers exception
  mapping, culture switching, access claims extraction, and registration order.
  Trigger: gRPC interceptor, exception handling, culture, access claims.
category: microservice/grpc
agent: command-architect
---

# Interceptors — Cross-Cutting gRPC Concerns

## Core Principles

- Interceptors handle cross-cutting concerns for gRPC calls
- `ApplicationExceptionInterceptor` maps domain exceptions to `RpcException` with ProblemDetails
- `ThreadCultureInterceptor` reads language header and sets thread culture
- Access claims extracted from `access-claims-bin` metadata header
- Registration order matters: culture before exception interceptor
- Both server and client interceptors are supported

## Key Patterns

### Application Exception Interceptor (Server)

```csharp
namespace {Company}.{Domain}.Grpc.Interceptors;

public sealed class ApplicationExceptionInterceptor(
    ILogger<ApplicationExceptionInterceptor> logger) : Interceptor
{
    public override async Task<TResponse> UnaryServerHandler<TRequest, TResponse>(
        TRequest request,
        ServerCallContext context,
        UnaryServerMethod<TRequest, TResponse> continuation)
    {
        try
        {
            return await continuation(request, context);
        }
        catch (DomainException ex) when (ex is IProblemDetailsProvider provider)
        {
            logger.LogWarning(ex, "Domain exception: {Message}", ex.Message);

            var problemDetails = provider.ToProblemDetails();
            var metadata = new Metadata
            {
                { "problem-details-bin",
                  Encoding.UTF8.GetBytes(
                      JsonConvert.SerializeObject(problemDetails)) }
            };

            throw new RpcException(
                new Status(MapStatusCode(ex), ex.Message), metadata);
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Unhandled exception in gRPC handler");
            throw new RpcException(
                new Status(StatusCode.Internal, "Internal server error"));
        }
    }

    private static StatusCode MapStatusCode(DomainException ex) => ex switch
    {
        NotFoundException => StatusCode.NotFound,
        ConflictException => StatusCode.AlreadyExists,
        ValidationException => StatusCode.InvalidArgument,
        UnauthorizedException => StatusCode.PermissionDenied,
        _ => StatusCode.Internal
    };
}
```

### Thread Culture Interceptor (Server)

```csharp
namespace {Company}.{Domain}.Grpc.Interceptors;

public sealed class ThreadCultureInterceptor : Interceptor
{
    public override async Task<TResponse> UnaryServerHandler<TRequest, TResponse>(
        TRequest request,
        ServerCallContext context,
        UnaryServerMethod<TRequest, TResponse> continuation)
    {
        var languageHeader = context.RequestHeaders
            .FirstOrDefault(h => h.Key == "language")?.Value;

        if (!string.IsNullOrEmpty(languageHeader))
        {
            var culture = new CultureInfo(languageHeader);
            Thread.CurrentThread.CurrentCulture = culture;
            Thread.CurrentThread.CurrentUICulture = culture;
        }

        return await continuation(request, context);
    }
}
```

### Access Claims Interceptor (Server)

```csharp
namespace {Company}.{Domain}.Grpc.Interceptors;

public sealed class AccessClaimsInterceptor : Interceptor
{
    public override async Task<TResponse> UnaryServerHandler<TRequest, TResponse>(
        TRequest request,
        ServerCallContext context,
        UnaryServerMethod<TRequest, TResponse> continuation)
    {
        var claimsEntry = context.RequestHeaders
            .FirstOrDefault(h => h.Key == "access-claims-bin");

        if (claimsEntry is not null)
        {
            var claimsJson = Encoding.UTF8.GetString(claimsEntry.ValueBytes);
            var claims = JsonConvert.DeserializeObject<AccessClaims>(claimsJson);
            context.UserState["AccessClaims"] = claims;
        }

        return await continuation(request, context);
    }
}
```

### Client Interceptor (For Outgoing Calls)

```csharp
namespace {Company}.{Domain}.Grpc.Interceptors;

public sealed class LanguageClientInterceptor : Interceptor
{
    public override AsyncUnaryCall<TResponse> AsyncUnaryCall<TRequest, TResponse>(
        TRequest request,
        ClientInterceptorContext<TRequest, TResponse> context,
        AsyncUnaryCallContinuation<TRequest, TResponse> continuation)
    {
        var headers = context.Options.Headers ?? new Metadata();
        headers.Add("language", CultureInfo.CurrentCulture.Name);

        var newContext = new ClientInterceptorContext<TRequest, TResponse>(
            context.Method, context.Host,
            context.Options.WithHeaders(headers));

        return continuation(request, newContext);
    }
}
```

### Registration

```csharp
builder.Services.AddGrpc(options =>
{
    // Order matters: first registered = first executed
    options.Interceptors.Add<ThreadCultureInterceptor>();
    options.Interceptors.Add<AccessClaimsInterceptor>();
    options.Interceptors.Add<ApplicationExceptionInterceptor>();
});
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Exception handling in every service method | Use exception interceptor |
| Culture setting in every handler | Use culture interceptor |
| Wrong interceptor order | Culture before exception interceptor |
| Exposing stack traces to clients | Log internally, return clean error to client |

## Detect Existing Patterns

```bash
# Find interceptors
grep -r ": Interceptor" --include="*.cs" src/

# Find interceptor registration
grep -r "Interceptors.Add" --include="*.cs" src/

# Find ProblemDetails in gRPC context
grep -r "problem-details-bin" --include="*.cs" src/
```

## Adding to Existing Project

1. **Check existing interceptor chain** — maintain registration order
2. **Match exception mapping** to existing domain exception hierarchy
3. **Follow ProblemDetails format** for error metadata
4. **Add client interceptors** when calling other services (language propagation)
5. **Test interceptor behavior** with unit tests
