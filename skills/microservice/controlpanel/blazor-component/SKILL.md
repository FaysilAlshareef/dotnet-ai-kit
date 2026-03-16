---
name: blazor-component
description: >
  MudBlazor components for control panel pages. Covers MudDataGrid with server-side
  data, MudDialog for forms, loading states, and gateway integration.
  Trigger: Blazor, MudBlazor, MudDataGrid, data grid, dialog, form.
category: microservice/controlpanel
agent: controlpanel-architect
---

# Blazor Component — MudBlazor Page Patterns

## Core Principles

- Control panel uses **Blazor Server** (or WASM) with MudBlazor component library
- `MudDataGrid<T>` with `ServerData` callback for server-side pagination
- `MudDialog` for create/edit forms
- Gateway facade handles API calls; `ResponseResult<T>.Switch()` handles results
- Loading states and error handling via Snackbar
- Filter model syncs with URL query string

## Key Patterns

### Data Grid Page

```razor
@page "/orders"
@inject OrdersGateway Gateway
@inject ISnackbar Snackbar
@inject NavigationManager NavigationManager

<MudText Typo="Typo.h4" Class="mb-4">Orders</MudText>

<MudDataGrid T="OrderSummaryResponse"
             ServerData="LoadServerData"
             @ref="_dataGrid"
             Filterable="false"
             Loading="_loading">

    <ToolBarContent>
        <MudTextField @bind-Value="_filter.Search"
                      Placeholder="Search..."
                      Adornment="Adornment.Start"
                      AdornmentIcon="@Icons.Material.Filled.Search"
                      DebounceInterval="300"
                      OnDebounceIntervalElapsed="OnSearchChanged" />
        <MudSpacer />
        <MudButton Variant="Variant.Filled" Color="Color.Primary"
                   OnClick="OpenCreateDialog">New Order</MudButton>
    </ToolBarContent>

    <Columns>
        <PropertyColumn Property="x => x.CustomerName" Title="Customer" />
        <PropertyColumn Property="x => x.Total" Title="Total" Format="C2" />
        <PropertyColumn Property="x => x.Status" Title="Status" />
        <TemplateColumn>
            <CellTemplate>
                <MudIconButton Icon="@Icons.Material.Filled.Edit"
                               OnClick="() => OpenEditDialog(context.Item)" />
            </CellTemplate>
        </TemplateColumn>
    </Columns>

    <PagerContent>
        <MudDataGridPager T="OrderSummaryResponse" />
    </PagerContent>
</MudDataGrid>

@code {
    private MudDataGrid<OrderSummaryResponse>? _dataGrid;
    private OrderFilterModel _filter = new();
    private bool _loading;

    private async Task<GridData<OrderSummaryResponse>> LoadServerData(
        GridState<OrderSummaryResponse> state)
    {
        _loading = true;
        var result = await Gateway.GetAllAsync(
            state.Page + 1, state.PageSize, _filter.Search);

        GridData<OrderSummaryResponse> data = new([], 0);

        result.Switch(
            onSuccess: paginated =>
            {
                data = new GridData<OrderSummaryResponse>(
                    paginated.Items, paginated.TotalCount);
            },
            onFailure: problem =>
            {
                Snackbar.Add(problem.Detail ?? "Failed to load orders",
                    Severity.Error);
            });

        _loading = false;
        return data;
    }

    private async Task OnSearchChanged()
    {
        if (_dataGrid is not null)
            await _dataGrid.ReloadServerData();
    }

    private async Task OpenCreateDialog()
    {
        var dialog = await DialogService.ShowAsync<CreateOrderDialog>("New Order");
        var result = await dialog.Result;
        if (!result.Canceled && _dataGrid is not null)
            await _dataGrid.ReloadServerData();
    }
}
```

### Dialog Component

```razor
@* CreateOrderDialog.razor *@
<MudDialog>
    <DialogContent>
        <MudForm @ref="_form" @bind-IsValid="_valid">
            <MudTextField @bind-Value="_model.CustomerName"
                          Label="Customer Name"
                          Required="true"
                          RequiredError="Customer name is required" />
            <MudNumericField @bind-Value="_model.Total"
                             Label="Total"
                             Min="0.01M" />
        </MudForm>
    </DialogContent>
    <DialogActions>
        <MudButton OnClick="Cancel">Cancel</MudButton>
        <MudButton Color="Color.Primary"
                   Disabled="!_valid"
                   OnClick="Submit">Create</MudButton>
    </DialogActions>
</MudDialog>

@code {
    [CascadingParameter] private IMudDialogInstance MudDialog { get; set; } = null!;
    [Inject] private OrdersGateway Gateway { get; set; } = null!;
    [Inject] private ISnackbar Snackbar { get; set; } = null!;

    private MudForm? _form;
    private bool _valid;
    private CreateOrderModel _model = new();

    private void Cancel() => MudDialog.Cancel();

    private async Task Submit()
    {
        var result = await Gateway.CreateAsync(_model.ToRequest());
        result.Switch(
            onSuccess: _ =>
            {
                Snackbar.Add("Order created", Severity.Success);
                MudDialog.Close(DialogResult.Ok(true));
            },
            onFailure: problem =>
            {
                Snackbar.Add(problem.Detail ?? "Creation failed", Severity.Error);
            });
    }
}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Client-side filtering for large datasets | Use ServerData callback |
| Direct HTTP calls in components | Use Gateway facade classes |
| Missing loading states | Show loading indicator during API calls |
| No error handling | Use Switch pattern with Snackbar |

## Detect Existing Patterns

```bash
# Find MudDataGrid usage
grep -r "MudDataGrid" --include="*.razor" src/ControlPanel/

# Find dialog components
grep -r "MudDialog" --include="*.razor" src/ControlPanel/

# Find gateway injection
grep -r "@inject.*Gateway" --include="*.razor" src/ControlPanel/
```

## Adding to Existing Project

1. **Follow existing page layout** — check `Shared/MainLayout.razor`
2. **Use existing gateway facade** pattern for API calls
3. **Match dialog patterns** — check existing dialogs for conventions
4. **Add page route** and menu item registration
5. **Use `ResponseResult.Switch`** for all gateway call results
