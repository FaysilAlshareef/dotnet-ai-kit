namespace {{ Company }}.ControlPanel.{{ Domain }}.Services;

/// <summary>
/// Provides MudNavMenu items for this module.
/// Integrates with the main ControlPanel shell navigation.
/// </summary>
public class MenuItemsProvider
{
    public record MenuItem(string Title, string Icon, string Href, string? Group = null);

    public IReadOnlyList<MenuItem> GetMenuItems() =>
    [
        new("{{ Domain }}", "dashboard", "/{{ domain }}")
    ];
}
