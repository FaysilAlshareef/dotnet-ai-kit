---
name: gateway-endpoint
description: >
  REST controllers in gateway that delegate to gRPC backend services. Covers
  ControllerBaseV1 inheritance, gRPC client injection, inline request/response mapping,
  Paginated<T>, and authorization attributes.
  Trigger: gateway controller, REST endpoint, gRPC client call, API endpoint.
when-to-use: "When creating or modifying REST controllers or gRPC service endpoints"
metadata:
  category: microservice/gateway
  agent: gateway-architect
---

# Gateway Endpoint — REST to gRPC Bridge

## Core Principles

- Gateway exposes REST endpoints that delegate to backend gRPC services
- Controllers inherit from a versioned `ControllerBaseV1` abstract class (not raw `ControllerBase`)
- `ControllerBaseV1` defines shared route constants and OpenAPI doc entries
- Controllers inject typed gRPC clients directly via primary constructors
- Request/response mapping is done inline in each action (no separate extension methods unless enum conversion is needed)
- `Paginated<T>` wraps list responses with `Results`, `CurrentPage`, `PageSize`, `Total`
- Command actions return a simple `Response { Message }` wrapper
- `[Authorize]` or `[Authorize(Policy = ...)]` or `[Authorize(Roles = ...)]` applied at class level

## Key Patterns

### ControllerBaseV1 — Shared Base Class

Every versioned controller inherits from this abstract base. It defines the default route constant, route prefix, and an OpenAPI doc entry for Scalar documentation.

```csharp
namespace {Company}.Gateways.{Domain}.Controllers.V1;

[ApiController]
[ApiExplorerSettings(GroupName = "v1")]
[Authorize]
public abstract class ControllerBaseV1 : ControllerBase
{
    public const string DefaultRoute = "api/v1/[controller]";
    public const string RoutePrefix = "api/v1/";

    public static OpenApiDocEntry GetDocEntry() => new DevelopmentOpenApiDocEntry(
        Name: "v1",
        new() { Title = "{Domain} Management V1 API's", Version = "v1" });
}
```

### Simple Query Controller — Direct gRPC Client Injection

Inject the gRPC client via primary constructor. Map gRPC response to REST DTO inline using `Select`.

```csharp
namespace {Company}.Gateways.{Domain}.Controllers.V1;

[Route(DefaultRoute)]
[Authorize(Policy = Policy.Operator)]
public class ProductsController(
    ProductManagement.ProductManagementClient productClient) : ControllerBaseV1
{
    private readonly ProductManagement.ProductManagementClient _productClient = productClient;

    [HttpGet]
    public async Task<ActionResult<GetProductsOutput>> GetProductsAsync()
    {
        var response = await _productClient.FetchAllAsync(new EmptyRequest { });

        return Ok(new GetProductsOutput
        {
            Products = response.Products.Select(p => new ProductModel
            {
                Id = Guid.Parse(p.Id),
                Name = p.Name,
                Code = p.Code,
            })
        });
    }
}
```

### Full CRUD Controller with Paginated Queries

Controllers that handle both commands and queries inject multiple gRPC clients. Command methods build gRPC request objects inline and return `Response { Message }`. Query methods map gRPC responses to output DTOs and wrap lists in `Paginated<T>`.

```csharp
namespace {Company}.Gateways.{Domain}.Controllers.V1;

[Route(DefaultRoute)]
[Authorize(Roles = $"{Roles.SuperAdmin},{Roles.Admin}")]
public class OrdersController(
    OrderCommands.OrderCommandsClient commandsClient,
    OrderManagementQueries.OrderManagementQueriesClient queriesClient,
    ILogger<OrdersController> logger) : ControllerBaseV1
{
    private readonly OrderCommands.OrderCommandsClient _commandsClient = commandsClient;
    private readonly OrderManagementQueries.OrderManagementQueriesClient _queriesClient = queriesClient;
    private readonly ILogger<OrdersController> _logger = logger;

    [HttpPost("{id}")]
    public async Task<ActionResult<Response>> CreateOrder(
        Guid id, [FromBody] CreateOrderModel model)
    {
        var response = await _commandsClient.CreateOrderAsync(new CreateOrderRequest
        {
            Id = id.ToString(),
            Name = model.Name,
            Description = model.Description,
            StartDate = model.StartDate.ToTimestamp(),
            Status = (Proto.OrderStatus)model.Status,
            Items = { model.Items.Select(x => x.ToString()) },
        });

        return new Response { Message = response.Message };
    }

    [HttpPut("{id}")]
    public async Task<ActionResult<Response>> UpdateOrderAsync(
        Guid id, [FromBody] UpdateOrderModel model)
    {
        var response = await _commandsClient.UpdateOrderAsync(new UpdateOrderRequest
        {
            Id = id.ToString(),
            Name = model.Name,
            Description = model.Description,
        });

        return new Response { Message = response.Message };
    }

    [HttpGet]
    public async Task<ActionResult<Paginated<OrderOutput>>> GetOrdersAsync(
        [FromQuery] GetOrdersFilterModel filterModel)
    {
        var response = await _queriesClient.GetOrdersAsync(new GetOrdersRequest
        {
            PageSize = filterModel.PageSize,
            CurrentPage = filterModel.CurrentPage,
            StartDateFrom = filterModel.StartDateFrom.ToTimestamp(),
            StartDateTo = filterModel.StartDateTo.ToTimestamp(),
            Status = (QueryProto.OrderStatus)filterModel.Status,
        });

        var output = response.Orders.Select(x => new OrderOutput
        {
            Id = Guid.Parse(x.Id),
            Name = x.Name,
            Description = x.Description,
            StartDate = x.StartDate.ToDateTime(),
            Status = (Models.Enums.OrderStatus)x.Status,
        });

        return new Paginated<OrderOutput>(
            output, response.CurrentPage, response.PageSize, response.Total);
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<OrderDetailOutput>> GetOrderAsync(Guid id)
    {
        var response = await _queriesClient.GetOrderDetailsAsync(
            new GetOrderDetailsRequest { Id = id.ToString() });

        return new OrderDetailOutput
        {
            Order = new OrderOutput
            {
                Id = Guid.Parse(response.Order.Id),
                Name = response.Order.Name,
                StartDate = response.Order.StartDate.ToDateTime(),
                Status = (Models.Enums.OrderStatus)response.Order.Status,
            },
            Items = response.Items.Select(Guid.Parse),
        };
    }
}
```

### gRPC Error Handling in Controllers

For specific endpoints needing custom error handling, catch `RpcException` and return `ProblemDetails`. The global `HttpResponseExceptionFilter` handles most cases automatically.

```csharp
[HttpGet("items")]
[ProducesResponseType(typeof(Paginated<ItemOutput>), StatusCodes.Status200OK)]
public async Task<ActionResult<Paginated<ItemOutput>>> GetItemsAsync(
    [FromQuery] int page = 1,
    [FromQuery] int pageSize = 20,
    [FromQuery] string? searchName = null)
{
    try
    {
        var request = new GetItemsRequest { Page = page, PageSize = pageSize };

        if (!string.IsNullOrEmpty(searchName))
            request.SearchName = searchName;

        var response = await _queriesClient.GetItemsAsync(request);

        return Ok(new Paginated<ItemOutput>(
            response.Items.Select(i => i.ToItemOutput()),
            response.Page, response.PageSize, response.TotalCount));
    }
    catch (RpcException ex)
    {
        _logger.LogError(ex,
            "gRPC error in {Method} -- StatusCode: {StatusCode}",
            nameof(GetItemsAsync), ex.StatusCode);

        return StatusCode(StatusCodes.Status502BadGateway, new ProblemDetails
        {
            Title = "Upstream service error",
            Detail = ex.Status.Detail,
            Status = StatusCodes.Status502BadGateway
        });
    }
}
```

### Paginated Response Model

```csharp
namespace {Company}.Gateways.Common.Models;

public class Paginated<TItem>(
    IEnumerable<TItem> results, int currentPage, int pageSize, int total)
{
    public IEnumerable<TItem> Results { get; } = results;
    public int CurrentPage { get; } = currentPage;
    public int PageSize { get; } = pageSize;
    public int Total { get; } = total;
    public int LastPage => PageSize == 0 ? 0
        : Total % PageSize <= 0 ? Total / PageSize
        : (Total / PageSize) + 1;
}
```

### Response Model for Commands

```csharp
namespace {Company}.Gateways.{Domain}.Models;

public class Response
{
    public required string Message { get; set; }
}
```

### Request/Response DTOs

Request models use `class` with `required` properties. Output models follow the same pattern.

```csharp
namespace {Company}.Gateways.{Domain}.Models.Requests;

public class CreateOrderModel : UpdateOrderModel
{
    public required List<Guid> Items { get; init; }
    public required List<DateTime> Dates { get; init; }
}
```

```csharp
namespace {Company}.Gateways.{Domain}.Models.Responses;

public class OrderOutput
{
    public required Guid Id { get; init; }
    public required string Name { get; init; }
    public required string Description { get; init; }
    public required DateTime StartDate { get; init; }
    public required OrderStatus Status { get; init; }
}
```

### Enum Mapping Extensions (Only When Needed)

Separate extension methods only for enum conversions between proto and domain types.

```csharp
namespace {Company}.Gateways.{Domain}.Extensions;

using CommandProto = {Company}.{Domain}.GrpcClients.Protos.Commands;
using QueryProto = {Company}.{Domain}.GrpcClients.Protos.Queries;

public static class OrderExtensions
{
    public static CommandProto.ItemType ToProtoEnum(this Models.Enums.ItemType itemType)
        => itemType switch
        {
            Models.Enums.ItemType.Physical => CommandProto.ItemType.Physical,
            Models.Enums.ItemType.Digital => CommandProto.ItemType.Digital,
            _ => throw new ArgumentOutOfRangeException(nameof(itemType))
        };

    public static Models.Enums.ItemType ToDomainEnum(this QueryProto.ItemType itemType)
        => itemType switch
        {
            QueryProto.ItemType.Physical => Models.Enums.ItemType.Physical,
            QueryProto.ItemType.Digital => Models.Enums.ItemType.Digital,
            _ => throw new ArgumentOutOfRangeException(nameof(itemType))
        };
}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Inheriting raw `ControllerBase` | Inherit `ControllerBaseV1` with shared route/docs |
| Separate mapping extension classes for all fields | Map inline in controller actions |
| Business logic in gateway controller | Gateway only maps and delegates to gRPC |
| Exposing gRPC proto types in REST response | Map to REST-specific DTOs |
| Missing `[Authorize]` on controller class | Apply at class level, use Policy or Roles |
| Constructor injection without backing field | Assign to `private readonly` field |
| Returning raw gRPC response | Wrap in `Response { Message }` for commands |

## Detect Existing Patterns

```bash
# Find gateway controllers
grep -r "ControllerBaseV1\|: ControllerBase" --include="*.cs" Controllers/

# Find gRPC client injection
grep -r "CommandsClient\|QueriesClient\|ManagementClient" --include="*.cs" Controllers/

# Find Paginated usage
grep -r "Paginated<" --include="*.cs"

# Find authorization attributes
grep -r "\[Authorize" --include="*.cs" Controllers/
```

## Adding to Existing Project

1. **Inherit `ControllerBaseV1`** and use `[Route(DefaultRoute)]`
2. **Inject gRPC clients** via primary constructor with backing `readonly` fields
3. **Map inline** in each action -- build gRPC request, map response to DTO
4. **Return `Paginated<T>`** for list endpoints using constructor args
5. **Return `Response { Message }`** for command endpoints
6. **Apply `[Authorize]`** at class level with Policy or Roles
7. **Register gRPC clients** via the endpoint-registration skill
