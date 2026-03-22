using Microsoft.AspNetCore.Components.WebAssembly.Hosting;
using MudBlazor;
using MudBlazor.Services;
using {{ Company }}.ControlPanel.{{ Domain }}.Gateways;
using {{ Company }}.ControlPanel.{{ Domain }}.Services;

var builder = WebAssemblyHostBuilder.CreateDefault(args);
builder.RootComponents.Add<App>("#app");

builder.Services.AddServerApiClients(builder.Configuration);

builder.Services.AddMudServices(config =>
{
    config.SnackbarConfiguration.PositionClass = Defaults.Classes.Position.BottomRight;
});

builder.Services.AddLocalization();
builder.Services.AddScoped<MenuItemsProvider>();

await builder.Build().RunAsync();
