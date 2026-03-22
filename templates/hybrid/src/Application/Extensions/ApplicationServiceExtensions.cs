using Microsoft.Extensions.DependencyInjection;
using System.Reflection;

namespace {{ Company }}.{{ Domain }}.Commands.Application;

public static class ApplicationContainer
{
    public static IServiceCollection AddApplicationServices(this IServiceCollection services)
    {
        services.AddMediatR(m => m.RegisterServicesFromAssembly(Assembly.GetExecutingAssembly()));

        return services;
    }
}
