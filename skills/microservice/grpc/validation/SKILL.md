---
name: validation
description: >
  FluentValidation for gRPC requests with Calzolari integration. Covers
  AbstractValidator for proto requests, resource-based messages, and pre-handler validation.
  Trigger: gRPC validation, FluentValidation, Calzolari, request validation.
category: microservice/grpc
agent: command-architect
---

# Validation — FluentValidation + gRPC

## Core Principles

- `AbstractValidator<TRequest>` validates gRPC requests before handlers execute
- Calzolari package integrates FluentValidation with gRPC pipeline
- Validation errors return `StatusCode.InvalidArgument` with details
- Error messages use resource strings (`Phrases.xxx`) for localization
- `AddAppValidators()` scans assembly for all validators

## Key Patterns

### Request Validator

```csharp
namespace {Company}.{Domain}.Grpc.Validators;

public sealed class CreateOrderRequestValidator
    : AbstractValidator<CreateOrderRequest>
{
    public CreateOrderRequestValidator()
    {
        RuleFor(x => x.CustomerName)
            .NotEmpty()
            .WithMessage(Phrases.CustomerNameRequired)
            .MaximumLength(200)
            .WithMessage(Phrases.CustomerNameTooLong);

        RuleFor(x => x.Total)
            .GreaterThan(0)
            .WithMessage(Phrases.InvalidTotal);

        RuleFor(x => x.Items)
            .NotEmpty()
            .WithMessage(Phrases.ItemsRequired);

        RuleForEach(x => x.Items).ChildRules(item =>
        {
            item.RuleFor(x => x.ProductId)
                .NotEmpty()
                .WithMessage(Phrases.ProductIdRequired);

            item.RuleFor(x => x.Quantity)
                .GreaterThan(0)
                .WithMessage(Phrases.InvalidQuantity);

            item.RuleFor(x => x.UnitPrice)
                .GreaterThan(0)
                .WithMessage(Phrases.InvalidUnitPrice);
        });
    }
}
```

### Custom Validation Rules

```csharp
namespace {Company}.{Domain}.Grpc.Validators;

public sealed class UpdateOrderRequestValidator
    : AbstractValidator<UpdateOrderRequest>
{
    public UpdateOrderRequestValidator()
    {
        RuleFor(x => x.OrderId)
            .NotEmpty()
            .Must(BeValidGuid)
            .WithMessage(Phrases.InvalidOrderId);

        // Conditional validation
        When(x => x.CustomerName is not null, () =>
        {
            RuleFor(x => x.CustomerName.Value)
                .NotEmpty()
                .MaximumLength(200);
        });
    }

    private static bool BeValidGuid(string value)
        => Guid.TryParse(value, out _);
}

// Phone number validation (Libyan format)
public sealed class PhoneValidator : AbstractValidator<string>
{
    public PhoneValidator()
    {
        RuleFor(x => x)
            .Matches(@"^0(91|92|93|94|95)\d{7}$")
            .WithMessage(Phrases.InvalidPhoneNumber);
    }
}
```

### Registration with Calzolari

```csharp
namespace {Company}.{Domain}.Grpc;

public static class ValidationRegistration
{
    public static IServiceCollection AddAppValidators(
        this IServiceCollection services)
    {
        // Calzolari gRPC validation integration
        services.AddGrpcValidation();

        // Scan assembly for all validators
        services.AddValidatorsFromAssemblyContaining<CreateOrderRequestValidator>();

        return services;
    }
}

// In Program.cs
builder.Services.AddGrpc(options =>
{
    options.EnableMessageValidation();
});
builder.Services.AddAppValidators();
```

### Validation Error Response

```
When validation fails, Calzolari returns:
  StatusCode: InvalidArgument
  Detail: "Validation failed"
  Trailers:
    - validation-errors-text: JSON array of validation failures
      [
        { "propertyName": "CustomerName", "errorMessage": "Customer name is required" },
        { "propertyName": "Total", "errorMessage": "Total must be greater than 0" }
      ]
```

### Manual Validation (Without Calzolari)

```csharp
// For cases needing manual validation control
public sealed class OrderCommandsService(
    IMediator mediator,
    IValidator<CreateOrderRequest> validator)
    : OrderCommands.OrderCommandsBase
{
    public override async Task<CreateOrderResponse> CreateOrder(
        CreateOrderRequest request, ServerCallContext context)
    {
        var validationResult = await validator.ValidateAsync(request);
        if (!validationResult.IsValid)
        {
            var errors = validationResult.Errors
                .Select(e => $"{e.PropertyName}: {e.ErrorMessage}");
            throw new RpcException(new Status(
                StatusCode.InvalidArgument,
                string.Join("; ", errors)));
        }

        var command = request.ToCommand();
        var output = await mediator.Send(command);
        return output.ToCreateResponse();
    }
}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Hardcoded error messages | Use resource strings (Phrases.xxx) |
| Validation in handler instead of validator | Validate at gRPC boundary |
| Missing validator for a request type | Every request needs a validator |
| Not using ChildRules for repeated | Use RuleForEach with ChildRules |
| Catching validation exceptions | Let Calzolari handle the response |

## Detect Existing Patterns

```bash
# Find validators
grep -r "AbstractValidator<.*Request" --include="*.cs" src/

# Find Calzolari registration
grep -r "AddGrpcValidation\|EnableMessageValidation" --include="*.cs" src/

# Find AddAppValidators
grep -r "AddAppValidators\|AddValidatorsFrom" --include="*.cs" src/

# Find resource strings in validators
grep -r "Phrases\." --include="*.cs" src/Grpc/Validators/
```

## Adding to Existing Project

1. **Create validator in `Grpc/Validators/` directory** matching request name
2. **Use existing `Phrases` resource** for error messages
3. **Ensure `AddAppValidators()` is called** (scans assembly automatically)
4. **Follow existing validation patterns** — check how nullable fields are handled
5. **Test validators** with xUnit and invalid inputs
