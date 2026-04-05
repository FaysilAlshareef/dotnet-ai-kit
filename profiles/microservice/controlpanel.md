---
alwaysApply: true
description: "Architecture profile for control panel projects — hard constraints"
---

# Architecture Profile: Control Panel (Blazor + MudBlazor)

## HARD CONSTRAINTS

### Blazor Component Patterns
- MUST use `MudDataGrid<T>` with `ServerData` callback for all paginated data — NEVER client-side filtering
- MUST use `MudDialog` via `IDialogService` for forms and confirmations — NEVER custom modals
- MUST use `MudSnackbar` for all user notifications — NEVER alert boxes or inline messages
- MUST show loading indicators (`MudProgressCircular`/`Loading` property) during API calls
- MUST use `MudForm` with validation for all input forms
- MUST reload data grid after successful create/edit/delete via `_dataGrid.ReloadServerData()`

```csharp
// ANTI-PATTERN: client-side filtering
<MudDataGrid Items="_allOrders"> // WRONG — loads everything

// CORRECT: server-side data
<MudDataGrid ServerData="LoadServerData"> // Fetches per page
```

### Gateway Facade Pattern
- MUST use typed gateway facade classes for all API calls — NEVER direct `HttpClient` in components
- MUST use nested management classes (`Gateway.Orders`, `Gateway.Customers`) for organization
- MUST use lazy initialization (`??=` pattern) for management class properties
- MUST return `ResponseResult<T>` from all management methods — NEVER raw HTTP responses
- MUST use `HttpExtensions` (`GetAsync<T>`, `PostAsJsonAsync<T>`) for consistent serialization
- MUST register gateways as typed HttpClients via `AddHttpClient<TGateway>`

### ResponseResult Switch Pattern
- MUST use `ResponseResult<T>.Switch()` for all gateway call results — NEVER null checks
- MUST handle both `onSuccess` and `onFailure` in every Switch call — NEVER ignore failures
- `onFailure` MUST display error via `Snackbar.Add(problem.Detail, Severity.Error)`
- `onSuccess` MUST provide user feedback via Snackbar for mutation operations
- NEVER use try/catch in UI components for API errors — `ResponseResult` encapsulates errors

```csharp
// ANTI-PATTERN: null checking
var result = await Gateway.Orders.GetByIdAsync(id);
if (result != null) { ... } // WRONG

// CORRECT: Switch pattern
result.Switch(
    onSuccess: order => _order = order,
    onFailure: problem => Snackbar.Add(problem.Detail ?? "Failed", Severity.Error));
```

### MudBlazor Conventions
- MUST use `MudTheme` for consistent theming — NEVER inline colors or styles
- MUST use `IMudDialogInstance` as `[CascadingParameter]` in dialog components
- MUST use `MudDialog.Close(DialogResult.Ok(true))` on success — NEVER just `Close()`
- MUST use `MudDialog.Cancel()` for cancellation
- MUST use `DialogParameters<T>` with typed lambda for passing parameters
- MUST set `Dense="true"` on data-heavy tables and grids

### Query String Binding
- MUST use `QueryStringBindable` base class for filter models — NEVER unsynced filter state
- Filter changes MUST update the browser URL (bookmarkable, shareable)
- MUST use `NavigateTo` with `replace: true` — NEVER full page reload on filter change
- MUST bind in `OnInitialized` via `BindToNavigationManager` — NEVER on every render
- MUST debounce text search fields (300ms) — NEVER fire API calls on every keystroke

### Component Organization
- `[Inject]` for services in dialog code-behind — NEVER constructor injection in components
- `@inject` directive for services in page components
- MUST use `[CascadingParameter]` for `IMudDialogInstance` — NEVER pass via parameter
- MUST follow naming: `{Entity}FilterModel`, `{Entity}Gateway`, `{Action}{Entity}Dialog`

## Testing Requirements

- MUST test gateway facade methods return correct `ResponseResult` types
- MUST test filter model serialization to/from query string
- MUST verify loading states toggle correctly during API calls

## Data Access

- Control panel has NO direct database access — ALWAYS use gateway facade
- MUST use route constants matching gateway controller routes
- Gateway base URLs MUST come from configuration — NEVER hardcode
