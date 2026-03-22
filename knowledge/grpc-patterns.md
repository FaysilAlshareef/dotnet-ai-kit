# gRPC Patterns

gRPC service design patterns for .NET microservice architecture.
Covers proto design, service implementation, interceptors, client factories, and error mapping between gRPC and REST.

---

## Proto File Design

### Naming Conventions

```
protos/
├── {domain}_commands.proto     # Command-side operations
├── {domain}_queries.proto      # Query-side operations
└── shared/
    └── common.proto            # Shared message types
```

### Proto Design Rules

1. Use `StringValue` for nullable strings (not empty string as null)
2. Use `Timestamp` for date/time fields
3. Use `DecimalValue` custom message for decimal precision
4. Paginated responses include `PageResponse` metadata
5. RPC names match operation (CreateOrder, GetOrders)
6. Request/Response messages are named `{RPC}Request` / `{RPC}Response`

### Example Proto File

```protobuf
syntax = "proto3";

package {company}.{domain}.commands.v1;

import "google/protobuf/wrappers.proto";
import "google/protobuf/timestamp.proto";

option csharp_namespace = "{Company}.{Domain}.Commands.Grpc";

service OrderCommands {
    rpc CreateOrder (CreateOrderRequest) returns (CreateOrderResponse);
    rpc UpdateOrder (UpdateOrderRequest) returns (UpdateOrderResponse);
    rpc CancelOrder (CancelOrderRequest) returns (CancelOrderResponse);
}

message CreateOrderRequest {
    string customer_name = 1;
    double total = 2;
    repeated OrderItemRequest items = 3;
}

message OrderItemRequest {
    string product_id = 1;
    int32 quantity = 2;
    double unit_price = 3;
}

message CreateOrderResponse {
    string order_id = 1;
    int32 sequence = 2;
}

// Query service proto
service OrderQueries {
    rpc GetOrder (GetOrderRequest) returns (GetOrderResponse);
    rpc GetOrders (GetOrdersRequest) returns (GetOrdersResponse);
}

message GetOrderRequest {
    string order_id = 1;
}

message GetOrderResponse {
    string order_id = 1;
    string customer_name = 2;
    double total = 3;
    google.protobuf.Timestamp created_at = 4;
    google.protobuf.StringValue notes = 5;  // nullable
    repeated OrderItemResponse items = 6;
}

message GetOrdersRequest {
    int32 page = 1;
    int32 page_size = 2;
    google.protobuf.StringValue search = 3;
}

message GetOrdersResponse {
    repeated GetOrderResponse orders = 1;
    PageResponse pagination = 2;
}

message PageResponse {
    int32 total_count = 1;
    int32 page = 2;
    int32 page_size = 3;
    bool has_next_page = 4;
}
```

---

## gRPC Service Implementation

Services inherit from the generated base class and delegate to MediatR handlers.

```csharp
public sealed class OrderCommandsService(IMediator mediator)
    : OrderCommands.OrderCommandsBase
{
    public override async Task<CreateOrderResponse> CreateOrder(
        CreateOrderRequest request, ServerCallContext context)
    {
        var command = request.ToCommand();
        var output = await mediator.Send(command, context.CancellationToken);
        return output.ToResponse();
    }

    public override async Task<UpdateOrderResponse> UpdateOrder(
        UpdateOrderRequest request, ServerCallContext context)
    {
        var command = request.ToCommand();
        var output = await mediator.Send(command, context.CancellationToken);
        return output.ToResponse();
    }
}
```

### Mapping Extensions

Keep mapping logic in extension classes, one per proto service:

```csharp
public static class OrderCommandMappings
{
    public static CreateOrderCommand ToCommand(this CreateOrderRequest request) =>
        new(request.CustomerName, (decimal)request.Total);

    public static CreateOrderResponse ToResponse(this OrderOutput output) =>
        new()
        {
            OrderId = output.Id.ToString(),
            Sequence = output.Sequence
        };

    public static UpdateOrderCommand ToCommand(this UpdateOrderRequest request) =>
        new(Guid.Parse(request.OrderId), request.CustomerName, (decimal)request.Total);
}

public static class OrderQueryMappings
{
    public static GetOrderResponse ToResponse(this OrderOutput output) =>
        new()
        {
            OrderId = output.Id.ToString(),
            CustomerName = output.CustomerName,
            Total = (double)output.Total,
            CreatedAt = Timestamp.FromDateTime(output.CreatedAt.ToUniversalTime()),
            Notes = output.Notes is not null ? new StringValue { Value = output.Notes } : null
        };

    public static GetOrdersResponse ToResponse(this Paginated<OrderOutput> paginated) =>
        new()
        {
            Orders = { paginated.Items.Select(o => o.ToResponse()) },
            Pagination = new PageResponse
            {
                TotalCount = paginated.TotalCount,
                Page = paginated.Page,
                PageSize = paginated.PageSize,
                HasNextPage = paginated.HasNextPage
            }
        };
}
```

---

## Interceptors

Interceptors handle cross-cutting concerns in gRPC: exception handling, culture switching, logging, and claims propagation.

### Application Exception Interceptor

Maps domain exceptions to gRPC status codes with ProblemDetails metadata:

```csharp
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
        catch (ValidationException ex)
        {
            throw CreateRpcException(StatusCode.InvalidArgument, ex.Message, ex);
        }
        catch (NotFoundException ex)
        {
            throw CreateRpcException(StatusCode.NotFound, ex.Message, ex);
        }
        catch (DomainException ex)
        {
            throw CreateRpcException(StatusCode.FailedPrecondition, ex.Message, ex);
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Unhandled exception in gRPC handler");
            throw CreateRpcException(StatusCode.Internal, "An internal error occurred", ex);
        }
    }

    private static RpcException CreateRpcException(
        StatusCode code, string message, Exception ex)
    {
        var metadata = new Metadata();

        if (ex is IProblemDetailsProvider provider)
        {
            var problemDetails = provider.ToProblemDetails();
            var json = JsonConvert.SerializeObject(problemDetails);
            metadata.Add("problem-details-bin", System.Text.Encoding.UTF8.GetBytes(json));
        }

        return new RpcException(new Status(code, message), metadata);
    }
}
```

### Thread Culture Interceptor

Sets the current thread culture from the gRPC "language" header:

```csharp
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
            var culture = CultureInfo.GetCultureInfo(languageHeader);
            CultureInfo.CurrentCulture = culture;
            CultureInfo.CurrentUICulture = culture;
        }

        return await continuation(request, context);
    }
}
```

### Access Claims Interceptor

Extracts access claims from binary metadata headers:

```csharp
public sealed class AccessClaimsInterceptor(IAccessClaimsProvider claimsProvider) : Interceptor
{
    public override async Task<TResponse> UnaryServerHandler<TRequest, TResponse>(
        TRequest request,
        ServerCallContext context,
        UnaryServerMethod<TRequest, TResponse> continuation)
    {
        var claimsBin = context.RequestHeaders
            .FirstOrDefault(h => h.Key == "access-claims-bin")?.ValueBytes;

        if (claimsBin is not null)
        {
            var claims = JsonConvert.DeserializeObject<AccessClaims>(
                System.Text.Encoding.UTF8.GetString(claimsBin));
            claimsProvider.SetClaims(claims);
        }

        return await continuation(request, context);
    }
}
```

### Registration Order

```csharp
// Order matters — outermost interceptor runs first
services.AddGrpc(options =>
{
    options.Interceptors.Add<ThreadCultureInterceptor>();
    options.Interceptors.Add<AccessClaimsInterceptor>();
    options.Interceptors.Add<ApplicationExceptionInterceptor>(); // innermost
    options.EnableDetailedErrors = builder.Environment.IsDevelopment();
});
```

---

## gRPC Client Factory

Register gRPC clients for calling other microservices.

### Registration

```csharp
public sealed class ExternalServicesOptions
{
    public const string SectionName = "ExternalServices";

    [Required]
    public string CommandServiceUrl { get; set; } = string.Empty;
    [Required]
    public string QueryServiceUrl { get; set; } = string.Empty;
}

public static class GrpcClientRegistration
{
    public static IServiceCollection AddGrpcClients(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        services.AddOptions<ExternalServicesOptions>()
            .BindConfiguration(ExternalServicesOptions.SectionName)
            .ValidateDataAnnotations()
            .ValidateOnStart();

        var externalServices = configuration
            .GetSection(ExternalServicesOptions.SectionName)
            .Get<ExternalServicesOptions>()!;

        services.AddGrpcClient<OrderCommands.OrderCommandsClient>(options =>
        {
            options.Address = new Uri(externalServices.CommandServiceUrl);
        })
        .ConfigureChannel(options =>
        {
            options.MaxReceiveMessageSize = 16 * 1024 * 1024; // 16 MB
        })
        .AddInterceptor<ClientLoggingInterceptor>();

        services.AddGrpcClient<OrderQueries.OrderQueriesClient>(options =>
        {
            options.Address = new Uri(externalServices.QueryServiceUrl);
        });

        return services;
    }
}
```

### Client Usage

```csharp
// In a gateway controller
[ApiController]
[Route("api/v1/orders")]
public sealed class OrderController(
    OrderCommands.OrderCommandsClient commandClient,
    OrderQueries.OrderQueriesClient queryClient) : ControllerBase
{
    [HttpPost]
    public async Task<ActionResult<OrderResponse>> Create(
        CreateOrderRequest request, CancellationToken ct)
    {
        try
        {
            var grpcRequest = request.ToGrpcRequest();
            var result = await commandClient.CreateOrderAsync(grpcRequest, cancellationToken: ct);
            return Ok(result.ToResponse());
        }
        catch (RpcException ex)
        {
            return MapRpcException(ex);
        }
    }
}
```

---

## Error Mapping: gRPC to REST

Map gRPC status codes to HTTP status codes in gateway controllers:

```csharp
public static class GrpcErrorMapper
{
    public static ActionResult MapRpcException(RpcException ex)
    {
        var problemDetails = ExtractProblemDetails(ex);

        var statusCode = ex.StatusCode switch
        {
            StatusCode.NotFound => StatusCodes.Status404NotFound,
            StatusCode.InvalidArgument => StatusCodes.Status400BadRequest,
            StatusCode.FailedPrecondition => StatusCodes.Status409Conflict,
            StatusCode.PermissionDenied => StatusCodes.Status403Forbidden,
            StatusCode.Unauthenticated => StatusCodes.Status401Unauthorized,
            StatusCode.Unavailable => StatusCodes.Status503ServiceUnavailable,
            StatusCode.DeadlineExceeded => StatusCodes.Status504GatewayTimeout,
            _ => StatusCodes.Status500InternalServerError
        };

        if (problemDetails is not null)
            return new ObjectResult(problemDetails) { StatusCode = statusCode };

        return new ObjectResult(new ProblemDetails
        {
            Status = statusCode,
            Title = ex.StatusCode.ToString(),
            Detail = ex.Status.Detail
        }) { StatusCode = statusCode };
    }

    private static ProblemDetails? ExtractProblemDetails(RpcException ex)
    {
        var entry = ex.Trailers?.FirstOrDefault(t => t.Key == "problem-details-bin");
        if (entry?.ValueBytes is null) return null;

        var json = System.Text.Encoding.UTF8.GetString(entry.ValueBytes);
        return JsonConvert.DeserializeObject<ProblemDetails>(json);
    }
}
```

---

## FluentValidation for gRPC Requests

Validate gRPC request messages using FluentValidation with the Calzolari integration:

```csharp
// Validator per request type
public sealed class CreateOrderRequestValidator : AbstractValidator<CreateOrderRequest>
{
    public CreateOrderRequestValidator()
    {
        RuleFor(x => x.CustomerName).NotEmpty().WithMessage(Phrases.CustomerNameRequired);
        RuleFor(x => x.Total).GreaterThan(0).WithMessage(Phrases.InvalidTotal);
        RuleForEach(x => x.Items).ChildRules(item =>
        {
            item.RuleFor(x => x.Quantity).GreaterThan(0);
        });
    }
}

// Registration
services.AddGrpc(options =>
{
    options.EnableMessageValidation();
});
services.AddGrpcValidation();
services.AddValidator<CreateOrderRequestValidator>();
```

---

## gRPC Service Registration

```csharp
// Program.cs
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddGrpc(options =>
{
    options.Interceptors.Add<ApplicationExceptionInterceptor>();
    options.EnableDetailedErrors = builder.Environment.IsDevelopment();
    options.MaxReceiveMessageSize = 16 * 1024 * 1024;
});
builder.Services.AddGrpcValidation();
builder.Services.AddGrpcReflection(); // For grpcurl testing

var app = builder.Build();

app.MapGrpcService<OrderCommandsService>();
app.MapGrpcService<OrderQueriesService>();

if (app.Environment.IsDevelopment())
    app.MapGrpcReflectionService();

app.Run();
```

---

## Related Documents

- `knowledge/event-sourcing-flow.md` — Complete event flow
- `knowledge/deployment-patterns.md` — gRPC in Kubernetes
- `knowledge/testing-patterns.md` — gRPC integration testing
