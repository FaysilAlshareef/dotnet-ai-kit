---
name: background-jobs
description: >
  Background job patterns with Hangfire, hosted services, and recurring tasks.
  Covers job scheduling, persistent store, and fire-and-forget patterns.
  Trigger: background job, Hangfire, recurring task, scheduled job, cron.
metadata:
  category: infra
  agent: dotnet-architect
---

# Background Jobs — Hangfire & Hosted Services

## Core Principles

- **Hangfire** for persistent, schedulable jobs with dashboard
- **BackgroundService** for continuous processing loops
- **IHostedService** for Service Bus listeners and startup tasks
- Recurring jobs use cron expressions
- Fire-and-forget jobs for async work after HTTP response
- Persistent job store (SQL Server) survives restarts

## Key Patterns

### Hangfire Setup

```csharp
// Program.cs
builder.Services.AddHangfire(config => config
    .SetDataCompatibilityLevel(CompatibilityLevel.Version_180)
    .UseSimpleAssemblyNameTypeSerializer()
    .UseRecommendedSerializerSettings()
    .UseSqlServerStorage(connectionString));

builder.Services.AddHangfireServer(options =>
{
    options.WorkerCount = Environment.ProcessorCount * 2;
});

var app = builder.Build();

app.UseHangfireDashboard("/hangfire", new DashboardOptions
{
    Authorization = [new HangfireAuthorizationFilter()]
});
```

### Recurring Job

```csharp
namespace {Company}.{Domain}.Infrastructure.Jobs;

public sealed class DailyReportJob(
    IReportService reportService,
    ILogger<DailyReportJob> logger)
{
    public async Task ExecuteAsync()
    {
        logger.LogInformation("Generating daily report");
        await reportService.GenerateDailyReportAsync();
    }
}

// Registration
RecurringJob.AddOrUpdate<DailyReportJob>(
    "daily-report",
    job => job.ExecuteAsync(),
    Cron.Daily(2, 0)); // 2:00 AM
```

### Fire-and-Forget

```csharp
// In a controller or handler — enqueue work after response
BackgroundJob.Enqueue<IEmailService>(
    service => service.SendOrderConfirmationAsync(orderId));
```

### Hosted Service for Startup Tasks

```csharp
namespace {Company}.{Domain}.Infrastructure;

public sealed class DatabaseMigrationService(
    IServiceScopeFactory scopeFactory,
    ILogger<DatabaseMigrationService> logger) : IHostedService
{
    public async Task StartAsync(CancellationToken ct)
    {
        using var scope = scopeFactory.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();

        logger.LogInformation("Applying database migrations");
        await db.Database.MigrateAsync(ct);
    }

    public Task StopAsync(CancellationToken ct) => Task.CompletedTask;
}
```

### BackgroundService for Polling

```csharp
namespace {Company}.{Domain}.Infrastructure;

public sealed class OutboxCleanupService(
    IServiceScopeFactory scopeFactory,
    ILogger<OutboxCleanupService> logger) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            try
            {
                using var scope = scopeFactory.CreateScope();
                var db = scope.ServiceProvider
                    .GetRequiredService<ApplicationDbContext>();

                var cutoff = DateTime.UtcNow.AddDays(-7);
                var deleted = await db.OutboxMessages
                    .Where(m => m.PublishedAt != null && m.PublishedAt < cutoff)
                    .ExecuteDeleteAsync(ct);

                if (deleted > 0)
                    logger.LogInformation("Cleaned up {Count} outbox messages", deleted);
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "Outbox cleanup failed");
            }

            await Task.Delay(TimeSpan.FromHours(1), ct);
        }
    }
}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| In-memory job scheduling | Use Hangfire with persistent store |
| Fire-and-forget without tracking | Use Hangfire for visibility and retry |
| Missing error handling in background | Wrap in try/catch, log errors |
| Blocking thread pool in hosted service | Use async/await throughout |

## Detect Existing Patterns

```bash
# Find Hangfire usage
grep -r "Hangfire\|RecurringJob\|BackgroundJob" --include="*.cs" src/

# Find BackgroundService implementations
grep -r ": BackgroundService" --include="*.cs" src/

# Find IHostedService
grep -r ": IHostedService" --include="*.cs" src/
```

## Adding to Existing Project

1. **Check if Hangfire is already configured** — reuse existing setup
2. **For microservices**, prefer BackgroundService over Hangfire
3. **For generic .NET**, Hangfire provides better job visibility
4. **Use IServiceScopeFactory** in all background services
5. **Register with `AddHostedService<T>`** for hosted services
