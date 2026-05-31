---
name: openiddict-server
description: "Stands up a self-hosted OAuth2/OpenID Connect authorization server with OpenIddict 10.x — issuing your own access/identity tokens via authorization-code+PKCE and client-credentials flows. Use when YOU own the identity provider and mint tokens for first-party clients/APIs. Do NOT use to consume an external Microsoft Entra tenant (use entra-id-auth), for WebAuthn credentials (use passkeys-webauthn), or for validating already-issued JWTs (use auth-jwt)."
---
# OpenIddict 10.x — Self-Hosted OAuth2/OIDC Server

## Core Principles

- OpenIddict turns your ASP.NET Core app into a standards-compliant **authorization server**: it owns the `/connect/authorize`, `/connect/token`, and discovery endpoints.
- Three cooperating pieces: the **core** (EF Core stores for apps/scopes/tokens), the **server** (issues tokens), and the **validation** (resource APIs verify them).
- Always require **PKCE** for interactive clients and prefer the **authorization-code** flow; use **client-credentials** only for machine-to-machine.
- In production use **persistent signing/encryption certificates** (e.g. from Key Vault); the development cert helpers are for local only.
- Register clients (`applications`) and `scopes` at startup via `IOpenIddictApplicationManager`; never hard-code client secrets in source.
- Enforce scope-based access on resource APIs with the OpenIddict validation handler + authorization policies.

## Example

```csharp
// Program.cs — authorization server + EF Core stores.
builder.Services.AddDbContext<AuthDbContext>(o =>
{
    o.UseNpgsql(connString);
    o.UseOpenIddict();
});

builder.Services.AddOpenIddict()
    .AddCore(o => o.UseEntityFrameworkCore().UseDbContext<AuthDbContext>())
    .AddServer(o =>
    {
        o.SetAuthorizationEndpointUris("connect/authorize")
         .SetTokenEndpointUris("connect/token");

        o.AllowAuthorizationCodeFlow().RequireProofKeyForCodeExchange()
         .AllowClientCredentialsFlow();

        o.RegisterScopes("api", "openid", "profile");

        // Dev only — replace with X509 certs from Key Vault in prod.
        o.AddDevelopmentEncryptionCertificate()
         .AddDevelopmentSigningCertificate();

        o.UseAspNetCore()
         .EnableAuthorizationEndpointPassthrough()
         .EnableTokenEndpointPassthrough();
    })
    .AddValidation(o =>
    {
        o.UseLocalServer();
        o.UseAspNetCore();
    });
```

```csharp
// Token endpoint handler for client-credentials.
app.MapPost("/connect/token", async (HttpContext ctx) =>
{
    var request = ctx.GetOpenIddictServerRequest()!;
    if (!request.IsClientCredentialsGrantType())
        return Results.BadRequest();

    var identity = new ClaimsIdentity(
        OpenIddictServerAspNetCoreDefaults.AuthenticationScheme);
    identity.SetClaim(Claims.Subject, request.ClientId!);
    var principal = new ClaimsPrincipal(identity);
    principal.SetScopes(request.GetScopes());

    return Results.SignIn(principal,
        authenticationScheme: OpenIddictServerAspNetCoreDefaults.AuthenticationScheme);
});
```

## Gotchas

- The development certificates regenerate per environment — tokens issued by one instance fail validation on another. Pin shared certs behind a load balancer.
- `RegisterScopes` at startup does not create persisted `scope` records; seed them via `IOpenIddictScopeManager` if a resource needs descriptor metadata.
- Forgetting `RequireProofKeyForCodeExchange()` leaves public clients open to code interception.
- Run a token/authorization **pruning** background job (`OpenIddict` provides one) or the token table grows unbounded.

## References

- https://documentation.openiddict.com/
- https://documentation.openiddict.com/guides/getting-started/
