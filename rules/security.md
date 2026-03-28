---
alwaysApply: true
description: Enforces security best practices — authentication, input validation, secrets, CORS, and output encoding.
---

# Security Rules

Every endpoint, every input, every secret — secure by default.

## MUST

- All API endpoints MUST have `[Authorize]` unless explicitly designed as public (annotate public endpoints with `[AllowAnonymous]` to signal intent)
- All user input MUST be validated at the API boundary before processing
- All output rendered in HTML MUST be encoded (`HtmlEncoder.Default.Encode()`)
- All SQL MUST use parameterized queries — never concatenate user input
- All secrets MUST use user secrets (dev) or Key Vault / environment variables (prod)
- All production APIs MUST enforce HTTPS
- All CORS policies MUST use explicit origins — never `AllowAnyOrigin()` with `AllowCredentials()`
- All file uploads MUST validate extension, MIME type, and size

## MUST NOT

- Do not store secrets in `appsettings.json`, source code, or environment-specific config files committed to git
- Do not log sensitive data (passwords, tokens, connection strings, PII)
- Do not return stack traces or internal exception details in production responses
- Do not disable CORS or use wildcard origins in production
- Do not use `@Html.Raw()` on user-provided content without sanitization
- Do not trust client-side validation alone — always re-validate server-side

## Security Headers

Production APIs should include:
- `Content-Security-Policy: default-src 'self'`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`

## Detection Instructions

1. Check for endpoints missing `[Authorize]` — add or mark `[AllowAnonymous]` with comment
2. Check for raw SQL string concatenation — replace with parameterized queries
3. Check for secrets in appsettings.json — move to user secrets or Key Vault
4. Check for `AllowAnyOrigin()` combined with `AllowCredentials()` — fix CORS policy
5. Check for missing input validation on POST/PUT endpoints

## Related Skills
- `skills/security/auth-jwt/SKILL.md` — JWT authentication patterns
- `skills/security/auth-policies/SKILL.md` — policy-based authorization
- `skills/security/cors-configuration/SKILL.md` — CORS policy setup
- `skills/security/input-sanitization/SKILL.md` — XSS prevention, CSP headers
- `skills/security/data-protection/SKILL.md` — encryption, Key Vault
