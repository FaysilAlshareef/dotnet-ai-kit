---
name: grpc-design
description: >
  gRPC API design for .NET — proto file conventions, service naming, message design,
  gRPC-JSON transcoding, gRPC-Web for browsers, and backward compatibility.
  Trigger: gRPC, proto, protobuf, gRPC-Web, gRPC transcoding, service definition.
metadata:
  category: api
  agent: api-designer
---

# gRPC API Design for .NET

## 1. Core Principles

- **Contract-first** — The `.proto` file IS the API. Design the proto, then generate code. Never hand-write generated stubs.
- **Backward compatible** — Every change must be safe for existing clients. Never break the wire format.
- **Strongly typed** — Leverage protobuf's type system. Avoid `google.protobuf.Any` and `string` for structured data.
- **Service-oriented** — Each service represents a bounded context or aggregate boundary. Keep services cohesive.
- **Efficient by default** — Binary serialization, HTTP/2 multiplexing, and streaming are built in. Use them intentionally.

## 2. When to Use gRPC

### Use gRPC When

- Service-to-service communication in microservices
- High-throughput, low-latency requirements
- Bidirectional or server streaming is needed
- Polyglot environments (shared proto contracts across .NET, Go, Java, Python)
- Strong contract enforcement is critical
- Internal APIs behind a gateway

### Do NOT Use gRPC When

- Browser clients need direct access (use REST or gRPC-Web with a proxy)
- You need human-readable payloads for debugging (use REST + JSON)
- The API is public-facing and must be universally consumable
- Simple CRUD with no streaming or performance needs (REST is simpler)
- Real-time push to many browser clients (use SignalR instead)
- The team has no protobuf experience and the timeline is tight

## 3. Proto File Conventions

### File Naming

Use `lowercase_with_underscores.proto`. One service per file.

```
protos/
  company/
    ordering/
      v1/
        order_service.proto
        order_messages.proto
      v2/
        order_service.proto
    catalog/
      v1/
        catalog_service.proto
```

### Package Naming

Use reverse domain with version suffix: `company.domain.v1`.

```protobuf
syntax = "proto3";

package contoso.ordering.v1;

option csharp_namespace = "Contoso.Ordering.V1";
```

### Service Naming

PascalCase for services and RPCs. Use verb-noun for RPC methods.

```protobuf
service OrderService {
  rpc CreateOrder(CreateOrderRequest) returns (CreateOrderResponse);
  rpc GetOrder(GetOrderRequest) returns (Order);
  rpc ListOrders(ListOrdersRequest) returns (ListOrdersResponse);
  rpc CancelOrder(CancelOrderRequest) returns (CancelOrderResponse);
  rpc StreamOrderUpdates(StreamOrderUpdatesRequest) returns (stream OrderUpdate);
}
```

### Request/Response Pattern

Every RPC gets its own `Request` and `Response` message, even if they seem similar. This allows independent evolution.

```protobuf
message CreateOrderRequest {
  string customer_id = 1;
  repeated OrderLineItem items = 2;
  google.protobuf.StringValue coupon_code = 3;  // nullable
}

message CreateOrderResponse {
  string order_id = 1;
  google.protobuf.Timestamp created_at = 2;
}
```

## 4. Message Design

### Field Numbering Rules

- **Never reuse** a field number after removing a field. Use `reserved`.
- Fields 1-15 use 1 byte for the tag — reserve these for frequently set fields.
- Fields 16-2047 use 2 bytes.

```protobuf
message Order {
  reserved 6, 8;                    // previously removed fields
  reserved "old_status", "legacy";  // reserved names prevent accidental reuse

  string order_id = 1;
  string customer_id = 2;
  OrderStatus status = 3;
  google.protobuf.Timestamp created_at = 4;
  repeated OrderLineItem items = 5;
  // field 6 was removed
  ShippingAddress shipping_address = 7;
  // field 8 was removed
  DecimalValue total_amount = 9;
}
```

### Well-Known Type Mappings

| .NET Type | Protobuf Type | Import |
|-----------|---------------|--------|
| `string?` | `google.protobuf.StringValue` | `google/protobuf/wrappers.proto` |
| `int?` | `google.protobuf.Int32Value` | `google/protobuf/wrappers.proto` |
| `bool?` | `google.protobuf.BoolValue` | `google/protobuf/wrappers.proto` |
| `DateTime` | `google.protobuf.Timestamp` | `google/protobuf/timestamp.proto` |
| `TimeSpan` | `google.protobuf.Duration` | `google/protobuf/duration.proto` |
| `decimal` | Custom `DecimalValue` | See below |
| `Dictionary` | `map<string, T>` | Built-in |

### Custom DecimalValue for Precision

Protobuf has no native decimal. Define a shared type:

```protobuf
// shared/decimal_value.proto
message DecimalValue {
  int64 units = 1;      // whole units
  int32 nanos = 2;      // nano units (10^-9)
}
```

### Enums

Always include an `UNSPECIFIED` zero value. Use UPPER_SNAKE_CASE.

```protobuf
enum OrderStatus {
  ORDER_STATUS_UNSPECIFIED = 0;
  ORDER_STATUS_PENDING = 1;
  ORDER_STATUS_CONFIRMED = 2;
  ORDER_STATUS_SHIPPED = 3;
  ORDER_STATUS_DELIVERED = 4;
  ORDER_STATUS_CANCELLED = 5;
}
```

### Pagination

Use cursor-based pagination for list operations:

```protobuf
message ListOrdersRequest {
  int32 page_size = 1;        // max items per page
  string page_token = 2;      // opaque cursor from previous response
  string filter = 3;          // optional filter expression
  string order_by = 4;        // optional sort
}

message ListOrdersResponse {
  repeated Order orders = 1;
  string next_page_token = 2;  // empty when no more pages
  int32 total_count = 3;
}
```

## 5. gRPC-JSON Transcoding

Expose gRPC services as RESTful JSON endpoints without a separate API layer.

### Setup

Add the NuGet package:

```xml
<PackageReference Include="Microsoft.AspNetCore.Grpc.JsonTranscoding" Version="8.0.*" />
```

Register in `Program.cs`:

```csharp
builder.Services.AddGrpc().AddJsonTranscoding();
```

### Proto Annotations

```protobuf
import "google/api/annotations.proto";

service OrderService {
  rpc GetOrder(GetOrderRequest) returns (Order) {
    option (google.api.http) = {
      get: "/v1/orders/{order_id}"
    };
  }

  rpc CreateOrder(CreateOrderRequest) returns (CreateOrderResponse) {
    option (google.api.http) = {
      post: "/v1/orders"
      body: "*"
    };
  }

  rpc ListOrders(ListOrdersRequest) returns (ListOrdersResponse) {
    option (google.api.http) = {
      get: "/v1/orders"
    };
  }
}
```

This serves both gRPC (binary/HTTP2) and REST (JSON/HTTP1.1) on the same port.

## 6. gRPC-Web for Blazor and Browser Clients

### Server Configuration

```csharp
var app = builder.Build();
app.UseGrpcWeb(new GrpcWebOptions { DefaultEnabled = true });
app.MapGrpcService<OrderServiceImpl>().EnableGrpcWeb();
```

### Blazor Client Setup

```csharp
builder.Services.AddGrpcClient<OrderService.OrderServiceClient>(options =>
{
    options.Address = new Uri("https://api.contoso.com");
})
.ConfigurePrimaryHttpMessageHandler(() => new GrpcWebHandler(new HttpClientHandler()));
```

**Limitation**: gRPC-Web does not support client streaming or bidirectional streaming. Only unary and server streaming work.

## 7. Client Generation with Grpc.Tools

### Project File Configuration

```xml
<ItemGroup>
  <PackageReference Include="Grpc.Tools" Version="2.62.*" PrivateAssets="All" />
  <PackageReference Include="Grpc.Net.Client" Version="2.62.*" />
  <PackageReference Include="Google.Protobuf" Version="3.26.*" />
</ItemGroup>

<ItemGroup>
  <Protobuf Include="Protos\**\*.proto"
            GrpcServices="Client"
            ProtoRoot="Protos" />
</ItemGroup>
```

For server projects, use `GrpcServices="Server"`. For shared projects with both, use `GrpcServices="Both"`.

### Shared Proto Package

Create a dedicated NuGet package for proto files so all services consume the same contract:

```
Contoso.Ordering.Protos/
  Protos/
    contoso/ordering/v1/order_service.proto
  Contoso.Ordering.Protos.csproj
```

## 8. C# Service Implementation

```csharp
public sealed class OrderServiceImpl : OrderService.OrderServiceBase
{
    private readonly IOrderRepository _repository;
    private readonly ILogger<OrderServiceImpl> _logger;

    public OrderServiceImpl(IOrderRepository repository, ILogger<OrderServiceImpl> logger)
    {
        _repository = repository;
        _logger = logger;
    }

    public override async Task<CreateOrderResponse> CreateOrder(
        CreateOrderRequest request, ServerCallContext context)
    {
        // Validate
        if (request.Items.Count == 0)
        {
            throw new RpcException(new Status(
                StatusCode.InvalidArgument, "Order must contain at least one item."));
        }

        // Map and persist
        var order = OrderMapper.ToDomain(request);
        await _repository.AddAsync(order, context.CancellationToken);

        _logger.LogInformation("Order {OrderId} created for customer {CustomerId}",
            order.Id, order.CustomerId);

        return new CreateOrderResponse
        {
            OrderId = order.Id.ToString(),
            CreatedAt = Timestamp.FromDateTime(order.CreatedAt)
        };
    }

    public override async Task<Order> GetOrder(
        GetOrderRequest request, ServerCallContext context)
    {
        var order = await _repository.GetByIdAsync(
            request.OrderId, context.CancellationToken);

        if (order is null)
        {
            throw new RpcException(new Status(
                StatusCode.NotFound, $"Order '{request.OrderId}' not found."));
        }

        return OrderMapper.ToProto(order);
    }

    public override async Task StreamOrderUpdates(
        StreamOrderUpdatesRequest request,
        IServerStreamWriter<OrderUpdate> responseStream,
        ServerCallContext context)
    {
        await foreach (var update in _repository
            .WatchOrderAsync(request.OrderId, context.CancellationToken))
        {
            await responseStream.WriteAsync(OrderMapper.ToUpdateProto(update));
        }
    }
}
```

### Error Handling

Map domain exceptions to gRPC status codes via interceptor (see `skills/microservice/grpc/interceptors/SKILL.md` for full pattern):

| gRPC Status Code | Use When |
|------------------|----------|
| `InvalidArgument` | Request validation fails |
| `NotFound` | Entity does not exist |
| `AlreadyExists` | Duplicate create attempt |
| `PermissionDenied` | Caller lacks permission |
| `FailedPrecondition` | Business rule violation |
| `Internal` | Unexpected server error (do not leak details) |

## 9. Proto Versioning Strategy

- **Non-breaking** (add fields/RPCs/enum values): do in-place
- **Breaking** (rename/remove/change types): create new version (`v2`), run both, migrate gradually
- Use `reserved` to mark removed fields so numbers are never reused

## 10. Decision Guide

| Scenario | Recommended | Reason |
|----------|-------------|--------|
| Internal microservice-to-microservice | **gRPC** | Performance, streaming, strong contracts |
| Public API for third-party developers | **REST** | Universal client support, documentation tooling |
| Flexible client queries on complex graphs | **GraphQL** | Client controls response shape |
| Real-time browser push (notifications) | **SignalR** | Native WebSocket, broad browser support |
| Browser client calling backend services | **gRPC-Web** or **REST** | gRPC-Web if already gRPC; REST if simpler |
| High-throughput event streaming | **gRPC streaming** | Efficient bidirectional binary streams |
| Mobile app with spotty connectivity | **REST** | Simpler retry, caching, offline support |
| Polyglot services (Go, Java, .NET) | **gRPC** | Single proto generates all client/server code |

## 11. Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Reusing deleted field numbers | Wire format corruption for old clients | Use `reserved` for removed fields |
| No version in package name | Cannot make breaking changes safely | Always include `v1`, `v2` in package |
| Fat messages (50+ fields) | Slow serialization, hard to evolve | Split into nested messages |
| Using `string` for everything | Loses type safety, validation moves to runtime | Use proper types and well-known wrappers |
| `google.protobuf.Any` everywhere | Defeats the purpose of a typed contract | Use `oneof` for polymorphism |
| No request/response wrappers | Cannot add fields without breaking signature | Every RPC gets its own Request/Response |
| Ignoring deadlines | Cascading timeouts across services | Always set and propagate deadlines |
| Returning internal errors verbatim | Leaks stack traces and implementation details | Map to status codes, log internally |
| Synchronous blocking in async RPCs | Thread pool starvation under load | Use `async`/`await` throughout |
| Skipping health checks | Load balancer cannot route away from failures | Implement `Grpc.HealthCheck` |
