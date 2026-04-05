---
name: fluent-validation
description: >
  Standalone FluentValidation patterns — validators, DI registration, manual and auto validation,
  custom validators, async validators, and integration with ProblemDetails.
  Trigger: FluentValidation, validator, validation, AbstractValidator, RuleFor.
metadata:
  category: core
  agent: dotnet-architect
  when-to-use: "When writing input validation rules using FluentValidation"
---

# FluentValidation (Standalone)

## Core Principles

- Fail fast — validate at system boundaries before any business logic executes
- Explicit rules — every validation constraint is a readable, testable RuleFor call
- Reusable validators — share common rules via `Include()` and composition, not inheritance hierarchies
- One validator per request model — do not validate domain entities (they protect their own invariants)
- Separation of concerns — validators live in the Application layer, not in controllers or domain

## When to Use

- **DTOs / request models** — `CreateOrderRequest`, `UpdateCustomerCommand`
- **API boundary input** — anything arriving from HTTP, gRPC, or message consumers
- **Form input** — Blazor / MVC form models before submission
- **Configuration objects** — validating options at startup with `IValidateOptions<T>`
- **Cross-field rules** — "end date must be after start date" expressed declaratively

## When NOT to Use

- **Domain invariants** — enforce inside the entity/aggregate constructor and methods
- **Simple null checks on internals** — a `required` keyword or `ArgumentNullException.ThrowIfNull` suffices
- **Authorization** — validation is not a substitute for policy-based auth checks
- **Database constraints** — unique indexes and FK constraints belong in the persistence layer

## Patterns

### Basic Validator

```csharp
using FluentValidation;

namespace Ordering.Application.Validators;

public sealed class CreateOrderRequestValidator : AbstractValidator<CreateOrderRequest>
{
    public CreateOrderRequestValidator()
    {
        RuleFor(x => x.CustomerId)
            .NotEmpty()
            .WithMessage("Customer ID is required.");

        RuleFor(x => x.OrderDate)
            .LessThanOrEqualTo(DateOnly.FromDateTime(DateTime.UtcNow))
            .WithMessage("Order date cannot be in the future.");

        RuleFor(x => x.LineItems)
            .NotEmpty()
            .WithMessage("Order must contain at least one line item.");

        RuleForEach(x => x.LineItems)
            .SetValidator(new LineItemValidator());
    }
}

public sealed class LineItemValidator : AbstractValidator<LineItemDto>
{
    public LineItemValidator()
    {
        RuleFor(x => x.ProductId).NotEmpty();
        RuleFor(x => x.Quantity).GreaterThan(0);
        RuleFor(x => x.UnitPrice).GreaterThan(0m);
    }
}
```

### DI Registration

Register all validators from an assembly in one call:

```csharp
using FluentValidation;

// In Program.cs or a DI module
builder.Services.AddValidatorsFromAssemblyContaining<CreateOrderRequestValidator>();
```

This scans the assembly and registers every `IValidator<T>` as `Scoped` by default. Override with:

```csharp
builder.Services.AddValidatorsFromAssemblyContaining<CreateOrderRequestValidator>(
    lifetime: ServiceLifetime.Transient);
```

### Manual Validation

Inject `IValidator<T>` and call `ValidateAsync` explicitly:

```csharp
using FluentValidation;

namespace Ordering.Application.Handlers;

public sealed class CreateOrderHandler(
    IValidator<CreateOrderRequest> validator,
    IOrderRepository repository)
{
    public async Task<Guid> HandleAsync(
        CreateOrderRequest request,
        CancellationToken ct = default)
    {
        var result = await validator.ValidateAsync(request, ct);

        if (!result.IsValid)
        {
            throw new ValidationException(result.Errors);
        }

        var order = Order.Create(request.CustomerId, request.OrderDate, request.LineItems);
        await repository.AddAsync(order, ct);
        return order.Id;
    }
}
```

### Auto-Validation in Minimal API

Use an endpoint filter to validate before the handler runs:

```csharp
using FluentValidation;

namespace Ordering.Api.Filters;

public sealed class ValidationFilter<T> : IEndpointFilter where T : class
{
    public async ValueTask<object?> InvokeAsync(
        EndpointFilterInvocationContext context,
        EndpointFilterDelegate next)
    {
        var validator = context.HttpContext.RequestServices.GetService<IValidator<T>>();
        if (validator is null)
        {
            return await next(context);
        }

        var model = context.Arguments.OfType<T>().FirstOrDefault();
        if (model is null)
        {
            return await next(context);
        }

        var result = await validator.ValidateAsync(model);
        if (!result.IsValid)
        {
            return Results.ValidationProblem(
                result.ToDictionary(),
                title: "Validation Failed",
                type: "https://tools.ietf.org/html/rfc9110#section-15.5.1");
        }

        return await next(context);
    }
}
```

Register the filter on an endpoint or group:

```csharp
app.MapPost("/api/orders", CreateOrder)
    .AddEndpointFilter<ValidationFilter<CreateOrderRequest>>();

// Or apply to an entire route group
app.MapGroup("/api/orders")
    .AddEndpointFilter<ValidationFilter<CreateOrderRequest>>();
```

### Auto-Validation in Controllers

Use an action filter that resolves `IValidator<>` for each action argument:

```csharp
using FluentValidation;
using FluentValidation.AspNetCore;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Filters;

namespace Ordering.Api.Filters;

public sealed class FluentValidationActionFilter(IServiceProvider serviceProvider)
    : IAsyncActionFilter
{
    public async Task OnActionExecutionAsync(
        ActionExecutingContext context, ActionExecutionDelegate next)
    {
        foreach (var (_, value) in context.ActionArguments)
        {
            if (value is null) continue;
            var validatorType = typeof(IValidator<>).MakeGenericType(value.GetType());
            if (serviceProvider.GetService(validatorType) is not IValidator validator)
                continue;
            var result = await validator.ValidateAsync(new ValidationContext<object>(value));
            if (!result.IsValid)
                result.AddToModelState(context.ModelState);
        }

        if (!context.ModelState.IsValid)
        {
            context.Result = new BadRequestObjectResult(
                new ValidationProblemDetails(context.ModelState));
            return;
        }
        await next();
    }
}
```

Register globally in `Program.cs`:

```csharp
builder.Services.AddControllers(o => o.Filters.Add<FluentValidationActionFilter>());
```

### Custom Validators

Use `Must()` for synchronous custom rules and cross-field validation:

```csharp
public sealed class DateRangeRequestValidator : AbstractValidator<DateRangeRequest>
{
    public DateRangeRequestValidator()
    {
        RuleFor(x => x.StartDate)
            .NotEmpty();

        RuleFor(x => x.EndDate)
            .NotEmpty()
            .Must((request, endDate) => endDate > request.StartDate)
            .WithMessage("End date must be after start date.");

        RuleFor(x => x.Currency)
            .Must(BeAValidCurrencyCode)
            .WithMessage("Currency must be a valid ISO 4217 code.");
    }

    private static bool BeAValidCurrencyCode(string currency) =>
        currency.Length == 3 && currency.All(char.IsUpper);
}
```

### Async Validators

Use `MustAsync()` when validation requires I/O such as database uniqueness checks:

```csharp
public sealed class CreateCustomerRequestValidator : AbstractValidator<CreateCustomerRequest>
{
    public CreateCustomerRequestValidator(ICustomerRepository repository)
    {
        RuleFor(x => x.Email)
            .NotEmpty().EmailAddress()
            .MustAsync(async (email, ct) => !await repository.ExistsByEmailAsync(email, ct))
            .WithMessage("A customer with this email already exists.");

        RuleFor(x => x.TaxId)
            .NotEmpty()
            .MustAsync(async (taxId, ct) => !await repository.ExistsByTaxIdAsync(taxId, ct))
            .WithMessage("A customer with this Tax ID already exists.");
    }
}
```

Important: async validators require `ValidateAsync()` -- calling `Validate()` synchronously will throw.

### Reusable Rules

Extract shared validation logic with `Include()`:

```csharp
public sealed class PaginationValidator : AbstractValidator<IPaginatedRequest>
{
    public PaginationValidator()
    {
        RuleFor(x => x.Page).GreaterThanOrEqualTo(1);
        RuleFor(x => x.PageSize).InclusiveBetween(1, 100);
    }
}

public sealed class AuditFieldsValidator : AbstractValidator<IAuditableRequest>
{
    public AuditFieldsValidator()
    {
        RuleFor(x => x.CorrelationId).NotEmpty();
        RuleFor(x => x.RequestedBy).NotEmpty().MaximumLength(256);
    }
}

public sealed class SearchOrdersRequestValidator : AbstractValidator<SearchOrdersRequest>
{
    public SearchOrdersRequestValidator()
    {
        Include(new PaginationValidator());
        Include(new AuditFieldsValidator());

        RuleFor(x => x.Status)
            .IsInEnum()
            .When(x => x.Status.HasValue);
    }
}
```

### ProblemDetails Integration

Map FluentValidation errors to RFC 9457 ProblemDetails via `IExceptionHandler`:

```csharp
using FluentValidation;
using Microsoft.AspNetCore.Diagnostics;
using Microsoft.AspNetCore.Mvc;

namespace Ordering.Api.ExceptionHandlers;

public sealed class ValidationExceptionHandler : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(
        HttpContext httpContext, Exception exception, CancellationToken ct)
    {
        if (exception is not ValidationException validationException)
            return false;

        var errors = validationException.Errors
            .GroupBy(e => e.PropertyName)
            .ToDictionary(g => g.Key, g => g.Select(e => e.ErrorMessage).ToArray());

        var problemDetails = new ValidationProblemDetails(errors)
        {
            Type = "https://tools.ietf.org/html/rfc9110#section-15.5.1",
            Title = "Validation Failed",
            Status = StatusCodes.Status400BadRequest,
            Instance = httpContext.Request.Path
        };

        httpContext.Response.StatusCode = StatusCodes.Status400BadRequest;
        await httpContext.Response.WriteAsJsonAsync(problemDetails, ct);
        return true;
    }
}
```

Register in `Program.cs`:

```csharp
builder.Services.AddExceptionHandler<ValidationExceptionHandler>();
builder.Services.AddProblemDetails();
app.UseExceptionHandler();
```

## Decision Guide

| Scenario | Approach | Why |
|---|---|---|
| Simple DTO field constraints | `RuleFor` with built-in validators | Readable, testable, no custom logic needed |
| Cross-field validation | `Must()` with model access | Access to sibling properties via `(model, field)` overload |
| Uniqueness / DB lookup | `MustAsync()` with injected repo | Requires async I/O — keeps validator DI-friendly |
| Shared pagination / audit rules | `Include()` with interface validators | Avoids duplication across multiple request validators |
| Minimal API validation | `ValidationFilter<T>` endpoint filter | Runs before handler, returns `ValidationProblem` automatically |
| MVC controller validation | `FluentValidationActionFilter` | Integrates with `ModelState` and `ValidationProblemDetails` |
| Complex nested objects | `SetValidator()` on child + `RuleForEach` | Composes child validators, validates each collection element |
| Domain invariants | Do NOT use FluentValidation | Enforce inside entity constructor / methods |
| Startup config validation | `IValidateOptions<T>` with FluentValidation | Fail fast at app start if configuration is invalid |

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Validating domain entities with FluentValidation | Domain entities enforce their own invariants in constructors and methods |
| Calling `Validate()` synchronously when async rules exist | Always use `ValidateAsync()` — sync call throws on async rules |
| One mega-validator for all request types | One validator per request model, compose with `Include()` |
| Throwing generic exceptions on validation failure | Throw `ValidationException(result.Errors)` and handle with `IExceptionHandler` |
| Duplicating rules across validators | Extract shared rules into reusable validators and use `Include()` |
| Validating inside the controller action body | Use filters or middleware to validate before the action executes |
| Ignoring `CancellationToken` in async validators | Pass `CancellationToken` through `MustAsync` to support request cancellation |
| Hard-coding error messages without context | Use `WithMessage()` with placeholders: `{PropertyName}`, `{PropertyValue}` |
| Registering validators as Singleton when they have scoped dependencies | Use default `Scoped` lifetime or `Transient` if injecting scoped services |

## Detect Existing Patterns

1. Search for existing `AbstractValidator<T>` implementations in `Application/Validators/`
2. Check `Program.cs` for `AddValidatorsFromAssembly` registration calls
3. Look for endpoint filters or action filters that perform validation
4. Identify `IExceptionHandler` implementations that handle `ValidationException`
5. Follow the established validator naming convention: `{RequestType}Validator`
