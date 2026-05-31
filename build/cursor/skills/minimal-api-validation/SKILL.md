---
name: minimal-api-validation
description: "Enables source-generated request validation for Minimal APIs on .NET 10 using AddValidation() and [ValidatableType], producing automatic 400 ValidationProblem responses from DataAnnotations. Use when validating bound request DTOs on Minimal API endpoints without writing manual checks. Do NOT use for general endpoint-wrapping concerns like logging or auth (use endpoint-filters) or for endpoint structure (use minimal-api-patterns)."
---
# Minimal API Validation (Source-Generated)

.NET 10 adds built-in, source-generated validation for Minimal APIs. Call `AddValidation()` once, annotate request types with DataAnnotations + `[ValidatableType]`, and the framework validates bound parameters and returns RFC 9457 `ValidationProblem` (400) automatically — no per-endpoint filter.

## Conventions
- Register once in DI: `builder.Services.AddValidation();` — it hooks the endpoint filter pipeline for all Minimal API endpoints.
- Mark validatable request records with `[ValidatableType]` so the source generator emits the validator at build time (AOT/trim-safe, no reflection at runtime).
- Use standard `System.ComponentModel.DataAnnotations` attributes (`[Required]`, `[Range]`, `[EmailAddress]`, `[StringLength]`); nested complex properties marked `[ValidatableType]` validate recursively.
- Invalid requests are rejected before the handler runs and return a `ValidationProblemDetails` body — handlers can assume valid input.
- This covers DataAnnotations-style rules; for cross-field or DB-backed rules, layer a FluentValidation check inside the use-case (keep it license-light/OSS) rather than overloading attributes.
- Pair with `TypedResults` so the success/`ValidationProblem` contract is explicit in the signature.

## Example
```csharp
// Program.cs
builder.Services.AddValidation();

[ValidatableType]
public sealed record CreateOrderRequest
{
    [Required, StringLength(120)]
    public string CustomerName { get; init; } = "";

    [Range(1, 1000)]
    public int Quantity { get; init; }

    [Required, ValidatableType]          // nested type validated recursively
    public AddressDto ShipTo { get; init; } = new();
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
