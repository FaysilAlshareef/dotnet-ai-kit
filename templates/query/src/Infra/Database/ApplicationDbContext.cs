using Microsoft.EntityFrameworkCore;

namespace {{ Company }}.{{ Domain }}.Queries.Infra.Database;

public class ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
    : DbContext(options)
{
    // DbSet<Entity> per entity type

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(ApplicationDbContext).Assembly);
    }
}
