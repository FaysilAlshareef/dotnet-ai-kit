using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using {{ Company }}.{{ Domain }}.Processor.Infra.Options;

namespace {{ Company }}.{{ Domain }}.Processor.Infra.Extensions;

public static class InfraServiceExtensions
{
    public static IServiceCollection AddInfraServices(
        this IServiceCollection services, IConfiguration configuration)
    {
        services.AddOptions<ServiceBusOptions>()
            .Bind(configuration.GetSection("ServiceBus"))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        services.AddOptions<ExternalServicesOptions>()
            .Bind(configuration.GetSection("ExternalServices"))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        // Register gRPC clients
        // services.AddGrpcClient<SomeService.SomeServiceClient>((sp, options) =>
        // {
        //     var urls = sp.GetRequiredService<IOptions<ExternalServicesOptions>>().Value;
        //     options.Address = new Uri(urls.SomeServiceUrl);
        // });

        // Register listeners as IHostedService
        // services.AddHostedService<SampleListener>();

        return services;
    }
}
