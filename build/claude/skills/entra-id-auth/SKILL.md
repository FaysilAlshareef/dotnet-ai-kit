---
name: entra-id-auth
description: "Integrates Microsoft Entra ID authentication with Microsoft.Identity.Web — OIDC sign-in, On-Behalf-Of/downstream API tokens, and managed-identity for service-to-service calls. Use when authenticating against an external Entra ID (Azure AD) tenant or calling Microsoft Graph / protected downstream APIs. Do NOT use to RUN your own OAuth server (use openiddict-server), for passwordless device credentials (use passkeys-webauthn), or for hand-rolled JWT validation (use auth-jwt)."
---
# Microsoft Entra ID with Microsoft.Identity.Web

## Core Principles

- Use `Microsoft.Identity.Web` — it wraps MSAL, token caching, and OIDC so you never validate Entra tokens by hand.
- A **web API** protects endpoints with `AddMicrosoftIdentityWebApi`; a **web app** signs users in with `AddMicrosoftIdentityWebApp`.
- For downstream calls, use the **On-Behalf-Of** flow via `ITokenAcquisition` / `AddDownstreamApi` — exchange the incoming user token for a token scoped to the downstream resource. Never forward the raw incoming token.
- For **service-to-service** (no user), use **managed identity** (`DefaultAzureCredential` / `ManagedIdentityCredential`) — no client secrets in config.
- Configuration lives under an `AzureAd` section; secrets come from Key Vault or managed identity, never appsettings.
- Enforce scopes/roles with `RequiredScope` or `[Authorize(Roles=...)]` (claims-based policy detail belongs to `auth-policies`).

## Example

```csharp
// Program.cs — protect an API and enable an authenticated downstream call.
builder.Services
    .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddMicrosoftIdentityWebApi(builder.Configuration.GetSection("AzureAd"))
        .EnableTokenAcquisitionToCallDownstreamApi()
        .AddDownstreamApi("Graph", builder.Configuration.GetSection("Graph"))
        .AddInMemoryTokenCaches();

var app = builder.Build();
app.UseAuthentication();
app.UseAuthorization();

app.MapGet("/me/manager", async (IDownstreamApi graph) =>
        await graph.GetForUserAsync<ManagerDto>("Graph",
            o => o.RelativePath = "me/manager"))
   .RequireAuthorization()
   .RequireScope("User.Read"); // RequiredScope extension
```

```jsonc
// appsettings.json — no secrets; use managed identity / Key Vault.
{
  "AzureAd": {
    "Instance": "https://login.microsoftonline.com/",
    "TenantId": "<tenant-guid>",
    "ClientId": "<api-app-id>",
    "Audience": "api://<api-app-id>"
  }
}
```

```csharp
// Service-to-service (daemon) — managed identity, zero secrets.
var credential = new DefaultAzureCredential();
var token = await credential.GetTokenAsync(
    new TokenRequestContext(["api://<downstream-app-id>/.default"]));
```

## Gotchas

- The downstream API's expected **audience** must match what Entra issues (`api://<app-id>` vs the bare GUID) — a mismatch yields silent 401s.
- `AddInMemoryTokenCaches` is fine for a single instance; use a distributed cache (`AddDistributedTokenCaches`) behind a load balancer.
- On-Behalf-Of requires the downstream scope to be granted/consented in the app registration, or `MsalUiRequiredException` surfaces.
- Prefer managed identity over client secrets everywhere it is available; rotate any secret that must exist.

## References

- https://learn.microsoft.com/en-us/entra/identity-platform/index-web-api
- https://learn.microsoft.com/en-us/azure/active-directory/develop/microsoft-identity-web
