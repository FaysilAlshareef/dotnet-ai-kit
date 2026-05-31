using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.AspNetCore.Routing;
using Microsoft.EntityFrameworkCore;

namespace Sample.Features.Products;

// Compact vertical slice for the Product "create" operation:
// request -> handler -> persistence, wired to a Minimal API route. A real CRUD
// slice repeats this shape for read/update/delete.
public sealed record CreateProduct(string Name, decimal Price);

public sealed class Product
{
    public Guid Id { get; private set; } = Guid.NewGuid();
    public string Name { get; private set; } = null!;
    public decimal Price { get; private set; }

    public static Product Create(string name, decimal price) =>
        new() { Name = name, Price = price };
}

public sealed class CreateProductHandler(AppDbContext db)
{
    public async Task<Guid> HandleAsync(CreateProduct command, CancellationToken ct)
    {
        var product = Product.Create(command.Name, command.Price);
        db.Products.Add(product);
        await db.SaveChangesAsync(ct);
        return product.Id;
    }
}

public static class ProductEndpoints
{
    public static IEndpointRouteBuilder MapProducts(this IEndpointRouteBuilder app)
    {
        app.MapPost("/products", async (
            CreateProduct command,
            CreateProductHandler handler,
            CancellationToken ct) =>
        {
            var id = await handler.HandleAsync(command, ct);
            return TypedResults.Created($"/products/{id}", new { id });
        });

        return app;
    }
}

public sealed class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    public DbSet<Product> Products => Set<Product>();
}
