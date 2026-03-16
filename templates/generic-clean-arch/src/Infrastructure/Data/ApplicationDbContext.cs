using Microsoft.EntityFrameworkCore;
using {{ Company }}.{{ ProjectName }}.Domain.Interfaces;

namespace {{ Company }}.{{ ProjectName }}.Infrastructure.Data;

public class ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
    : DbContext(options), IUnitOfWork
{
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(ApplicationDbContext).Assembly);
    }
}
