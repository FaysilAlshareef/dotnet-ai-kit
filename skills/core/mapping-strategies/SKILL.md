---
name: mapping-strategies
description: >
  Use when mapping between DTOs and domain objects — manual mapping, LINQ projections, or AutoMapper.
metadata:
  category: core
  agent: dotnet-architect
  when-to-use: "When implementing object mapping between DTOs and domain models"
---

# Mapping Strategies

## Core Principles

1. **Explicit is better than implicit.** Every property assignment should be visible in code. When a mapping breaks, you should find the problem with Ctrl+F, not by debugging a reflection pipeline.
2. **Compile-time safety over convention-based magic.** If a property is renamed or removed, the build must fail immediately — not a test, not a runtime exception, the build itself.
3. **Manual mapping is the default.** Treat mapper libraries the way you treat ORMs: useful in narrow cases, dangerous as a reflex. Most projects never need one.
4. **Mapping is not infrastructure.** It is domain-adjacent logic that deserves the same readability standards as any other business code.
5. **Debuggability matters.** You should be able to set a breakpoint on any property assignment and inspect the transformation.

---

## When to Use Manual Mapping

Use manual mapping in **all** of the following situations (which covers the vast majority of projects):

- You have fewer than ~100 DTO types (most projects).
- Your mappings contain any conditional logic, formatting, or aggregation.
- You value compile-time errors over runtime surprises.
- You want new developers to understand mappings without learning a framework.
- You need to debug a wrong value in a response and want to find it in seconds.
- You care about startup performance (no reflection scanning).
- You want refactoring tools (rename, find usages) to work reliably across mappings.

**Bottom line:** if you are unsure, use manual mapping. You can always extract a pattern later. You cannot easily undo the implicit coupling a mapper library introduces.

---

## When to Consider a Mapper Library

Consider a mapper library **only** when ALL of these are true simultaneously:

- You have **100+ nearly identical DTOs** that are pure 1:1 property copies with zero logic.
- The team has already written manual mappings and measured the actual maintenance cost.
- You are doing rapid prototyping where long-term maintainability is explicitly deprioritized.
- You accept the trade-off: faster initial write speed in exchange for harder debugging and runtime failure modes.

Even then, prefer **Mapster with code generation** over AutoMapper, because Mapster's codegen produces compile-time mappings rather than runtime reflection.

---

## Patterns

### Extension Methods (Recommended)

The primary pattern for manual mapping. Place extension methods in a `Mapping` folder or alongside the DTO.

```csharp
public static class OrderMappingExtensions
{
    public static OrderDto ToDto(this Order order) => new(
        Id: order.Id,
        CustomerName: order.Customer.FullName,
        TotalAmount: order.Lines.Sum(l => l.Quantity * l.UnitPrice),
        Status: order.Status.ToString(),
        CreatedAt: order.CreatedAtUtc.ToString("O")
    );

    public static OrderSummaryDto ToSummaryDto(this Order order) => new(
        Id: order.Id,
        CustomerName: order.Customer.FullName,
        TotalAmount: order.Lines.Sum(l => l.Quantity * l.UnitPrice)
    );

    public static Order ToEntity(this CreateOrderRequest request, Customer customer) => new()
    {
        Customer = customer,
        Lines = request.Lines.Select(l => l.ToEntity()).ToList(),
        CreatedAtUtc = DateTime.UtcNow
    };
}
```

**Why this is the default:**

- Every assignment is visible — no hidden conventions.
- Rename a property and the compiler tells you immediately.
- Breakpoints work on any line.
- No framework dependency, no startup cost, no profile registration.
- The `this` keyword makes call sites clean: `order.ToDto()`.

---

### LINQ Projections (Recommended)

Use LINQ projections when querying from EF Core to push the mapping into SQL and avoid loading full entities.

```csharp
public async Task<List<OrderDto>> GetOrdersAsync(CancellationToken ct)
{
    return await dbContext.Orders
        .Where(o => o.Status == OrderStatus.Active)
        .Select(o => new OrderDto(
            o.Id,
            o.Customer.FullName,
            o.Lines.Sum(l => l.Quantity * l.UnitPrice),
            o.Status.ToString(),
            o.CreatedAtUtc.ToString("O")
        ))
        .ToListAsync(ct);
}
```

**Why this matters:**

- EF Core translates the projection to SQL — only selected columns are fetched.
- No N+1 queries, no over-fetching, no lazy-loading traps.
- The mapping and the query are in one place — easy to read and optimize.
- Compile-time safety: if `Order.Customer` is removed, this breaks at build time.

---

### Static Factory Methods

An alternative when you prefer the DTO to own its own construction logic.

```csharp
public record OrderDto(
    Guid Id,
    string CustomerName,
    decimal TotalAmount,
    string Status,
    string CreatedAt)
{
    public static OrderDto FromEntity(Order order) => new(
        Id: order.Id,
        CustomerName: order.Customer.FullName,
        TotalAmount: order.Lines.Sum(l => l.Quantity * l.UnitPrice),
        Status: order.Status.ToString(),
        CreatedAt: order.CreatedAtUtc.ToString("O")
    );
}
```

**When to use this over extension methods:**

- When the DTO is a record and you want construction logic co-located with the type.
- When you want `OrderDto.FromEntity(order)` to read as a named constructor.
- Avoid this if the DTO would need a reference to domain layer types it should not know about.

---

### AutoMapper (Comparison Only)

> **This section exists for context when working with legacy codebases. Do not introduce AutoMapper into new projects.**

AutoMapper uses runtime reflection and convention-based name matching.

```csharp
// Profile registration
public class OrderProfile : Profile
{
    public OrderProfile()
    {
        CreateMap<Order, OrderDto>()
            .ForMember(d => d.CustomerName, opt => opt.MapFrom(s => s.Customer.FullName))
            .ForMember(d => d.TotalAmount, opt => opt.MapFrom(s =>
                s.Lines.Sum(l => l.Quantity * l.UnitPrice)));
    }
}

// Usage
var dto = mapper.Map<OrderDto>(order);
```

**Known risks:**

| Risk | Impact |
|------|--------|
| Missing `ForMember` config | Runtime exception, not compile-time error |
| Property renamed in entity | Silently maps `default` — null or zero — no build error |
| Convention-based matching | Properties with similar names map incorrectly without warning |
| Startup cost | Reflection scanning all profiles on first resolve |
| Debugging | Cannot step into `mapper.Map<T>()` to see which property failed |
| Hidden complexity | `.ForMember().ConvertUsing().AfterMap()` chains become unreadable |
| Test requirement | You must call `AssertConfigurationIsValid()` in tests — if you forget, you ship broken mappings |

**If you inherit an AutoMapper codebase:** incrementally replace profiles with extension methods. Each replaced mapping is one fewer runtime failure mode.

---

### Mapster (Comparison Only)

> **Shown for comparison only. Prefer manual mapping. If you must use a library, Mapster with code generation is the least harmful option.**

Mapster offers a code-generation mode that produces compile-time mapping methods.

```csharp
// Configuration (typically in a startup/config class)
TypeAdapterConfig<Order, OrderDto>.NewConfig()
    .Map(d => d.CustomerName, s => s.Customer.FullName)
    .Map(d => d.TotalAmount, s => s.Lines.Sum(l => l.Quantity * l.UnitPrice));

// Usage (runtime mode — same risks as AutoMapper)
var dto = order.Adapt<OrderDto>();

// Code-gen mode (preferred if you use Mapster at all)
// Generates explicit mapping methods at build time via source generator
// Run: dotnet build to regenerate mappings
var dto = order.AdaptToOrderDto();  // Generated extension method
```

**Mapster vs AutoMapper:**

| Aspect | Mapster (codegen) | AutoMapper |
|--------|-------------------|------------|
| Compile-time safety | Yes (codegen mode) | No |
| Startup cost | None (codegen mode) | Reflection scan |
| Debugging | Step into generated code | Opaque |
| Adoption risk | Still a dependency | Same |

**Mapster is better than AutoMapper but still worse than manual mapping** for most projects. The generated code is essentially what you would write by hand — so write it by hand and own it completely.

---

## Decision Guide

| Scenario | Approach | Why |
|----------|----------|-----|
| New project, any size | **Extension methods** | Compile-time safe, zero dependencies, debuggable |
| EF Core queries | **LINQ projections** | SQL-level efficiency, no over-fetching |
| Record DTOs owning construction | **Static factory methods** | Clean named constructors |
| < 50 DTOs | **Extension methods** | Trivial to write and maintain |
| 50-100 DTOs | **Extension methods** | Still manageable; use a shared base or generic helpers if repetitive |
| 100+ identical 1:1 DTOs, zero logic | **Mapster codegen** (reluctantly) | Genuine boilerplate reduction; still get compile-time safety |
| Legacy codebase with AutoMapper | **Incremental migration to extension methods** | Remove one profile at a time, gain safety with each removal |
| Rapid throwaway prototype | **AutoMapper or Mapster** (acceptable) | Speed matters, longevity does not |
| Mappings with conditional logic | **Extension methods** | Mapper DSLs become unreadable for conditionals |
| Mappings with aggregation/calculation | **Extension methods** | Business logic should be explicit, not buried in `.ForMember()` |
| Microservice with < 20 endpoints | **Extension methods** | A mapper library adds more complexity than it removes |

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Using AutoMapper for 5-10 DTOs | Adds a dependency, startup cost, and runtime failure modes for negligible savings | Write extension methods — it takes minutes |
| `Mapper.Map<T>()` scattered everywhere | Hides what is actually being mapped; impossible to trace without running the app | Replace with explicit `entity.ToDto()` calls |
| Missing map configuration discovered at runtime | `AutoMapperMappingException` in production because no test called `AssertConfigurationIsValid()` | Use manual mapping — the compiler is your validator |
| Convention-based mapping with mismatched names | `Source.Name` silently maps to `Dest.Name` even when they mean different things | Be explicit: write the assignment so intent is clear |
| Mapper profiles with 50+ `.ForMember()` calls | The profile is harder to read than the manual mapping it replaced | Extract to extension methods — you already wrote the logic, just not in the right place |
| Using `.AfterMap()` / `.BeforeMap()` for side effects | Mapping should be a pure transformation, not a place to trigger business logic | Move side effects to the calling service |
| Injecting `IMapper` into domain services | Couples your domain to a mapping framework | Domain services should not know about DTOs at all |
| Not testing AutoMapper config | Silent failures ship to production | If you must use AutoMapper, test with `AssertConfigurationIsValid()` in CI — or just use manual mapping |

---

## Summary

Manual mapping with extension methods is the right default for .NET projects. It gives you compile-time safety, straightforward debugging, zero dependencies, and code that any developer can read without learning a framework. Reserve mapper libraries for the rare case of 100+ purely mechanical 1:1 DTO copies — and even then, prefer Mapster's codegen over AutoMapper's runtime reflection. When in doubt, write the mapping by hand.
