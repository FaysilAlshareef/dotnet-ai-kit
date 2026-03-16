namespace {{ Company }}.{{ ProjectName }}.Common.Extensions;

public static class ServiceCollectionExtensions
{
    /// <summary>
    /// Discovers and maps all feature endpoints implementing IEndpointGroup.
    /// </summary>
    public static WebApplication MapFeatureEndpoints(this WebApplication app)
    {
        var endpointGroupType = typeof(IEndpointGroup);
        var types = typeof(Program).Assembly.GetTypes()
            .Where(t => endpointGroupType.IsAssignableFrom(t) && t is { IsInterface: false, IsAbstract: false });

        foreach (var type in types)
        {
            var instance = (IEndpointGroup)Activator.CreateInstance(type)!;
            instance.MapEndpoints(app);
        }

        return app;
    }
}

public interface IEndpointGroup
{
    void MapEndpoints(IEndpointRouteBuilder endpoints);
}
