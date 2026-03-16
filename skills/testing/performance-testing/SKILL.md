---
name: performance-testing
description: >
  Performance testing with BenchmarkDotNet, load testing, and Test.Live projects
  for Service Bus throughput validation. Covers hot path optimization and baselines.
  Trigger: benchmark, performance test, load test, throughput, Test.Live.
category: testing
agent: test-engineer
---

# Performance Testing — Benchmarks & Load Tests

## Core Principles

- **BenchmarkDotNet** for micro-benchmarks of hot path code
- **Test.Live** projects for Service Bus throughput validation with real infrastructure
- Establish baselines before optimization
- Focus on hot paths: serialization, event handling, query execution
- Load testing validates system behavior under stress
- Performance tests run separately from CI (manual or scheduled)

## Key Patterns

### BenchmarkDotNet Setup

```csharp
namespace {Company}.{Domain}.Benchmarks;

[MemoryDiagnoser]
[SimpleJob(RuntimeMoniker.Net90)]
public class EventSerializationBenchmarks
{
    private Event<OrderCreatedData> _event = null!;
    private string _json = null!;

    [GlobalSetup]
    public void Setup()
    {
        _event = new Event<OrderCreatedData>
        {
            AggregateId = Guid.NewGuid(),
            Sequence = 1,
            Type = EventTypes.OrderCreated,
            DateTime = DateTime.UtcNow,
            Data = new OrderCreatedData("Test", 100m, [])
        };
        _json = JsonConvert.SerializeObject(_event);
    }

    [Benchmark(Baseline = true)]
    public string Serialize_Newtonsoft()
        => JsonConvert.SerializeObject(_event);

    [Benchmark]
    public Event<OrderCreatedData> Deserialize_Newtonsoft()
        => JsonConvert.DeserializeObject<Event<OrderCreatedData>>(_json)!;
}

// Run: dotnet run -c Release --project src/Benchmarks/
```

### Test.Live Project (Service Bus Throughput)

```csharp
namespace {Company}.{Domain}.Tests.Live;

/// <summary>
/// Sends batches of events to Service Bus and measures throughput.
/// Requires real Service Bus connection string in environment.
/// </summary>
public sealed class ServiceBusThroughputTest
{
    [Fact(Skip = "Manual execution only — requires live Service Bus")]
    public async Task MeasurePublishThroughput()
    {
        // Arrange
        var connectionString = Environment.GetEnvironmentVariable(
            "SERVICEBUS_CONNECTION_STRING")!;
        var client = new ServiceBusClient(connectionString);
        var sender = client.CreateSender("{company}-{domain}-commands");

        var events = Enumerable.Range(1, 1000).Select(i =>
            new ServiceBusMessage($"{{\"AggregateId\":\"{Guid.NewGuid()}\",\"Sequence\":{i}}}")
            {
                Subject = EventTypes.OrderCreated,
                SessionId = Guid.NewGuid().ToString()
            }).ToList();

        // Act
        var sw = Stopwatch.StartNew();

        foreach (var batch in events.Chunk(100))
        {
            using var messageBatch = await sender.CreateMessageBatchAsync();
            foreach (var msg in batch)
                messageBatch.TryAddMessage(msg);
            await sender.SendMessagesAsync(messageBatch);
        }

        sw.Stop();

        // Assert
        var throughput = events.Count / sw.Elapsed.TotalSeconds;
        Console.WriteLine($"Throughput: {throughput:F0} messages/sec");
        throughput.Should().BeGreaterThan(100, "Minimum throughput not met");
    }
}
```

### Query Performance Test

```csharp
[MemoryDiagnoser]
public class QueryBenchmarks
{
    private ApplicationDbContext _db = null!;

    [GlobalSetup]
    public async Task Setup()
    {
        var options = new DbContextOptionsBuilder<ApplicationDbContext>()
            .UseSqlServer("Server=.;Database=BenchmarkDb;Trusted_Connection=true;")
            .Options;
        _db = new ApplicationDbContext(options);

        // Seed 10,000 orders for realistic benchmarks
        await SeedData.SeedOrders(_db, 10000);
    }

    [Benchmark]
    public async Task<List<OrderOutput>> Query_WithPagination()
    {
        return await _db.Orders.AsNoTracking()
            .OrderByDescending(o => o.Sequence)
            .Skip(0).Take(20)
            .Select(o => new OrderOutput(o.Id, o.CustomerName, o.Total))
            .ToListAsync();
    }

    [Benchmark]
    public async Task<List<OrderOutput>> Query_WithFilter()
    {
        return await _db.Orders.AsNoTracking()
            .Where(o => o.CustomerName.Contains("Test"))
            .OrderByDescending(o => o.Sequence)
            .Skip(0).Take(20)
            .Select(o => new OrderOutput(o.Id, o.CustomerName, o.Total))
            .ToListAsync();
    }
}
```

### Project Structure

```
tests/
  {Domain}.Tests.Unit/          # Unit tests (CI)
  {Domain}.Tests.Integration/   # Integration tests (CI)
  {Domain}.Tests.Live/          # Live infrastructure tests (manual)
  {Domain}.Benchmarks/          # BenchmarkDotNet projects (manual)
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Optimizing without benchmarks | Measure first, optimize second |
| Benchmarks in CI pipeline | Run benchmarks manually or on schedule |
| Testing with Debug build | Always benchmark in Release mode |
| Live tests without Skip attribute | Mark with `Skip` to prevent accidental CI runs |

## Detect Existing Patterns

```bash
# Find BenchmarkDotNet usage
grep -r "BenchmarkDotNet\|\[Benchmark\]" --include="*.cs" tests/ benchmarks/

# Find Test.Live projects
find . -name "*Tests.Live*" -type d

# Find throughput tests
grep -r "Throughput\|Stopwatch" --include="*.cs" tests/
```

## Adding to Existing Project

1. **Check for existing benchmark projects** before creating new ones
2. **Add benchmarks in `Benchmarks/` project** with Release configuration
3. **Use `Test.Live` project** for real infrastructure validation
4. **Mark live tests** with `Skip` attribute or `[Trait("Category", "Live")]`
5. **Establish baselines** before making performance changes
