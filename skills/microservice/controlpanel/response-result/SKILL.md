---
name: response-result
description: >
  ResponseResult<T> pattern with Switch for success/failure handling. Covers
  SuccessResult, FailedResult, ProblemDetails parsing, and UI integration.
  Trigger: ResponseResult, Switch pattern, error handling, result pattern.
metadata:
  category: microservice/controlpanel
  agent: controlpanel-architect
  when-to-use: "When implementing ResponseResult Switch pattern or gateway call error handling"
---

# ResponseResult<T> — Switch Pattern

## Core Principles

- `ResponseResult<T>` encapsulates success or failure from gateway calls
- `Switch()` routes to appropriate handler (success action or failure action)
- `SwitchAsync()` for async handlers
- Failed results carry `ProblemDetails` for structured error information
- Snackbar displays success/failure messages to user
- Eliminates null checking and exception handling in UI code

## Key Patterns

### ResponseResult Type

```csharp
namespace {Company}.{Domain}.ControlPanel.Models;

public abstract record ResponseResult<T>
{
    public static ResponseResult<T> Success(T data) => new SuccessResult<T>(data);
    public static ResponseResult<T> Failure(string detail) =>
        new FailedResult<T>(new ProblemDetails { Detail = detail });
    public static ResponseResult<T> Failure(ProblemDetails problem) =>
        new FailedResult<T>(problem);
}

public sealed record SuccessResult<T>(T Data) : ResponseResult<T>;

public sealed record FailedResult<T>(ProblemDetails Problem) : ResponseResult<T>;
```

### Switch Extension Methods

```csharp
namespace {Company}.{Domain}.ControlPanel.Extensions;

public static class ResponseResultExtensions
{
    public static void Switch<T>(
        this ResponseResult<T> result,
        Action<T> onSuccess,
        Action<ProblemDetails> onFailure)
    {
        switch (result)
        {
            case SuccessResult<T> success:
                onSuccess(success.Data);
                break;
            case FailedResult<T> failed:
                onFailure(failed.Problem);
                break;
        }
    }

    public static async Task SwitchAsync<T>(
        this ResponseResult<T> result,
        Func<T, Task> onSuccess,
        Func<ProblemDetails, Task> onFailure)
    {
        switch (result)
        {
            case SuccessResult<T> success:
                await onSuccess(success.Data);
                break;
            case FailedResult<T> failed:
                await onFailure(failed.Problem);
                break;
        }
    }

    public static T? GetDataOrDefault<T>(this ResponseResult<T> result) =>
        result is SuccessResult<T> success ? success.Data : default;

    public static bool IsSuccess<T>(this ResponseResult<T> result) =>
        result is SuccessResult<T>;
}
```

### Usage in Blazor Components

```csharp
// Create operation with Snackbar feedback
private async Task CreateOrder()
{
    var result = await Gateway.Orders.CreateAsync(request);

    result.Switch(
        onSuccess: order =>
        {
            Snackbar.Add("Order created successfully", Severity.Success);
            NavigationManager.NavigateTo($"/orders/{order.Id}");
        },
        onFailure: problem =>
        {
            Snackbar.Add(problem.Detail ?? "Failed to create order",
                Severity.Error);
        });
}

// Load data with error handling
private async Task LoadOrderDetails(Guid id)
{
    _loading = true;
    var result = await Gateway.Orders.GetByIdAsync(id);

    result.Switch(
        onSuccess: order => _order = order,
        onFailure: problem =>
        {
            Snackbar.Add(problem.Detail ?? "Order not found", Severity.Error);
            NavigationManager.NavigateTo("/orders");
        });
    _loading = false;
    StateHasChanged();
}

// Conditional rendering based on result
@if (_order is not null)
{
    <OrderDetails Order="_order" />
}
else if (_loading)
{
    <MudProgressCircular Indeterminate="true" />
}
```

### Server Data Grid Integration

```csharp
private async Task<GridData<OrderSummaryResponse>> LoadServerData(
    GridState<OrderSummaryResponse> state)
{
    var result = await Gateway.Orders.GetAllAsync(
        state.Page + 1, state.PageSize);

    return result switch
    {
        SuccessResult<Paginated<OrderSummaryResponse>> s =>
            new GridData<OrderSummaryResponse>(s.Data.Items, s.Data.TotalCount),
        _ => new GridData<OrderSummaryResponse>([], 0)
    };
}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Null checks instead of Switch | Use Switch for explicit success/failure |
| Try/catch in UI components | ResponseResult encapsulates errors |
| Ignoring failure results | Always handle failure with user feedback |
| Generic error messages | Use ProblemDetails.Detail for specific messages |

## Detect Existing Patterns

```bash
# Find ResponseResult types
grep -r "ResponseResult<" --include="*.cs" src/ControlPanel/

# Find Switch usage
grep -r "\.Switch(" --include="*.cs" src/ControlPanel/
grep -r "\.Switch(" --include="*.razor" src/ControlPanel/

# Find SuccessResult/FailedResult
grep -r "SuccessResult\|FailedResult" --include="*.cs" src/ControlPanel/
```

## Adding to Existing Project

1. **Use existing `ResponseResult<T>`** type — do not create a new one
2. **Follow `Switch` pattern** for all gateway call results
3. **Use Snackbar** for user feedback (success and error)
4. **Handle loading states** with `_loading` flag and `MudProgressCircular`
5. **Navigate on success** where appropriate (e.g., after create/delete)
