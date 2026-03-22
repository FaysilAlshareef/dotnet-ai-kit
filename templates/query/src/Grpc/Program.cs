using Serilog;
using {{ Company }}.{{ Domain }}.Queries.Application.Extensions;
using {{ Company }}.{{ Domain }}.Queries.Infra.Extensions;

var logger = new LoggerConfiguration()
    .WriteTo.Console()
    .WriteTo.Seq("http://localhost:5341")
    .Enrich.WithProperty("AppName", "{{ Company }}.{{ Domain }}.Queries")
    .CreateLogger();

Log.Logger = logger;

try
{
    var builder = WebApplication.CreateBuilder(args);
    builder.Host.UseSerilog();

    builder.Services.AddApplicationServices();
    builder.Services.AddInfraServices(builder.Configuration);

    builder.Services.AddGrpc(options =>
    {
        // options.Interceptors.Add<ThreadCultureInterceptor>();
        // options.Interceptors.Add<ApplicationExceptionInterceptor>();
    });

    var app = builder.Build();

    // Map gRPC services here
    // app.MapGrpcService<{{ Domain }}QueryService>();

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
