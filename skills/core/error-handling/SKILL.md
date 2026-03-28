---
name: error-handling
description: >
  Domain exception hierarchy, ProblemDetails for REST, RpcException for gRPC,
  interceptor-based mapping, structured error codes, and error logging.
  Trigger: error handling, exceptions, problem details, RpcException, error codes.
metadata:
  category: core
  agent: dotnet-architect
  alwaysApply: true
---

# Error Handling Patterns

## Core Principles

- Domain exceptions inherit from a `DomainException` base class
- REST APIs return RFC 9457 ProblemDetails responses
- gRPC services throw `RpcException` with `StatusCode` and `Trailers`
- Interceptors handle automatic exception-to-error mapping
- Structured error codes identify specific failure scenarios
- Never swallow exceptions — log with structured context then re-throw or convert

## Exception Hierarchy

```csharp
namespace {Company}.{Domain}.Domain.Exceptions;

public abstract class DomainException(
    string message,
    string errorCode,
    Exception? innerException = null) : Exception(message, innerException)
{
    public string ErrorCode { get; } = errorCode;
}

public class NotFoundException(
    string entityName,
    object entityId)
    : DomainException(
        $"{entityName} with ID '{entityId}' was not found.",
        $"{entityName.ToUpperInvariant()}_NOT_FOUND")
{
    public string EntityName { get; } = entityName;
    public object EntityId { get; } = entityId;
}

public class ValidationException(
    string message,
    string errorCode,
    IDictionary<string, string[]>? errors = null)
    : DomainException(message, errorCode)
{
    public IDictionary<string, string[]> Errors { get; } =
        errors ?? new Dictionary<string, string[]>();
}

public class ConcurrencyException(
    string entityName,
    object entityId)
    : DomainException(
        $"Concurrency conflict on {entityName} with ID '{entityId}'.",
        $"{entityName.ToUpperInvariant()}_CONCURRENCY_CONFLICT")
{
    public string EntityName { get; } = entityName;
    public object EntityId { get; } = entityId;
}
```

## Structured Error Codes

Use uppercase snake_case constants scoped to the domain:

```csharp
public static class ErrorCodes
{
    public const string DrawNotFound = "DRAW_NOT_FOUND";
    public const string InvalidSequence = "INVALID_SEQUENCE";
    public const string DuplicateEntry = "DUPLICATE_ENTRY";
    public const string InsufficientBalance = "INSUFFICIENT_BALANCE";
    public const string OrderAlreadyCancelled = "ORDER_ALREADY_CANCELLED";
}
```

## IProblemDetailsProvider (REST)

```csharp
using Microsoft.AspNetCore.Http;

namespace {Company}.{Domain}.Domain.Exceptions;

public interface IProblemDetailsProvider
{
    string Type { get; }
    string Title { get; }
    int Status { get; }
    string Detail { get; }
}

public class NotFoundException : DomainException, IProblemDetailsProvider
{
    // ... constructor and properties as above ...

    public string Type => "https://tools.ietf.org/html/rfc9110#section-15.5.5";
    public string Title => "Not Found";
    public int Status => StatusCodes.Status404NotFound;
    public string Detail => Message;
}
```

### ProblemDetails Response Format

```json
{
  "type": "https://tools.ietf.org/html/rfc9110#section-15.5.5",
  "title": "Not Found",
  "status": 404,
  "detail": "Draw with ID '3fa85f64-5717-4562-b3fc-2c963f66afa6' was not found.",
  "instance": "/api/draws/3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "errorCode": "DRAW_NOT_FOUND"
}
```

## gRPC RpcException Mapping

```csharp
using Grpc.Core;
using System.Text.Json;

namespace {Company}.{Domain}.Grpc.Interceptors;

public class ApplicationExceptionInterceptor : Interceptor
{
    public override async Task<TResponse> UnaryServerHandler<TRequest, TResponse>(
        TRequest request,
        ServerCallContext context,
        UnaryServerMethod<TRequest, TResponse> continuation)
    {
        try
        {
            return await continuation(request, context);
        }
        catch (DomainException ex) when (ex is IProblemDetailsProvider provider)
        {
            var metadata = new Metadata();
            var problemDetails = new
            {
                provider.Type,
                provider.Title,
                provider.Status,
                provider.Detail,
                ex.ErrorCode
            };
            metadata.Add("problem-details-bin",
                JsonSerializer.SerializeToUtf8Bytes(problemDetails));

            throw new RpcException(
                new Status(MapToGrpcStatusCode(provider.Status), ex.Message),
                metadata);
        }
    }

    private static StatusCode MapToGrpcStatusCode(int httpStatus) => httpStatus switch
    {
        400 => StatusCode.InvalidArgument,
        404 => StatusCode.NotFound,
        409 => StatusCode.AlreadyExists,
        422 => StatusCode.InvalidArgument,
        _ => StatusCode.Internal
    };
}
```

Key details:
- Catches `DomainException` that implements `IProblemDetailsProvider`
- Serializes problem details to gRPC binary metadata trailer (`problem-details-bin`)
- Maps HTTP status codes to gRPC status codes
- Uncaught exceptions become `StatusCode.Internal`

## gRPC Interceptor Registration

```csharp
// In Program.cs or GrpcContainer
builder.Services.AddGrpc(options =>
{
    options.Interceptors.Add<ApplicationExceptionInterceptor>();
});
```

## Error Logging with Structured Context

```csharp
public async Task<bool> Handle(
    Event<OrderCreatedData> @event,
    CancellationToken cancellationToken)
{
    try
    {
        // ... handler logic ...
    }
    catch (DomainException ex)
    {
        _logger.LogError(ex,
            "Domain error processing event {EventType} for aggregate {AggregateId}. " +
            "ErrorCode: {ErrorCode}, UserId: {UserId}",
            @event.Type,
            @event.AggregateId,
            ex.ErrorCode,
            @event.UserId);
        throw;
    }
}
```

Always include in structured log context:
- `AggregateId` — which entity was affected
- `UserId` — who triggered the operation
- `EventType` — what operation was attempted
- `ErrorCode` — machine-readable error identifier

## Status Code Mapping

| Exception Type | HTTP Status | gRPC StatusCode |
|---|---|---|
| `NotFoundException` | 404 | `NotFound` |
| `ValidationException` | 400 | `InvalidArgument` |
| `ConcurrencyException` | 409 | `AlreadyExists` |
| `DomainException` (other) | 422 | `InvalidArgument` |
| Unhandled `Exception` | 500 | `Internal` |

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Catching generic `Exception` and swallowing | Catch specific types, log, re-throw or convert |
| String error messages without codes | Use structured `ErrorCode` constants |
| Throwing `RpcException` from domain layer | Throw `DomainException`, let interceptor convert |
| Generic "An error occurred" responses | Return specific ProblemDetails with error code |
| Logging without context properties | Include aggregateId, userId, eventType in every log |

## Detect Existing Patterns

1. Search for existing exception base classes in `Domain/Exceptions/`
2. Check for `IProblemDetailsProvider` implementations
3. Look for gRPC interceptors in `Grpc/Interceptors/`
4. Identify error code constants or enums
5. Follow the established exception hierarchy for new error types
