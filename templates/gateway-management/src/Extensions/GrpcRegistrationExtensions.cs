namespace {{ Company }}.Gateways.{{ Domain }}.Management.Extensions;

public static class GrpcRegistrationExtensions
{
    public static IServiceCollection AddGrpcClients(
        this IServiceCollection services, IConfiguration configuration)
    {
        // Register gRPC clients per backing service:
        // services.AddGrpcClient<CommandService.CommandServiceClient>((sp, options) =>
        // {
        //     var urls = sp.GetRequiredService<IOptions<ServicesUrlsOptions>>().Value;
        //     options.Address = new Uri(urls.CommandServiceUrl);
        // });

        return services;
    }
}
