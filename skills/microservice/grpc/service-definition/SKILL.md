---
name: dotnet-ai-service-definition
description: >
  Proto file design and gRPC service implementation patterns. Covers proto service/message
  definitions, service class inheritance, MediatR integration, and mapping extensions.
  Trigger: proto file, gRPC service, protobuf, service definition, rpc.
category: microservice/grpc
agent: command-architect
---

# Service Definition — Proto Files & Implementation

## Core Principles

- Proto files define the service contract (`.proto` files)
- Service classes inherit from generated `*Base` class
- MediatR dispatches from gRPC service to handlers
- Mapping extensions convert between proto and domain types
- Proto types: `google.protobuf.StringValue` for nullable, `google.protobuf.Timestamp` for DateTime
- Pagination uses `PageRequest`/`PageResponse` messages

## Key Patterns

### Proto File Structure

```protobuf
syntax = "proto3";

package {company}.{domain};

import "google/protobuf/wrappers.proto";
import "google/protobuf/timestamp.proto";

option csharp_namespace = "{Company}.{Domain}.Grpc";

// Command service
service OrderCommands {
  rpc CreateOrder (CreateOrderRequest) returns (CreateOrderResponse);
  rpc UpdateOrder (UpdateOrderRequest) returns (UpdateOrderResponse);
  rpc CompleteOrder (CompleteOrderRequest) returns (CompleteOrderResponse);
}

// Query service
service OrderQueries {
  rpc GetOrder (GetOrderRequest) returns (OrderResponse);
  rpc GetOrders (GetOrdersRequest) returns (GetOrdersResponse);
}

// Messages
message CreateOrderRequest {
  string customer_name = 1;
  double total = 2;
  repeated OrderItemMessage items = 3;
}

message CreateOrderResponse {
  string order_id = 1;
  int32 sequence = 2;
}

message GetOrdersRequest {
  int32 page = 1;
  int32 page_size = 2;
  google.protobuf.StringValue search = 3;      // nullable
  google.protobuf.StringValue status = 4;       // nullable
}

message GetOrdersResponse {
  repeated OrderSummary items = 1;
  int32 total_count = 2;
  int32 page = 3;
  int32 page_size = 4;
}

message OrderSummary {
  string id = 1;
  string customer_name = 2;
  double total = 3;
  string status = 4;
}

message OrderItemMessage {
  string product_id = 1;
  int32 quantity = 2;
  double unit_price = 3;
}
```

### Service Implementation

```csharp
namespace {Company}.{Domain}.Grpc.Services;

public sealed class OrderCommandsService(IMediator mediator)
    : OrderCommands.OrderCommandsBase
{
    public override async Task<CreateOrderResponse> CreateOrder(
        CreateOrderRequest request, ServerCallContext context)
    {
        var command = request.ToCommand();
        var output = await mediator.Send(command);
        return output.ToCreateResponse();
    }

    public override async Task<UpdateOrderResponse> UpdateOrder(
        UpdateOrderRequest request, ServerCallContext context)
    {
        var command = request.ToCommand();
        var output = await mediator.Send(command);
        return output.ToUpdateResponse();
    }
}
```

### Mapping Extensions

```csharp
namespace {Company}.{Domain}.Grpc.Extensions;

public static class OrderMappingExtensions
{
    // Request → Command
    public static CreateOrderCommand ToCommand(this CreateOrderRequest r) =>
        new(r.CustomerName, (decimal)r.Total,
            r.Items.Select(i => new OrderItemInput(
                Guid.Parse(i.ProductId), i.Quantity, (decimal)i.UnitPrice
            )).ToList());

    // Output → Response
    public static CreateOrderResponse ToCreateResponse(this OrderOutput o) =>
        new() { OrderId = o.Id.ToString(), Sequence = o.Sequence };

    // Nullable proto → C# nullable
    public static string? ToNullable(this StringValue? value) =>
        value?.Value;

    // DateTime → Timestamp
    public static Timestamp ToTimestamp(this DateTime dt) =>
        Timestamp.FromDateTime(dt.ToUniversalTime());
}
```

### Registration in Program.cs

```csharp
// Server-side registration
builder.Services.AddGrpc(options =>
{
    options.Interceptors.Add<ApplicationExceptionInterceptor>();
    options.Interceptors.Add<ThreadCultureInterceptor>();
});

var app = builder.Build();

app.MapGrpcService<OrderCommandsService>();
app.MapGrpcService<OrderQueriesService>();
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Using `string` for nullable fields | Use `google.protobuf.StringValue` |
| Business logic in gRPC service | Delegate to MediatR handlers |
| Missing mapping extensions | Always have explicit ToCommand/ToResponse |
| Using `float` for money | Use `double` in proto, cast to `decimal` in C# |
| Hardcoded strings in service | Use resource strings for error messages |

## Detect Existing Patterns

```bash
# Find .proto files
find . -name "*.proto" -type f

# Find gRPC service implementations
grep -r "CommandsBase\|QueriesBase" --include="*.cs" src/

# Find mapping extensions
grep -r "ToCommand\|ToResponse" --include="*.cs" src/Grpc/

# Find MapGrpcService
grep -r "MapGrpcService" --include="*.cs" src/
```

## Adding to Existing Project

1. **Follow existing proto file naming** — `{domain}-commands.proto`, `{domain}-queries.proto`
2. **Match message naming conventions** — PascalCase messages, snake_case fields
3. **Add mapping extensions** in `Grpc/Extensions/` directory
4. **Register new service** with `MapGrpcService<T>()` in Program.cs
5. **Update `.csproj`** with proto file reference (`GrpcServices="Server"` or `"Both"`)
