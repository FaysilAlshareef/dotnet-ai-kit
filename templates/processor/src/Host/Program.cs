using Serilog;
using {{ Company }}.{{ Domain }}.Processor.Application.Extensions;
using {{ Company }}.{{ Domain }}.Processor.Infra.Extensions;

var logger = new LoggerConfiguration()
    .WriteTo.Console()
    .WriteTo.Seq("http://localhost:5341")
    .Enrich.WithProperty("AppName", "{{ Company }}.{{ Domain }}.Processor")
    .CreateLogger();

Log.Logger = logger;

try
{
    var builder = WebApplication.CreateBuilder(args);
    builder.Host.UseSerilog();

    builder.Services.AddApplicationServices();
    builder.Services.AddInfraServices(builder.Configuration);

    var app = builder.Build();
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
