using Microsoft.AspNetCore.Authentication.JwtBearer;

namespace {{ Company }}.Gateways.{{ Domain }}.Management.Extensions;

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

        services.AddAuthorization(options =>
        {
            // Policy-based authorization
            // options.AddPolicy("CircleOfficer", policy => policy.RequireClaim("role", "CircleOfficer"));
        });

        return services;
    }
}
