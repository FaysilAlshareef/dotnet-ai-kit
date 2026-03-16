---
name: gateway-facade
description: >
  Gateway management class hierarchy for control panel API calls. Covers typed
  HttpClient wrappers, nested management classes, HTTP extension methods.
  Trigger: gateway facade, HttpClient, API client, management class.
category: microservice/controlpanel
agent: controlpanel-architect
---

# Gateway Facade — Typed HttpClient Wrappers

## Core Principles

- Gateway class wraps `HttpClient` for calling gateway REST endpoints
- Nested management classes organize endpoints by domain entity
- Lazy initialization (`??=` pattern) for management classes
- `HttpExtensions` provide consistent serialization and error handling
- All methods return `ResponseResult<T>` for uniform error handling

## Key Patterns

### Gateway Class with Nested Management

```csharp
namespace {Company}.{Domain}.ControlPanel.Gateways;

public sealed class OrderGateway(HttpClient http)
{
    private OrderManagement? _orders;
    private CustomerManagement? _customers;

    public OrderManagement Orders => _orders ??= new(http);
    public CustomerManagement Customers => _customers ??= new(http);
}
```

### Management Class

```csharp
namespace {Company}.{Domain}.ControlPanel.Gateways;

public sealed class OrderManagement(HttpClient http)
{
    private const string BaseRoute = "api/v1/orders";

    public async Task<ResponseResult<Paginated<OrderSummaryResponse>>> GetAllAsync(
        int page, int pageSize, string? search = null)
    {
        var url = $"{BaseRoute}?page={page}&pageSize={pageSize}";
        if (!string.IsNullOrEmpty(search))
            url += $"&search={Uri.EscapeDataString(search)}";

        return await http.GetAsync<Paginated<OrderSummaryResponse>>(url);
    }

    public async Task<ResponseResult<OrderDetailResponse>> GetByIdAsync(Guid id)
        => await http.GetAsync<OrderDetailResponse>($"{BaseRoute}/{id}");

    public async Task<ResponseResult<OrderResponse>> CreateAsync(
        CreateOrderRequest request)
        => await http.PostAsJsonAsync<OrderResponse>(BaseRoute, request);

    public async Task<ResponseResult<OrderResponse>> UpdateAsync(
        Guid id, UpdateOrderRequest request)
        => await http.PutAsJsonAsync<OrderResponse>($"{BaseRoute}/{id}", request);

    public async Task<ResponseResult<bool>> DeleteAsync(Guid id)
        => await http.DeleteAsync<bool>($"{BaseRoute}/{id}");
}
```

### HTTP Extension Methods

```csharp
namespace {Company}.{Domain}.ControlPanel.Extensions;

public static class HttpExtensions
{
    public static async Task<ResponseResult<T>> GetAsync<T>(
        this HttpClient http, string url)
    {
        try
        {
            var response = await http.GetAsync(url);
            return await HandleResponse<T>(response);
        }
        catch (Exception ex)
        {
            return ResponseResult<T>.Failure(ex.Message);
        }
    }

    public static async Task<ResponseResult<T>> PostAsJsonAsync<T>(
        this HttpClient http, string url, object content)
    {
        try
        {
            var response = await http.PostAsJsonAsync(url, content);
            return await HandleResponse<T>(response);
        }
        catch (Exception ex)
        {
            return ResponseResult<T>.Failure(ex.Message);
        }
    }

    public static async Task<ResponseResult<T>> PutAsJsonAsync<T>(
        this HttpClient http, string url, object content)
    {
        try
        {
            var response = await http.PutAsJsonAsync(url, content);
            return await HandleResponse<T>(response);
        }
        catch (Exception ex)
        {
            return ResponseResult<T>.Failure(ex.Message);
        }
    }

    private static async Task<ResponseResult<T>> HandleResponse<T>(
        HttpResponseMessage response)
    {
        if (response.IsSuccessStatusCode)
        {
            var data = await response.Content
                .ReadFromJsonAsync<T>();
            return ResponseResult<T>.Success(data!);
        }

        var problem = await response.Content
            .ReadFromJsonAsync<ProblemDetails>();
        return ResponseResult<T>.Failure(
            problem?.Detail ?? $"HTTP {(int)response.StatusCode}");
    }
}
```

### Registration

```csharp
public static IServiceCollection AddGatewayClients(
    this IServiceCollection services, IConfiguration configuration)
{
    var gatewayUrl = configuration["GatewayUrl"]!;

    services.AddHttpClient<OrderGateway>(client =>
    {
        client.BaseAddress = new Uri(gatewayUrl);
    });

    return services;
}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Direct HttpClient in components | Use gateway facade classes |
| No error handling in HTTP calls | Wrap in try/catch, return ResponseResult |
| Hardcoded URLs | Use BaseRoute constants and configuration |
| Missing serialization handling | Use HttpExtensions for consistency |

## Detect Existing Patterns

```bash
# Find gateway classes
grep -r "Gateway.*HttpClient\|Management.*HttpClient" --include="*.cs" src/ControlPanel/

# Find HttpExtensions
grep -r "HttpExtensions\|GetAsync<\|PostAsJsonAsync<" --include="*.cs" src/ControlPanel/

# Find gateway registration
grep -r "AddHttpClient<.*Gateway" --include="*.cs" src/ControlPanel/
```

## Adding to Existing Project

1. **Follow the nested management class pattern** — Gateway → Management
2. **Use existing `HttpExtensions`** for all HTTP calls
3. **Return `ResponseResult<T>`** from all management methods
4. **Register gateway** as typed HttpClient in DI
5. **Use route constants** matching gateway controller routes
