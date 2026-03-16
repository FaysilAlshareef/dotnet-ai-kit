using Microsoft.EntityFrameworkCore;
using {{ Company }}.{{ Domain }}.Queries.Infra.Database;

namespace {{ Company }}.{{ Domain }}.Queries.Infra.Repositories;

public class AsyncRepository<T>(ApplicationDbContext context)
    where T : class
{
    protected readonly ApplicationDbContext Context = context;
    protected readonly DbSet<T> DbSet = context.Set<T>();

    public virtual async Task<T?> FindAsync(Guid id)
        => await DbSet.FindAsync(id);

    public virtual async Task AddAsync(T entity)
        => await DbSet.AddAsync(entity);

    public virtual void Update(T entity)
        => DbSet.Update(entity);

    public virtual IQueryable<T> Query()
        => DbSet.AsQueryable();
}
