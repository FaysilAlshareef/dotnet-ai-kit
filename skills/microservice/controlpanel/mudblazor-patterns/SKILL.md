---
name: mudblazor-patterns
description: >
  Use when applying MudBlazor theming, dialog patterns, or snackbar integration.
metadata:
  category: microservice/controlpanel
  agent: controlpanel-architect
  when-to-use: "When configuring MudBlazor theming, dialogs, or snackbar integration"
---

# MudBlazor Patterns — Theming, Dialogs, Snackbar

## Core Principles

- MudBlazor provides Material Design components for Blazor
- Custom theme for consistent branding across control panels
- Dialog service for modal forms and confirmations
- Snackbar for user notifications (success, error, warning)
- `MudExpansionPanels` for collapsible detail sections
- `MudCard` for content grouping

## Key Patterns

### Theme Configuration

```csharp
namespace {Company}.{Domain}.ControlPanel.Configuration;

public static class ThemeConfiguration
{
    public static MudTheme AppTheme => new()
    {
        PaletteLight = new PaletteLight
        {
            Primary = "#1976D2",
            Secondary = "#424242",
            AppbarBackground = "#1976D2",
            Background = "#F5F5F5",
            DrawerBackground = "#FFFFFF",
            Success = "#4CAF50",
            Error = "#F44336",
            Warning = "#FF9800"
        },
        Typography = new Typography
        {
            Default = new DefaultTypography
            {
                FontFamily = ["Roboto", "Helvetica", "Arial", "sans-serif"]
            }
        },
        LayoutProperties = new LayoutProperties
        {
            DrawerWidthLeft = "260px"
        }
    };
}
```

### MainLayout with Theme

```razor
@inherits LayoutComponentBase

<MudThemeProvider Theme="ThemeConfiguration.AppTheme" />
<MudPopoverProvider />
<MudDialogProvider />
<MudSnackbarProvider />

<MudLayout>
    <MudAppBar Elevation="1">
        <MudIconButton Icon="@Icons.Material.Filled.Menu"
                       Color="Color.Inherit"
                       OnClick="ToggleDrawer" />
        <MudText Typo="Typo.h6">{Company} Control Panel</MudText>
    </MudAppBar>

    <MudDrawer @bind-Open="_drawerOpen" Elevation="2">
        <NavMenu />
    </MudDrawer>

    <MudMainContent Class="pa-4">
        @Body
    </MudMainContent>
</MudLayout>
```

### Confirmation Dialog

```razor
@* ConfirmDialog.razor *@
<MudDialog>
    <DialogContent>
        <MudText>@ContentText</MudText>
    </DialogContent>
    <DialogActions>
        <MudButton OnClick="Cancel">Cancel</MudButton>
        <MudButton Color="@Color" Variant="Variant.Filled"
                   OnClick="Submit">@ButtonText</MudButton>
    </DialogActions>
</MudDialog>

@code {
    [CascadingParameter] private IMudDialogInstance MudDialog { get; set; } = null!;
    [Parameter] public string ContentText { get; set; } = "";
    [Parameter] public string ButtonText { get; set; } = "Confirm";
    [Parameter] public Color Color { get; set; } = Color.Primary;

    private void Cancel() => MudDialog.Cancel();
    private void Submit() => MudDialog.Close(DialogResult.Ok(true));
}
```

### Using Confirmation Dialog

```csharp
private async Task DeleteOrder(Guid orderId)
{
    var parameters = new DialogParameters<ConfirmDialog>
    {
        { x => x.ContentText, "Are you sure you want to delete this order?" },
        { x => x.ButtonText, "Delete" },
        { x => x.Color, Color.Error }
    };

    var dialog = await DialogService.ShowAsync<ConfirmDialog>("Confirm", parameters);
    var result = await dialog.Result;

    if (!result.Canceled)
    {
        var response = await Gateway.Orders.DeleteAsync(orderId);
        response.Switch(
            onSuccess: _ =>
            {
                Snackbar.Add("Order deleted", Severity.Success);
                await _dataGrid!.ReloadServerData();
            },
            onFailure: p => Snackbar.Add(p.Detail ?? "Delete failed", Severity.Error));
    }
}
```

### Snackbar Configuration

```csharp
// Program.cs
services.AddMudServices(config =>
{
    config.SnackbarConfiguration.PositionClass = Defaults.Classes.Position.BottomRight;
    config.SnackbarConfiguration.PreventDuplicates = false;
    config.SnackbarConfiguration.NewestOnTop = true;
    config.SnackbarConfiguration.ShowCloseIcon = true;
    config.SnackbarConfiguration.VisibleStateDuration = 5000;
    config.SnackbarConfiguration.SnackbarVariant = Variant.Filled;
});
```

### Expansion Panel Detail View

```razor
<MudExpansionPanels MultiExpansion="true">
    <MudExpansionPanel Text="Order Details" IsInitiallyExpanded="true">
        <MudSimpleTable Dense="true">
            <tbody>
                <tr><td>Customer</td><td>@_order.CustomerName</td></tr>
                <tr><td>Total</td><td>@_order.Total.ToString("C2")</td></tr>
                <tr><td>Status</td><td><MudChip T="string" Color="StatusColor">@_order.Status</MudChip></td></tr>
            </tbody>
        </MudSimpleTable>
    </MudExpansionPanel>

    <MudExpansionPanel Text="Order Items">
        <MudTable Items="_order.Items" Dense="true" Hover="true">
            <HeaderContent>
                <MudTh>Product</MudTh>
                <MudTh>Qty</MudTh>
                <MudTh>Price</MudTh>
            </HeaderContent>
            <RowTemplate>
                <MudTd>@context.ProductName</MudTd>
                <MudTd>@context.Quantity</MudTd>
                <MudTd>@context.UnitPrice.ToString("C2")</MudTd>
            </RowTemplate>
        </MudTable>
    </MudExpansionPanel>
</MudExpansionPanels>
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Inline colors and styles | Use MudTheme for consistent theming |
| Alert boxes for notifications | Use MudSnackbar |
| Custom modal implementation | Use MudDialog service |
| Missing loading indicators | Use MudProgressCircular/Linear |

## Detect Existing Patterns

```bash
# Find MudBlazor theme
grep -r "MudTheme\|PaletteLight" --include="*.cs" src/ControlPanel/

# Find dialog service usage
grep -r "DialogService.Show" --include="*.razor" src/ControlPanel/

# Find snackbar configuration
grep -r "AddMudServices\|SnackbarConfiguration" --include="*.cs" src/ControlPanel/
```

## Adding to Existing Project

1. **Use existing theme** — do not create separate themes
2. **Follow dialog patterns** — check existing dialog components
3. **Use Snackbar consistently** for all user notifications
4. **Match component density** — Dense="true" for data-heavy pages
5. **Add menu item** in `NavMenu` for new pages
