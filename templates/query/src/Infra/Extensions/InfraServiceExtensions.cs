using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using {{ Company }}.{{ Domain }}.Queries.Infra.Database;
using {{ Company }}.{{ Domain }}.Queries.Infra.Options;
using {{ Company }}.{{ Domain }}.Queries.Infra.Repositories;

namespace {{ Company }}.{{ Domain }}.Queries.Infra.Extensions;

public static class InfraServiceExtensions
{
    public static IServiceCollection AddInfraServices(
        this IServiceCollection services, IConfiguration configuration)
    {
        services.AddDbContext<ApplicationDbContext>(options =>
            options.UseSqlServer(configuration.GetConnectionString("DefaultConnection")));

        services.AddOptions<ServiceBusOptions>()
            .Bind(configuration.GetSection("ServiceBus"))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        services.AddScoped<IUnitOfWork, UnitOfWork>();

        // Register listeners as IHostedService
        // services.AddHostedService<SampleListener>();

        return services;
    }
}
