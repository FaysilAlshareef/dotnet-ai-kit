using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Options;
using {{ Company }}.{{ Domain }}.Queries.Infra.Options;

namespace {{ Company }}.{{ Domain }}.Queries.Infra.Cosmos;

/// <summary>
/// IHostedService that initializes database and container on startup.
/// Creates database and container in development only.
/// Configures 3-level hierarchical partition key.
/// </summary>
public class DatabaseRunner(
    CosmosClient cosmosClient,
    IOptions<CosmosDbOptions> options,
    IHostEnvironment environment) : IHostedService
{
    public async Task StartAsync(CancellationToken ct)
    {
        if (!environment.IsDevelopment()) return;

        var database = await cosmosClient.CreateDatabaseIfNotExistsAsync(
            options.Value.DatabaseName, cancellationToken: ct);

        var containerProperties = new ContainerProperties
        {
            Id = options.Value.DatabaseName,
            PartitionKeyPaths = new List<string>
            {
                "/partitionKey1",
                "/partitionKey2",
                "/partitionKey3"
            }
        };

        await database.Database.CreateContainerIfNotExistsAsync(
            containerProperties, cancellationToken: ct);
    }

    public Task StopAsync(CancellationToken ct) => Task.CompletedTask;
}
