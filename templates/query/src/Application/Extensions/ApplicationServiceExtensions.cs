using Microsoft.Extensions.DependencyInjection;

namespace {{ Company }}.{{ Domain }}.Queries.Application.Extensions;

public static class ApplicationServiceExtensions
{
    public static IServiceCollection AddApplicationServices(this IServiceCollection services)
    {
        services.AddMediatR(cfg =>
            cfg.RegisterServicesFromAssembly(typeof(ApplicationServiceExtensions).Assembly));
        return services;
    }
}
