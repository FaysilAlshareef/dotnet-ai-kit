using {{ Company }}.{{ Domain }}.Commands.Application.Contracts.Repositories;
using {{ Company }}.{{ Domain }}.Commands.Application.Contracts.Services.BaseServices;
using {{ Company }}.{{ Domain }}.Commands.Application.Contracts.Services.ServiceBus;
using {{ Company }}.{{ Domain }}.Commands.Infra.Persistence;
using {{ Company }}.{{ Domain }}.Commands.Infra.Persistence.Repositories;
using {{ Company }}.{{ Domain }}.Commands.Infra.Services.BaseService;
using {{ Company }}.{{ Domain }}.Commands.Infra.Services.ServiceBus;
using Azure.Messaging.ServiceBus;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace {{ Company }}.{{ Domain }}.Commands.Infra;

public static class InfraContainer
{
    public static IServiceCollection AddInfraServices(
        this IServiceCollection services, IConfiguration configuration)
    {
        services.AddDbContext<ApplicationDbContext>(options =>
            options.UseSqlServer(configuration.GetConnectionString("DefaultConnection")));

        services.AddScoped<IUnitOfWork, UnitOfWork>();

        services.AddSingleton<IServiceBusPublisher, ServiceBusPublisher>();

        services.AddSingleton(s =>
        {
            return new ServiceBusClient(configuration.GetConnectionString("ServiceBus"));
        });

        services.AddScoped<ICommitEventService, CommitEventService>();

        return services;
    }
}
