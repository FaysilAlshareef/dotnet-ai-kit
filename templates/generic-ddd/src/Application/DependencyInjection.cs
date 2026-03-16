using MediatR;
using Microsoft.Extensions.DependencyInjection;
using {{ Company }}.{{ ProjectName }}.Application.Behaviors;

namespace {{ Company }}.{{ ProjectName }}.Application;

public static class DependencyInjection
{
    public static IServiceCollection AddApplication(this IServiceCollection services)
    {
        services.AddMediatR(cfg =>
            cfg.RegisterServicesFromAssembly(typeof(DependencyInjection).Assembly));
        services.AddTransient(typeof(IPipelineBehavior<,>), typeof(DomainEventDispatchBehavior<,>));
        return services;
    }
}
