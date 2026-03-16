---
name: content-negotiation
description: >
  Content type negotiation, custom formatters, Accept headers,
  and response format configuration.
  Trigger: content negotiation, Accept header, formatter, content type, media type.
category: api
agent: api-designer
---

# Content Negotiation

## Core Principles

- Respect the `Accept` header to determine response format
- Default to `application/json` when no preference is specified
- Support `application/problem+json` for error responses (RFC 9457)
- Use output formatters for custom content types (CSV, XML, PDF)
- Configure JSON serialization options globally

## Patterns

### JSON Serialization Configuration

```csharp
// Program.cs — global JSON options
builder.Services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.Converters.Add(
        new JsonStringEnumConverter());
    options.SerializerOptions.DefaultIgnoreCondition =
        JsonIgnoreCondition.WhenWritingNull;
    options.SerializerOptions.PropertyNamingPolicy =
        JsonNamingPolicy.CamelCase;
});

// Controller-specific
builder.Services.AddControllers()
    .AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.Converters.Add(
            new JsonStringEnumConverter());
        options.JsonSerializerOptions.DefaultIgnoreCondition =
            JsonIgnoreCondition.WhenWritingNull;
    });
```

### Adding XML Support

```csharp
builder.Services.AddControllers()
    .AddXmlDataContractSerializerFormatters();

// Endpoints now respond to:
// Accept: application/json → JSON
// Accept: application/xml  → XML
```

### Custom Output Formatter (CSV)

```csharp
public sealed class CsvOutputFormatter : TextOutputFormatter
{
    public CsvOutputFormatter()
    {
        SupportedMediaTypes.Add(
            MediaTypeHeaderValue.Parse("text/csv"));
        SupportedEncodings.Add(Encoding.UTF8);
    }

    protected override bool CanWriteType(Type? type)
    {
        return type is not null &&
            (typeof(IEnumerable).IsAssignableFrom(type) ||
             type.IsGenericType);
    }

    public override async Task WriteResponseBodyAsync(
        OutputFormatterWriteContext context,
        Encoding selectedEncoding)
    {
        var response = context.HttpContext.Response;
        var items = (IEnumerable<object>)context.Object!;

        var sb = new StringBuilder();
        var properties = context.ObjectType!
            .GetGenericArguments()[0]
            .GetProperties();

        // Header row
        sb.AppendLine(string.Join(",",
            properties.Select(p => p.Name)));

        // Data rows
        foreach (var item in items)
        {
            var values = properties.Select(p =>
                EscapeCsvValue(p.GetValue(item)?.ToString() ?? ""));
            sb.AppendLine(string.Join(",", values));
        }

        await response.WriteAsync(sb.ToString(), selectedEncoding);
    }

    private static string EscapeCsvValue(string value)
    {
        if (value.Contains(',') || value.Contains('"') ||
            value.Contains('\n'))
            return $"\"{value.Replace("\"", "\"\"")}\"";
        return value;
    }
}

// Registration
builder.Services.AddControllers(options =>
{
    options.OutputFormatters.Add(new CsvOutputFormatter());
});
```

### Format Filter for URL-Based Selection

```csharp
// Allow ?format=csv or /orders.csv
builder.Services.AddControllers(options =>
{
    options.FormatterMappings.SetMediaTypeMappingForFormat(
        "csv", "text/csv");
    options.FormatterMappings.SetMediaTypeMappingForFormat(
        "xml", "application/xml");
});

[HttpGet]
[FormatFilter]
[Route("/orders.{format?}")]
public async Task<ActionResult<List<OrderResponse>>> GetOrders() { }
```

### Minimal API Content Types

```csharp
// Minimal API — explicit content type
app.MapGet("/orders/{id}", async (Guid id, ISender sender) =>
{
    var order = await sender.Send(new GetOrderQuery(id));
    return order is not null
        ? Results.Ok(order)
        : Results.NotFound();
}).Produces<OrderResponse>(StatusCodes.Status200OK, "application/json");

// Return specific content type
app.MapGet("/orders/export", async (ISender sender) =>
{
    var csv = await sender.Send(new ExportOrdersCsvQuery());
    return Results.Text(csv, "text/csv", Encoding.UTF8);
});

// Return file
app.MapGet("/orders/{id}/invoice", async (Guid id, ISender sender) =>
{
    var pdf = await sender.Send(new GenerateInvoiceQuery(id));
    return Results.File(
        pdf, "application/pdf", $"invoice-{id}.pdf");
});
```

### ProblemDetails for Errors

```csharp
builder.Services.AddProblemDetails();

// Automatic problem+json responses for errors
app.UseExceptionHandler();
app.UseStatusCodePages();

// Custom problem details
app.MapGet("/orders/{id}", async (Guid id) =>
{
    return Results.Problem(
        title: "Order Not Found",
        detail: $"No order exists with ID {id}",
        statusCode: StatusCodes.Status404NotFound,
        type: "https://tools.ietf.org/html/rfc9110#section-15.5.5");
});
```

### Accept Header Handling

```
Client sends:
  Accept: application/json           → JSON response
  Accept: application/xml            → XML response
  Accept: text/csv                   → CSV response
  Accept: */*                        → Default (JSON)
  Accept: application/problem+json   → Error responses

Server responds with:
  Content-Type: application/json; charset=utf-8
```

## Anti-Patterns

- Ignoring the Accept header (always returning JSON)
- Not supporting `application/problem+json` for errors
- Hardcoding content types in response instead of using formatters
- Missing Content-Type header on responses
- Using custom error formats instead of ProblemDetails

## Detect Existing Patterns

1. Check for `AddJsonOptions` or `ConfigureHttpJsonOptions` configuration
2. Look for custom `OutputFormatter` implementations
3. Search for `AddXmlDataContractSerializerFormatters` calls
4. Check for `[Produces]` and `[Consumes]` attributes on controllers
5. Look for `AddProblemDetails` in `Program.cs`

## Adding to Existing Project

1. **Configure JSON options** globally with enum conversion and null handling
2. **Add ProblemDetails** middleware for consistent error responses
3. **Add custom formatters** for export formats (CSV, XML) if needed
4. **Add `[Produces]` attributes** to document supported content types
5. **Test with different Accept headers** to verify negotiation works

## Decision Guide

| Content Type | Use Case |
|-------------|----------|
| `application/json` | Default for API responses |
| `application/problem+json` | Error responses (RFC 9457) |
| `text/csv` | Data export |
| `application/xml` | Legacy integrations |
| `application/pdf` | Report generation |
| `application/octet-stream` | File downloads |

## References

- https://learn.microsoft.com/en-us/aspnet/core/web-api/advanced/formatting
- https://learn.microsoft.com/en-us/aspnet/core/web-api/advanced/custom-formatters
