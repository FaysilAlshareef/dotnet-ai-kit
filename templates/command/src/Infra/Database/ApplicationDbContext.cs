using {{ Company }}.{{ Domain }}.Commands.Domain.Entities;
using {{ Company }}.{{ Domain }}.Commands.Domain.Events;
using {{ Company }}.{{ Domain }}.Commands.Infra.Persistence.Configurations;
using Microsoft.EntityFrameworkCore;

namespace {{ Company }}.{{ Domain }}.Commands.Infra.Persistence;

public class ApplicationDbContext(DbContextOptions<ApplicationDbContext> options) : DbContext(options)
{
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfiguration(new EventConfiguration());
        modelBuilder.ApplyConfiguration(new OutboxMessageConfiguration());

        // Register GenericEventConfiguration for each concrete event type:
        // modelBuilder.ApplyConfiguration(new GenericEventConfiguration<OrderCreated, OrderCreatedData>());

        base.OnModelCreating(modelBuilder);
    }

    public DbSet<Event> Events { get; set; }
    public DbSet<OutboxMessage> OutboxMessages { get; set; }
}
