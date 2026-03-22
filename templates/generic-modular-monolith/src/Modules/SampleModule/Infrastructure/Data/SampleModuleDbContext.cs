using Microsoft.EntityFrameworkCore;

namespace {{ Company }}.{{ ProjectName }}.Modules.SampleModule.Infrastructure.Data;

public class SampleModuleDbContext(DbContextOptions<SampleModuleDbContext> options)
    : DbContext(options)
{
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.HasDefaultSchema("sample");
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(SampleModuleDbContext).Assembly);
    }
}
