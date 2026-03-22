using Asp.Versioning;
using Serilog;
using {{ Company }}.Gateways.{{ Domain }}.Consumers.Extensions;
using {{ Company }}.Gateways.{{ Domain }}.Consumers.Options;

var logger = new LoggerConfiguration()
    .WriteTo.Console()
    .WriteTo.Seq("http://localhost:5341")
    .Enrich.WithProperty("AppName", "{{ Company }}.Gateways.{{ Domain }}.Consumers")
    .CreateLogger();

Log.Logger = logger;

try
{
    var builder = WebApplication.CreateBuilder(args);
    builder.Host.UseSerilog();

    builder.Services.AddControllers();
    builder.Services.AddOpenApi();

    builder.Services.AddApiVersioning(options =>
    {
        options.DefaultApiVersion = new ApiVersion(1, 0);
        options.AssumeDefaultVersionWhenUnspecified = true;
        options.ReportApiVersions = true;
    }).AddApiExplorer(options =>
    {
        options.GroupNameFormat = "'v'VVV";
        options.SubstituteApiVersionInUrl = true;
    });

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
