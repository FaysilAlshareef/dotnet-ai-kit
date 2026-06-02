---
name: minimal-api-validation
description: "Enables source-generated request validation for Minimal APIs on .NET 10 using AddValidation() and [ValidatableType], producing automatic 400 ValidationProblem responses from DataAnnotations. Use when validating bound request DTOs on Minimal API endpoints without writing manual checks. Do NOT use for general endpoint-wrapping concerns like logging or auth (use endpoint-filters) or for endpoint structure (use minimal-api-patterns)."
metadata:
  category: "api"
  agent: "api-designer"
---
# Minimal API Validation (Source-Generated)

.NET 10 adds built-in, source-generated validation for Minimal APIs. Call `AddValidation()` once, annotate request types with DataAnnotations + `[ValidatableType]`, and the framework validates bound parameters and returns RFC 9457 `ValidationProblem` (400) automatically — no per-endpoint filter.

## Conventions
- Register once in DI: `builder.Services.AddValidation();` — it hooks the endpoint filter pipeline for all Minimal API endpoints.
- Mark validatable request records with `[ValidatableType]` so the source generator emits the validator at build time (AOT/trim-safe, no reflection at runtime). In current .NET 10 previews the attribute is experimental (`ASP0029`), so keep the warning visible instead of suppressing it silently.
- Use standard `System.ComponentModel.DataAnnotations` attributes (`[Required]`, `[Range]`, `[EmailAddress]`, `[StringLength]`); mark nested complex types with `[ValidatableType]` on the nested type declaration, not on the property.
- Invalid requests are rejected before the handler runs and return a `ValidationProblemDetails` body — handlers can assume valid input.
- This covers DataAnnotations-style rules; for cross-field or DB-backed rules, layer a FluentValidation check inside the use-case (keep it license-light/OSS) rather than overloading attributes.
- Pair with `TypedResults` so the success/`ValidationProblem` contract is explicit in the signature.

## Example
```csharp
// Program.cs
builder.Services.AddValidation();

[Experimental("ASP0029")]
[ValidatableType]
public sealed record CreateOrderRequest
{
    [Required, StringLength(120)]
    public string CustomerName { get; init; } = "";

    [Range(1, 1000)]
    public int Quantity { get; init; }

    [Required]
    public AddressDto ShipTo { get; init; } = new();
}

[Experimental("ASP0029")]
[ValidatableType]
public sealed record AddressDto
{
    [Required, StringLength(160)]
    public string Street { get; init; } = "";

    [Required, StringLength(80)]
    public string City { get; init; } = "";
}

// Handler runs only if the request is valid; otherwise auto-400 ValidationProblem
app.MapPost("/orders",
    (CreateOrderRequest request, IOrderService svc, CancellationToken ct)
        => svc.CreateAsync(request, ct));
```

## Anti-Patterns
- Writing manual `if (string.IsNullOrEmpty(...)) return BadRequest()` checks in the handler.
- Forgetting `[ValidatableType]`, so the generator skips the type and nothing validates.
- Encoding cross-entity/DB rules as attributes instead of validating them in the use-case.
- Returning ad-hoc error shapes instead of the standard `ValidationProblem`.

## References
- https://learn.microsoft.com/en-us/aspnet/core/fundamentals/minimal-apis/validation
