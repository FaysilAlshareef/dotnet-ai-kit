using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using {{ Company }}.{{ ProjectName }}.Domain.Interfaces;
using {{ Company }}.{{ ProjectName }}.Infrastructure.Data;

namespace {{ Company }}.{{ ProjectName }}.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services, IConfiguration configuration)
    {
        services.AddDbContext<ApplicationDbContext>(options =>
            options.UseSqlServer(configuration.GetConnectionString("Default")));

        services.AddScoped<IDomainEventDispatcher, DomainEventInterceptor>();

        return services;
    }
}
