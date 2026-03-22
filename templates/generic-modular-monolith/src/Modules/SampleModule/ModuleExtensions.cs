using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.AspNetCore.Routing;
using {{ Company }}.{{ ProjectName }}.Shared.Contracts;
using {{ Company }}.{{ ProjectName }}.Modules.SampleModule.Infrastructure.Data;

namespace {{ Company }}.{{ ProjectName }}.Modules.SampleModule;

public sealed class SampleModuleInitializer : IModuleInitializer
{
    public void ConfigureServices(IServiceCollection services, IConfiguration configuration)
    {
        services.AddMediatR(cfg =>
            cfg.RegisterServicesFromAssembly(typeof(SampleModuleInitializer).Assembly));

        services.AddDbContext<SampleModuleDbContext>(options =>
            options.UseSqlServer(configuration.GetConnectionString("SampleModule")));
    }

    public void MapEndpoints(IEndpointRouteBuilder endpoints)
    {
        // Register module endpoints here
    }
}
