using {{ Company }}.ControlPanel.{{ Domain }}.Gateways;

namespace {{ Company }}.ControlPanel.{{ Domain }}.Services;

public static class WebAppRegistration
{
    public static IServiceCollection AddServerApiClients(
        this IServiceCollection services, IConfiguration configuration)
    {
        services.AddHttpClient<Gateway>(client =>
        {
            client.BaseAddress = new Uri(configuration["GatewayBaseUrl"]!);
        });

        return services;
    }
}
