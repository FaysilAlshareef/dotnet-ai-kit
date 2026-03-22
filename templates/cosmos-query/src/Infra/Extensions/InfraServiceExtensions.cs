using Azure.Identity;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using {{ Company }}.{{ Domain }}.Queries.Infra.Cosmos;
using {{ Company }}.{{ Domain }}.Queries.Infra.Options;

namespace {{ Company }}.{{ Domain }}.Queries.Infra.Extensions;

public static class InfraServiceExtensions
{
    public static IServiceCollection AddInfraServices(
        this IServiceCollection services, IConfiguration configuration)
    {
        services.AddOptions<CosmosDbOptions>()
            .Bind(configuration.GetSection("CosmosDb"))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        services.AddOptions<ServiceBusOptions>()
            .Bind(configuration.GetSection("ServiceBus"))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        services.AddSingleton(sp =>
        {
            var options = sp.GetRequiredService<Microsoft.Extensions.Options.IOptions<CosmosDbOptions>>().Value;
            var clientOptions = new CosmosClientOptions
            {
                ConnectionMode = ConnectionMode.Direct,
                SerializerOptions = new CosmosSerializationOptions
                {
                    PropertyNamingPolicy = CosmosPropertyNamingPolicy.CamelCase
                }
            };

            return options.UseServicePrincipal
                ? new CosmosClient(options.AccountEndpoint, new DefaultAzureCredential(), clientOptions)
                : new CosmosClient(options.AccountEndpoint, options.AuthKey, clientOptions);
        });

        services.AddSingleton(sp =>
        {
            var cosmosClient = sp.GetRequiredService<CosmosClient>();
            var options = sp.GetRequiredService<Microsoft.Extensions.Options.IOptions<CosmosDbOptions>>().Value;
            return cosmosClient.GetContainer(options.DatabaseName, options.DatabaseName);
        });

        services.AddHostedService<DatabaseRunner>();
        services.AddScoped<CosmosUnitOfWork>();
        services.AddScoped<CosmosRepository>();

        // Register listeners as IHostedService
        // services.AddHostedService<SampleListener>();

        return services;
    }
}
