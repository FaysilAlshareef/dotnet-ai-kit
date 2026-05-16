using MeasurementSvc.Application;
using MeasurementSvc.Infrastructure;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddApplication();
builder.Services.AddInfrastructure();

var app = builder.Build();

app.MapGet("/orders/{id}", (Guid id, IOrderQueries q) => q.GetAsync(id));

app.Run();
