using {{ Company }}.{{ Domain }}.Queries.Infra.Database;

namespace {{ Company }}.{{ Domain }}.Queries.Infra.Repositories;

public class UnitOfWork(ApplicationDbContext context) : IUnitOfWork
{
    // Lazy-loaded repository properties
    // private SampleRepository? _samples;
    // public SampleRepository Samples => _samples ??= new(context);

    public async Task<int> SaveChangesAsync(CancellationToken ct = default)
        => await context.SaveChangesAsync(ct);
}

public interface IUnitOfWork
{
    Task<int> SaveChangesAsync(CancellationToken ct = default);
}
