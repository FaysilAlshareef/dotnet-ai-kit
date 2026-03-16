using {{ Company }}.{{ ProjectName }}.Application;
using {{ Company }}.{{ ProjectName }}.Infrastructure;
using {{ Company }}.{{ ProjectName }}.API.Middleware;

var builder = WebApplication.CreateBuilder(args);

builder.Services
    .AddApplication()
    .AddInfrastructure(builder.Configuration);

builder.Services.AddOpenApi();

var app = builder.Build();

app.UseMiddleware<ExceptionHandlerMiddleware>();
app.MapOpenApi();
app.MapScalarApiReference();
// app.MapEndpoints(); // Auto-discover IEndpointGroup

app.Run();
