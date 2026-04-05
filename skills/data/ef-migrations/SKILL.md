---
name: ef-migrations
description: >
  EF Core migration strategy, CI/CD migration application, data seeding,
  idempotent scripts, and migration best practices.
  Trigger: migration, database migration, seed data, schema change, EF migration.
metadata:
  category: data
  agent: ef-specialist
  when-to-use: "When creating EF Core migrations, data seeding, or schema change scripts"
---

# EF Core Migrations

## Core Principles

- Migrations are source-controlled alongside application code
- Apply migrations automatically in development, via scripts in production
- Use idempotent scripts for CI/CD pipelines
- Seed reference data through migrations, not application startup
- Never edit published migrations — create new ones for corrections

## Patterns

### Creating Migrations

```bash
# Add a new migration
dotnet ef migrations add CreateOrdersTable \
  --project src/{Company}.{Domain}.Infrastructure \
  --startup-project src/{Company}.{Domain}.WebApi

# Generate idempotent SQL script for production
dotnet ef migrations script --idempotent \
  --project src/{Company}.{Domain}.Infrastructure \
  --startup-project src/{Company}.{Domain}.WebApi \
  --output migrations.sql

# Remove last unapplied migration
dotnet ef migrations remove \
  --project src/{Company}.{Domain}.Infrastructure
```

### Migration with Data Seeding

```csharp
public partial class SeedOrderStatuses : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.InsertData(
            table: "OrderStatuses",
            columns: ["Id", "Name", "Description"],
            values: new object[,]
            {
                { 1, "Draft", "Order is being prepared" },
                { 2, "Submitted", "Order has been submitted" },
                { 3, "Processing", "Order is being processed" },
                { 4, "Shipped", "Order has been shipped" },
                { 5, "Delivered", "Order has been delivered" },
                { 6, "Cancelled", "Order was cancelled" }
            });
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DeleteData(
            table: "OrderStatuses",
            keyColumn: "Id",
            keyValues: [1, 2, 3, 4, 5, 6]);
    }
}
```

### Automatic Migration in Development

```csharp
// Program.cs — development only
if (app.Environment.IsDevelopment())
{
    using var scope = app.Services.CreateScope();
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    await db.Database.MigrateAsync();
}
```

### CI/CD Migration Application

```yaml
# GitHub Actions — apply migrations before deployment
- name: Apply Migrations
  run: |
    dotnet ef database update \
      --project src/{Company}.{Domain}.Infrastructure \
      --startup-project src/{Company}.{Domain}.WebApi \
      --connection "${{ secrets.DB_CONNECTION_STRING }}"

# Alternative: use idempotent SQL script
- name: Generate Migration Script
  run: |
    dotnet ef migrations script --idempotent \
      --project src/{Company}.{Domain}.Infrastructure \
      --startup-project src/{Company}.{Domain}.WebApi \
      --output ${{ runner.temp }}/migrate.sql

- name: Apply Migration Script
  uses: azure/sql-action@v2
  with:
    connection-string: ${{ secrets.DB_CONNECTION_STRING }}
    path: ${{ runner.temp }}/migrate.sql
```

### Bundle Migration (Self-Contained)

```bash
# Create a migration bundle executable
dotnet ef migrations bundle \
  --project src/{Company}.{Domain}.Infrastructure \
  --startup-project src/{Company}.{Domain}.WebApi \
  --output efbundle

# Run the bundle (in CI/CD or on the server)
./efbundle --connection "Server=prod;Database=AppDb;..."
```

### Design-Time Factory

```csharp
internal sealed class AppDbContextFactory
    : IDesignTimeDbContextFactory<AppDbContext>
{
    public AppDbContext CreateDbContext(string[] args)
    {
        var config = new ConfigurationBuilder()
            .AddJsonFile("appsettings.json")
            .AddJsonFile("appsettings.Development.json", optional: true)
            .AddUserSecrets<AppDbContextFactory>(optional: true)
            .Build();

        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseSqlServer(config.GetConnectionString("Default"))
            .Options;

        return new AppDbContext(options);
    }
}
```

### Migration History Table per Module

```csharp
// Modular monolith — separate migration history per module
options.UseSqlServer(connectionString, sql =>
{
    sql.MigrationsHistoryTable("__EFMigrationsHistory", "orders");
});
```

## Anti-Patterns

- Applying migrations at application startup in production
- Editing published migrations that have already been applied
- Manual schema changes outside of EF migrations
- Missing `Down` method implementations
- Not generating idempotent scripts for production deployments

## Detect Existing Patterns

1. Check for `Migrations/` folder in the project
2. Look for `IDesignTimeDbContextFactory<>` implementations
3. Search for `Database.MigrateAsync()` calls in `Program.cs`
4. Check CI/CD pipelines for `dotnet ef` commands
5. Look for `MigrationsHistoryTable` configuration

## Adding to Existing Project

1. **Install EF Core Tools** — `dotnet tool install dotnet-ef --global`
2. **Create initial migration** from existing DbContext configuration
3. **Add design-time factory** for CLI migration support
4. **Set up CI/CD pipeline** with idempotent script generation
5. **Add seed data** for reference/lookup tables
6. **Configure migration history table** per module if using modular monolith

## Decision Guide

| Environment | Migration Strategy |
|-------------|-------------------|
| Development | `Database.MigrateAsync()` at startup |
| CI/Testing | `dotnet ef database update` in pipeline |
| Staging | Idempotent SQL script or bundle |
| Production | Idempotent SQL script reviewed and applied |

## References

- https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/
- https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/applying
