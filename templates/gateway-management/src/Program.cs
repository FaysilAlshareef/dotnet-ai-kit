using Serilog;
using {{ Company }}.Gateways.{{ Domain }}.Management.Extensions;
using {{ Company }}.Gateways.{{ Domain }}.Management.Options;

var logger = new LoggerConfiguration()
    .WriteTo.Console()
    .WriteTo.Seq("http://localhost:5341")
    .Enrich.WithProperty("AppName", "{{ Company }}.Gateways.{{ Domain }}.Management")
    .CreateLogger();

Log.Logger = logger;

try
{
    var builder = WebApplication.CreateBuilder(args);
    builder.Host.UseSerilog();

    builder.Services.AddControllers();
    builder.Services.AddOpenApi();

    builder.Services.AddGrpcClients(builder.Configuration);
    builder.Services.AddAuthServices(builder.Configuration);

    builder.Services.AddOptions<ServicesUrlsOptions>()
        .Bind(builder.Configuration.GetSection("ServicesUrls"))
        .ValidateDataAnnotations()
        .ValidateOnStart();

    var app = builder.Build();

    app.UseAuthentication();
    app.UseAuthorization();

    app.MapOpenApi();
    app.MapScalarApiReference(options =>
    {
        options.Theme = ScalarTheme.BluePlanet;
    });

    app.MapControllers();

    app.Run();
}
catch (Exception ex)
{
    Log.Fatal(ex, "Application terminated unexpectedly");
}
finally
{
    Log.CloseAndFlush();
}
