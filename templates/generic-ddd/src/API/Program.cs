using {{ Company }}.{{ ProjectName }}.Application;
using {{ Company }}.{{ ProjectName }}.Infrastructure;

var builder = WebApplication.CreateBuilder(args);

builder.Services
    .AddApplication()
    .AddInfrastructure(builder.Configuration);

builder.Services.AddOpenApi();

var app = builder.Build();

app.MapOpenApi();
app.MapScalarApiReference();
// Map endpoints here

app.Run();
