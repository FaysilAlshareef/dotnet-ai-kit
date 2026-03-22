using Microsoft.AspNetCore.Authentication.JwtBearer;

namespace {{ Company }}.Gateways.{{ Domain }}.Consumers.Extensions;

public static class AuthExtensions
{
    public static IServiceCollection AddAuthServices(
        this IServiceCollection services, IConfiguration configuration)
    {
        services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
            .AddJwtBearer(options =>
            {
                options.Authority = configuration["Auth:Authority"];
                options.Audience = configuration["Auth:Audience"];
            });

        services.AddAuthorization();

        return services;
    }
}
