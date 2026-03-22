using {{ Company }}.{{ ProjectName }}.Shared.Contracts;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddOpenApi();

// Auto-discover and register modules
builder.Services.AddModules(builder.Configuration);

var app = builder.Build();

app.MapOpenApi();
app.MapScalarApiReference();
app.MapModuleEndpoints();

app.Run();

public static class ModuleHostExtensions
{
    public static IServiceCollection AddModules(
        this IServiceCollection services, IConfiguration configuration)
    {
        var moduleTypes = AppDomain.CurrentDomain.GetAssemblies()
            .SelectMany(a => a.GetTypes())
            .Where(t => typeof(IModuleInitializer).IsAssignableFrom(t)
                        && t is { IsInterface: false, IsAbstract: false });

        foreach (var type in moduleTypes)
        {
            var module = (IModuleInitializer)Activator.CreateInstance(type)!;
            module.ConfigureServices(services, configuration);
        }

        return services;
    }

    public static WebApplication MapModuleEndpoints(this WebApplication app)
    {
        var moduleTypes = AppDomain.CurrentDomain.GetAssemblies()
            .SelectMany(a => a.GetTypes())
            .Where(t => typeof(IModuleInitializer).IsAssignableFrom(t)
                        && t is { IsInterface: false, IsAbstract: false });

        foreach (var type in moduleTypes)
        {
            var module = (IModuleInitializer)Activator.CreateInstance(type)!;
            module.MapEndpoints(app);
        }

        return app;
    }
}
