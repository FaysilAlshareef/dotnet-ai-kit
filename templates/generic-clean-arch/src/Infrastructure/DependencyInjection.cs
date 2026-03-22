using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using {{ Company }}.{{ ProjectName }}.Domain.Interfaces;
using {{ Company }}.{{ ProjectName }}.Infrastructure.Data;
using {{ Company }}.{{ ProjectName }}.Infrastructure.Data.Repositories;

namespace {{ Company }}.{{ ProjectName }}.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services, IConfiguration configuration)
    {
        services.AddDbContext<ApplicationDbContext>(options =>
            options.UseSqlServer(configuration.GetConnectionString("Default")));

        services.AddScoped(typeof(IRepository<>), typeof(GenericRepository<>));
        services.AddScoped<IUnitOfWork, ApplicationDbContext>();

        return services;
    }
}
