---
name: grpc-client
description: >
  GrpcClientFactory registration with AddGrpcClient using (provider, client) callback,
  IOptions<ExternalServicesOptions> for URL resolution, and RetryCallerService wrapper
  for resilient gRPC calls with retry loop.
  Trigger: gRPC client, client factory, external service, cross-service call, retry.
category: microservice/processor
agent: processor-architect
---

# gRPC Client -- Cross-Service Communication

## Core Principles

- `AddGrpcClient<T>()` with `(provider, client) =>` callback to resolve URL from DI
- Service URLs come from `IOptions<ExternalServicesOptions>` resolved inside the callback
- `ExternalServicesOptions` uses `[Required, Url]` attributes with `const string Options` pattern
- `RetryCallerService` wraps gRPC calls with retry loop (catch `RpcException`, delay, retry)
- `RpcException` with `StatusCode.AlreadyExists` is treated as idempotent success
- No Polly -- custom retry loop in `RetryCallerService`

## Key Patterns

### ExternalServicesOptions

```csharp
namespace {Company}.{Domain}.Processor.Setup;

public class ExternalServicesOptions
{
    public const string Options = "ExternalServices";

    [Required, Url]
    public required string OrderCommand { get; init; }
    [Required, Url]
    public required string OrderQuery { get; init; }
    [Required, Url]
    public required string ProductGrpc { get; init; }
    [Required, Url]
    public required string ProductGrpcReplica { get; init; }
}
```

### Registration with (provider, client) Callback

```csharp
namespace {Company}.{Domain}.Processor.Setup;

public static class ExternalServicesRegistrationExtensions
{
    public static IServiceCollection RegisterExternalServices(
        this IServiceCollection services, IConfiguration configuration)
    {
        services.AddOptions<ExternalServicesOptions>()
            .Bind(configuration.GetSection(ExternalServicesOptions.Options));

        // Pattern: AddGrpcClient with (provider, configure) callback
        // URL is resolved from IOptions at runtime, not at registration time
        services.AddGrpcClient<OrderCommands.OrderCommandsClient>((provider, configure) =>
        {
            var options = provider.GetRequiredService<IOptions<ExternalServicesOptions>>();
            configure.Address = new Uri(options.Value.OrderCommand);
        });

        services.AddGrpcClient<OrderQueries.OrderQueriesClient>((provider, configure) =>
        {
            var options = provider.GetRequiredService<IOptions<ExternalServicesOptions>>();
            configure.Address = new Uri(options.Value.OrderQuery);
        });

        services.AddGrpcClient<ProductQueries.ProductQueriesClient>((provider, configure) =>
        {
            var options = provider.GetRequiredService<IOptions<ExternalServicesOptions>>();
            configure.Address = new Uri(options.Value.ProductGrpc);
        });

        // Some clients need explicit Action cast for overload resolution
        services.AddGrpcClient<SpecialQueries.SpecialQueriesClient>(
            (Action<IServiceProvider, global::Grpc.Net.ClientFactory.GrpcClientFactoryOptions>)
            ((provider, configure) =>
            {
                var options = provider
                    .GetRequiredService<IOptions<ExternalServicesOptions>>();
                configure.Address = new Uri(options.Value.ProductGrpcReplica);
            }));

        return services;
    }
}
```

### IRetryCallerService Interface

```csharp
namespace {Company}.{Domain}.Processor.Application.Contracts;

public interface IRetryCallerService
{
    Task<T> CallAsync<T>(
        Func<Task<T>> operation,
        int retryCount = 5,
        int millisecondsDelay = 250);
}
```

### RetryCallerService Implementation

```csharp
namespace {Company}.{Domain}.Processor.Infra.Services;

public class RetryCallerService : IRetryCallerService
{
    private readonly ILogger<RetryCallerService> _logger;

    public RetryCallerService(ILogger<RetryCallerService> logger)
    {
        _logger = logger;
    }

    public async Task<T> CallAsync<T>(
        Func<Task<T>> operation,
        int retryCount = 5,
        int millisecondsDelay = 250)
    {
        var count = retryCount + 1;

        while (true)
        {
            count--;

            try
            {
                return await operation();
            }
            catch (RpcException e)
            {
                _logger.LogWarning(e, "Call failed with {attempts} left", count);

                if (count == 0)
                    throw new RpcException(
                        new Status(StatusCode.Aborted, e.Message));
            }

            await Task.Delay(millisecondsDelay);
        }
    }
}
```

### Usage in Handler with Idempotent Error Handling

```csharp
namespace {Company}.{Domain}.Processor.Application.Features.OrderEvents;

public class OrderCreatedHandler(
    OrderCommands.OrderCommandsClient commandsClient,
    OrderQueries.OrderQueriesClient queriesClient)
    : IRequestHandler<Event<OrderCreatedData>, bool>
{
    public async Task<bool> Handle(
        Event<OrderCreatedData> @event, CancellationToken ct)
    {
        try
        {
            await commandsClient.CreateOrderAsync(new CreateOrderRequest
            {
                OrderId = @event.AggregateId.ToString(),
                Sequence = @event.Sequence
            }, cancellationToken: ct);

            return true;
        }
        catch (RpcException ex) when (ex.StatusCode == StatusCode.AlreadyExists)
        {
            // Idempotent -- already processed
            return true;
        }
        catch (Exception)
        {
            throw; // Let listener abandon the message for retry
        }
    }
}
```

### Registration of RetryCallerService

```csharp
// In ServiceBusRegistrationExtensions or ServicesRegistrationExtensions
services.AddSingleton<IRetryCallerService, RetryCallerService>();
```

### AppSettings Configuration

```json
{
  "ExternalServices": {
    "OrderCommand": "https://order-command:443",
    "OrderQuery": "https://order-query:443",
    "ProductGrpc": "https://product-grpc:443",
    "ProductGrpcReplica": "https://product-grpc-replica:443"
  }
}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Resolving options at registration time | Use `(provider, configure)` callback to resolve at runtime |
| Using Polly for retry | Use custom RetryCallerService with while loop |
| Not handling AlreadyExists | Treat RpcException with AlreadyExists as idempotent success |
| Hardcoded service URLs | Use ExternalServicesOptions from configuration |
| Creating gRPC channels manually | Use AddGrpcClient factory pattern |
| Catching and swallowing exceptions | Re-throw to let listener abandon the message |

## Detect Existing Patterns

```bash
# Find AddGrpcClient registrations
grep -r "AddGrpcClient<" --include="*.cs" src/

# Find ExternalServicesOptions
grep -r "ExternalServicesOptions" --include="*.cs" src/

# Find RetryCallerService usage
grep -r "RetryCallerService\|IRetryCallerService" --include="*.cs" src/

# Find RpcException handling
grep -r "RpcException" --include="*.cs" src/

# Find AlreadyExists idempotent handling
grep -r "StatusCode.AlreadyExists" --include="*.cs" src/
```

## Adding to Existing Project

1. **Add new URL property** to `ExternalServicesOptions` with `[Required, Url]`
2. **Add `AddGrpcClient<T>`** with `(provider, configure)` callback in registration
3. **Add service URL** to appsettings.json and K8s environment variables
4. **Inject typed client** directly into MediatR handlers
5. **Handle `StatusCode.AlreadyExists`** as idempotent success in handlers
6. **Use `RetryCallerService.CallAsync`** for operations needing retry semantics beyond message abandonment
