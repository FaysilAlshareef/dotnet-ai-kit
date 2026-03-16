namespace {{ Company }}.Gateways.{{ Domain }}.Consumers.Extensions;

public static class GrpcRegistrationExtensions
{
    public static IServiceCollection AddGrpcClients(
        this IServiceCollection services, IConfiguration configuration)
    {
        // Register gRPC clients per backing service:
        // services.AddGrpcClient<QueryService.QueryServiceClient>((sp, options) =>
        // {
        //     var urls = sp.GetRequiredService<IOptions<ServicesUrlsOptions>>().Value;
        //     options.Address = new Uri(urls.QueryServiceUrl);
        // });

        return services;
    }
}
