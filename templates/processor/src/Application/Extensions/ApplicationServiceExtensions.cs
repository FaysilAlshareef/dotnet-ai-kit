using Microsoft.Extensions.DependencyInjection;

namespace {{ Company }}.{{ Domain }}.Processor.Application.Extensions;

public static class ApplicationServiceExtensions
{
    public static IServiceCollection AddApplicationServices(this IServiceCollection services)
    {
        services.AddMediatR(cfg =>
            cfg.RegisterServicesFromAssembly(typeof(ApplicationServiceExtensions).Assembly));
        return services;
    }
}
