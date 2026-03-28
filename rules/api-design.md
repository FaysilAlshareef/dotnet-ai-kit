---
alwaysApply: true
description: Enforces REST API conventions — status codes, ProblemDetails, versioning, and endpoint design.
---

# API Design Rules

Detect the existing API style (Minimal API or Controllers) and follow it consistently.

## MUST

- Return correct HTTP status codes: 200 OK, 201 Created, 204 No Content, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity
- Return `ProblemDetails` (RFC 9457) for all error responses
- Use `TypedResults` in Minimal API for OpenAPI schema generation
- Use `[ProducesResponseType]` on controller actions for documentation
- Use API versioning on all public endpoints (`Asp.Versioning`)
- Use `CancellationToken` on all endpoint handlers
- Return `Paginated<T>` wrapper for all list endpoints (items, total, page, pageSize)

## MUST NOT

- Never return 200 with an error body — use proper status codes
- Never return raw exception messages in responses
- Never use `string` route parameters for IDs — use `Guid` or strongly-typed IDs
- Never mix Minimal API and Controllers in the same project unless existing pattern
- Never create endpoints without OpenAPI summary and description

## Endpoint Naming

| HTTP Method | Route Pattern | Returns | Example |
|-------------|---------------|---------|---------|
| GET | `/resources` | 200 + list | `GET /orders` |
| GET | `/resources/{id}` | 200 or 404 | `GET /orders/{id}` |
| POST | `/resources` | 201 + location | `POST /orders` |
| PUT | `/resources/{id}` | 200 or 204 | `PUT /orders/{id}` |
| DELETE | `/resources/{id}` | 204 or 404 | `DELETE /orders/{id}` |

## Detection Instructions

1. Check for endpoints returning 200 on errors — fix status codes
2. Check for missing `[ProducesResponseType]` on controllers
3. Verify all error responses use ProblemDetails format
4. Check for unbounded list endpoints — add pagination
5. Verify API versioning is configured

## Related Skills
- `skills/api/minimal-api/SKILL.md` — Minimal API patterns
- `skills/api/controllers/SKILL.md` — controller patterns
- `skills/api/versioning/SKILL.md` — versioning strategies
- `skills/api/caching-strategies/SKILL.md` — response caching, ETag
- `skills/api/rate-limiting/SKILL.md` — rate limiting policies
