---
name: event-store
description: "Configure the append-only EF Core event store with TPH discriminator mapping, Newtonsoft.Json data conversion, and a unique (AggregateId, Sequence) index. Use when setting up EventConfiguration, GenericEventConfiguration, or the 1:1 Event-to-OutboxMessage relationship. Do NOT use for defining the event classes themselves (use event-design) or for publishing committed events (use outbox)."
metadata:
  category: "microservice/command"
  agent: "command-architect"
---
# Event Store -- EF Core Configuration

## Core Principles

- The event store is an **append-only** table of `Event` entities
- A single `Event` base table uses **TPH (table-per-hierarchy)** with a discriminator on `EventType`
- `EventConfiguration` sets up the discriminator mapping from `EventType` enum to concrete event classes
- `GenericEventConfiguration<TEntity, TData>` handles the Newtonsoft.Json conversion for the `Data` column
- A unique index on `(AggregateId, Sequence)` prevents duplicate events
- `OutboxMessage` has a **1:1 relationship** with Event via shared primary key (`HasForeignKey<OutboxMessage>(e => e.Id)`)
- The `Type` column is stored as a string with `HasConversion<string>()`

## Why Newtonsoft.Json (not System.Text.Json) — F-G

The event-store, outbox, and event-routing pipelines deliberately use
**Newtonsoft.Json (`JsonConvert`)** instead of `System.Text.Json`. The
constraints that drive this choice:

1. **Polymorphic deserialisation of `IEventData`** — Newtonsoft handles
   `$type`-discriminated polymorphism out of the box (`TypeNameHandling`
   + custom `SerializationBinder`). `System.Text.Json` only added similar
   support in .NET 7+ via `[JsonPolymorphic]` + `[JsonDerivedType]`, and
   it requires every concrete type to be statically known at compile time —
   incompatible with the event-store's open set of `IEventData`
   implementations contributed by downstream features.
2. **Inheritance + private setters** — Newtonsoft handles inheritance,
   private setters, and constructor-less DTOs without ceremony. STJ
   requires public parameterless ctors or explicit `[JsonConstructor]`.
3. **Wire compatibility with the rest of the platform** — feature-013
   onwards has standardised on Newtonsoft across event-store / outbox /
   event-routing. Switching one boundary breaks every historical row.
4. **Custom converters** — the `StringEnumConverter`, contract resolver
   for snake-case columns, and `NullValueHandling.Ignore` are all
   Newtonsoft-native. The STJ analogues are partial and noisy.

Cross-references: `skills/microservice/command/outbox/SKILL.md` (line 139
where the outbox publisher imports `Newtonsoft.Json`),
`skills/microservice/processor/event-routing/SKILL.md` (line ~200
anti-pattern row reaffirming Newtonsoft), and
`knowledge/outbox-pattern.md` (line ~251 worked example).

## Key Patterns

### GenericEventConfiguration

Handles JSON serialization of the typed `Data` property for each concrete event type. Uses **Newtonsoft.Json** (not System.Text.Json).

```csharp
using {Company}.{Domain}.Commands.Domain.Events;
using {Company}.{Domain}.Commands.Domain.Events.DataTypes;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Newtonsoft.Json;

namespace {Company}.{Domain}.Commands.Infra.Persistence.Configurations;

public class GenericEventConfiguration<TEntity, TData> : IEntityTypeConfiguration<TEntity>
        where TEntity : Event<TData>
        where TData : IEventData
{
    public void Configure(EntityTypeBuilder<TEntity> builder)
    {
        var jsonSerializerSettings = new JsonSerializerSettings
        {
            NullValueHandling = NullValueHandling.Ignore
        };

        jsonSerializerSettings.Converters.Add(new Newtonsoft.Json.Converters.StringEnumConverter());

        builder.Property(e => e.Data).HasConversion(
             v => JsonConvert.SerializeObject(v, jsonSerializerSettings),
             v => JsonConvert.DeserializeObject<TData>(v)!
        ).HasColumnName("Data");
    }
}
```

Key details:
- Generic over `TEntity` (the concrete event class) and `TData` (the event data type)
- Constraint: `TEntity : Event<TData>` and `TData : IEventData`
- Serialization uses `NullValueHandling.Ignore` and `StringEnumConverter`
- Deserialization does NOT use the custom settings (just default `DeserializeObject`)
- Column is named `"Data"` explicitly

### EventConfiguration (Discriminator Mapping)

Maps the `EventType` enum to concrete event classes using EF Core's discriminator pattern.

```csharp
using {Company}.{Domain}.Commands.Domain.Enums;
using {Company}.{Domain}.Commands.Domain.Events;
using {Company}.{Domain}.Commands.Domain.Events.Orders;
using {Company}.{Domain}.Commands.Domain.Events.Invoices;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace {Company}.{Domain}.Commands.Infra.Persistence.Configurations;

public class EventConfiguration : IEntityTypeConfiguration<Event>
{
    public void Configure(EntityTypeBuilder<Event> builder)
    {
        builder.HasIndex(e => new { e.AggregateId, e.Sequence }).IsUnique();

        builder.Property(e => e.Type)
               .HasMaxLength(128)
               .HasConversion<string>();

        builder.HasDiscriminator(e => e.Type)
            .HasValue<OrderCreated>(EventType.OrderCreated)
            .HasValue<OrderUpdated>(EventType.OrderUpdated)
            .HasValue<OrderItemsAdded>(EventType.OrderItemsAdded)
            .HasValue<OrderItemsRemoved>(EventType.OrderItemsRemoved)
            .HasValue<InvoiceGenerated>(EventType.InvoiceGenerated)
            .HasValue<InvoiceUpdated>(EventType.InvoiceUpdated);
    }
}
```

Key details:
- **Unique composite index** on `(AggregateId, Sequence)` prevents duplicate events
- `Type` is stored as a **string** via `HasConversion<string>()` with max length 128
- The discriminator is the `EventType` enum, mapping each enum value to a concrete event class
- Every new event type must be registered here

### OutboxMessageConfiguration

```csharp
using {Company}.{Domain}.Commands.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace {Company}.{Domain}.Commands.Infra.Persistence.Configurations;

public class OutboxMessageConfiguration : IEntityTypeConfiguration<OutboxMessage>
{
    public void Configure(EntityTypeBuilder<OutboxMessage> builder)
    {
        builder.HasOne(e => e.Event)
            .WithOne()
            .HasForeignKey<OutboxMessage>(e => e.Id)
            .IsRequired()
            .OnDelete(DeleteBehavior.Cascade);
    }
}
```

Key details:
- **1:1 relationship**: OutboxMessage.Id IS the foreign key to Event.Id (shared primary key)
- `HasOne(e => e.Event).WithOne()` -- OutboxMessage has an `Event` navigation property
- `HasForeignKey<OutboxMessage>(e => e.Id)` -- the OutboxMessage's own `Id` is the FK
- Cascade delete: when an OutboxMessage is deleted, the relationship is cleaned up

### ApplicationDbContext

```csharp
using {Company}.{Domain}.Commands.Domain.Entities;
using {Company}.{Domain}.Commands.Domain.Events;
using {Company}.{Domain}.Commands.Domain.Events.DataTypes;
using {Company}.{Domain}.Commands.Domain.Events.Orders;
using {Company}.{Domain}.Commands.Domain.Events.Invoices;
using {Company}.{Domain}.Commands.Infra.Persistence.Configurations;
using Microsoft.EntityFrameworkCore;

namespace {Company}.{Domain}.Commands.Infra.Persistence;

public class ApplicationDbContext(DbContextOptions<ApplicationDbContext> options) : DbContext(options)
{
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // Base configurations
        modelBuilder.ApplyConfiguration(new EventConfiguration());
        modelBuilder.ApplyConfiguration(new OutboxMessageConfiguration());

        // GenericEventConfiguration for each concrete event type
        modelBuilder.ApplyConfiguration(new GenericEventConfiguration<OrderCreated, OrderCreatedData>());
        modelBuilder.ApplyConfiguration(new GenericEventConfiguration<OrderUpdated, OrderUpdatedData>());
        modelBuilder.ApplyConfiguration(new GenericEventConfiguration<OrderItemsAdded, OrderItemsAddedData>());
        modelBuilder.ApplyConfiguration(new GenericEventConfiguration<OrderItemsRemoved, OrderItemsRemovedData>());
        modelBuilder.ApplyConfiguration(new GenericEventConfiguration<InvoiceGenerated, InvoiceGeneratedData>());
        modelBuilder.ApplyConfiguration(new GenericEventConfiguration<InvoiceUpdated, InvoiceUpdatedData>());

        base.OnModelCreating(modelBuilder);
    }

    public DbSet<Event> Events { get; set; }
    public DbSet<OutboxMessage> OutboxMessages { get; set; }
}
```

Key details:
- **Single `DbSet<Event>`** for all events (TPH pattern)
- Each concrete event type needs BOTH a discriminator entry in `EventConfiguration` AND a `GenericEventConfiguration` registration
- `base.OnModelCreating(modelBuilder)` is called at the end
- DbSets use `{ get; set; }` (not expression-bodied `=> Set<T>()`)

### Event Repository

```csharp
namespace {Company}.{Domain}.Commands.Infra.Persistence.Repositories;

public class EventRepository : AsyncRepository<Event>, IEventRepository
{
    private readonly ApplicationDbContext _appDbContext;

    public EventRepository(ApplicationDbContext appDbContext) : base(appDbContext)
    {
        _appDbContext = appDbContext;
    }

    public async Task<IEnumerable<Event>> GetAllByAggregateIdAsync(
        Guid aggregateId, CancellationToken cancellationToken)
        => await _appDbContext.Events
                              .AsNoTracking()
                              .Where(e => e.AggregateId == aggregateId)
                              .OrderBy(e => e.Sequence)
                              .ToListAsync(cancellationToken);
}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Updating existing events | Events are immutable -- append only |
| Missing discriminator mapping | Every concrete event needs `HasValue<>` in EventConfiguration |
| Missing GenericEventConfiguration | Every concrete event also needs its Data JSON conversion registered |
| Using System.Text.Json for Data column | Use Newtonsoft.Json (project convention) |
| Separate tables per event type | Use TPH with single Events table and discriminator |
| OutboxMessage with its own independent Id | OutboxMessage.Id IS the Event.Id (shared PK/FK) |

## Detect Existing Patterns

```bash
# Find ApplicationDbContext
grep -r "class ApplicationDbContext" --include="*.cs" src/

# Find GenericEventConfiguration registrations
grep -r "GenericEventConfiguration" --include="*.cs" src/

# Find discriminator setup
grep -r "HasDiscriminator" --include="*.cs" src/

# Find EventConfiguration
grep -r "class EventConfiguration" --include="*.cs" src/

# Find OutboxMessageConfiguration
grep -r "OutboxMessageConfiguration" --include="*.cs" src/
```

## Adding to Existing Project

1. **Add new EventType** value to the enum
2. **Create concrete event class** and event data record
3. **Add discriminator mapping** in `EventConfiguration` (`HasValue<NewEvent>(EventType.NewEvent)`)
4. **Add GenericEventConfiguration** registration in `ApplicationDbContext.OnModelCreating`
5. **Add EF Core migration** after registering new event configurations
6. **Verify the unique index** on `(AggregateId, Sequence)` exists
