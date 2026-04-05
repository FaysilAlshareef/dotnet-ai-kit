---
alwaysApply: true
description: "Architecture profile for gateway projects — hard constraints"
---

# Architecture Profile: Gateway (REST-to-gRPC Bridge)

## HARD CONSTRAINTS

### Endpoint Registration
- MUST use `ServicesURLsOptions` with `[Required, Url]` for all backend service URLs
- MUST call `ValidateOnStart()` on service URL options — NEVER skip startup validation
- MUST use `AddGrpcClient<T>((provider, options) => ...)` callback — NEVER resolve URLs at registration time
- MUST use `RegisterInterceptors` to add `GlobalMetadataInterceptor` for culture/claims forwarding
- MUST share one `ServicesURLsOptions` class for all URLs — NEVER create per-client options classes
- Multiple gRPC clients MAY share the same URL property when they connect to the same host

### Gateway Endpoint Pattern
- ALWAYS inherit `ControllerBaseV1` — NEVER raw `ControllerBase` or `Controller`
- ALWAYS use `[Route(DefaultRoute)]` from the base class
- MUST inject typed gRPC clients via primary constructor with `private readonly` backing fields
- ALWAYS map request/response inline in controller actions — NEVER create separate mapping classes
- Enum conversions are the ONLY exception where separate extension methods are allowed
- MUST return `Paginated<T>` for list endpoints — NEVER raw collections
- MUST return `Response { Message }` wrapper for command endpoints — NEVER raw strings
- NEVER expose gRPC proto types in REST responses — always map to REST-specific DTOs
- NEVER put business logic in gateway controllers — gateway ONLY maps and delegates

```csharp
// ANTI-PATTERN: business logic in gateway
if (model.Items.Count > 100) return BadRequest(); // WRONG — backend validates

// ANTI-PATTERN: returning proto types
return Ok(grpcResponse); // WRONG — map to REST DTO
return Ok(new OrderOutput { Id = Guid.Parse(grpcResponse.Id) }); // CORRECT
```

### Authorization
- MUST apply `[Authorize]`, `[Authorize(Policy = ...)]`, or `[Authorize(Roles = ...)]` at class level
- MUST use `Policy` constants class for policy names — NEVER hardcode strings in attributes
- MUST use `Roles` constants class for role names — NEVER hardcode role strings
- MUST call `UseAuthentication()` before `UseAuthorization()` in middleware pipeline
- MUST register authorization handlers as `AddScoped` — NEVER singleton (handlers use scoped services)

### Security
- MUST use `AddJwtAuthentication` and `AddPolicies` as separate registrations
- MUST use `ApiScope` enum to configure the Consumer policy per gateway type
- Custom authorization MUST use `IAuthorizationRequirement` + `AuthorizationHandler<T>` pattern
- MUST use `ScalarBasicAuthMiddleware` to protect `/scalar` and `/openapi` in production

### Scalar API Documentation
- MUST use `AddBaseScalarApiDocumentation` with `OpenApiDocEntry` records — NEVER Swagger UI
- MUST use `BearerSecuritySchemeTransformer` on every OpenAPI document
- MUST use `ControllerBaseV1.GetDocEntry()` for versioned doc entries
- MUST use `ScalarServerOptions` from configuration for server URL — NEVER hardcode
- MUST use `AddControllersWithConfigurations()` for slug routing and global filters
- MUST use `MapControllersWithAuthorization()` — NEVER `MapControllers()` without auth

### Versioning
- MUST use versioned base classes (`ControllerBaseV1`) with `[ApiExplorerSettings(GroupName)]`
- Route prefix MUST follow `api/v{n}/[controller]` pattern
- MUST use `SlugifyControllerNamesConvention` for URL casing

## Testing Requirements

- MUST test gRPC error mapping to ProblemDetails responses
- MUST test authorization policies (missing token, wrong role, correct role)
- MUST verify Paginated response structure (Results, CurrentPage, PageSize, Total, LastPage)

## Data Access

- Gateway has NO direct database access — ALWAYS delegate to backend gRPC services
- MUST use `HttpResponseExceptionFilter` for global gRPC-to-HTTP error mapping
- MUST use `ValidateAccessFilter` for access claims validation
