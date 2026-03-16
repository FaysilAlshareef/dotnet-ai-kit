using FluentValidation;
using Microsoft.EntityFrameworkCore;
using {{ Company }}.{{ ProjectName }}.Common.Extensions;
using {{ Company }}.{{ ProjectName }}.Data;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddOpenApi();
builder.Services.AddMediatR(cfg => cfg.RegisterServicesFromAssembly(typeof(Program).Assembly));
builder.Services.AddValidatorsFromAssembly(typeof(Program).Assembly);
builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("Default")));

var app = builder.Build();

app.MapOpenApi();
app.MapScalarApiReference();
app.MapFeatureEndpoints();

app.Run();
