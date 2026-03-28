---
alwaysApply: true
description: Enforces error handling patterns appropriate to the project mode.
---

# Error Handling

Detect and follow the existing error handling pattern in the project.

## Microservice Mode

- Domain exceptions implement `IProblemDetailsProvider`
- `ApplicationExceptionInterceptor` converts exceptions to `RpcException`
- Problem details include: Type, Title, Status, Detail
- Status code mapping:
  - NotFound -> gRPC `NotFound`
  - Conflict -> gRPC `AlreadyExists`
- gRPC metadata key: `problem-details-bin`
- Control panel uses `ResponseResult<T>` with Switch pattern
- Idempotent handlers return true for `AlreadyExists` RpcException

## Generic Mode

- Use `Result<T>` pattern (`Result.Success`, `Result.Failure`) or ProblemDetails RFC 9457
- Map domain errors to HTTP status codes via ProblemDetails
- Use global exception handler middleware
- `FluentValidation` -> `ValidationException` -> 400 Bad Request

## Both Modes

- Never swallow exceptions -- log then re-throw or return false for retry
- Never return generic error messages to users
- Use structured logging for all exception context
- Client must send an ID for idempotency -- never generate idempotency keys server-side
- For retry scenarios, use client-provided correlation IDs

## Detection Instructions

1. Check for existing exception types, middleware, or interceptors in the project
2. Identify whether the project uses Result pattern, exceptions, or ProblemDetails
3. Follow the established pattern for all new error handling code
4. If no pattern exists, choose based on the project mode (microservice or generic)

## Related Skills
- `skills/core/functional-csharp/SKILL.md` — Result<T> pattern, railway-oriented programming
- `skills/core/fluent-validation/SKILL.md` — standalone validation patterns
