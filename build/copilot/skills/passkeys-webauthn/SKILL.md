---
name: passkeys-webauthn
description: "Adds passkey (WebAuthn/FIDO2) registration and passwordless sign-in to ASP.NET Core 10 Identity using the built-in passkey APIs and the browser navigator.credentials JS interop. Use when offering phishing-resistant passwordless login backed by platform/roaming authenticators. Do NOT use for federated external IdP sign-in (use entra-id-auth), for issuing OAuth tokens (use openiddict-server), or for bearer-token validation (use auth-jwt)."
---
# Passkeys / WebAuthn (ASP.NET Core 10 Identity)

## Core Principles

- ASP.NET Core 10 Identity ships **first-class passkey support** — no third-party FIDO2 library needed for the common case. A passkey is a public-key credential bound to your origin (the Relying Party).
- Two ceremonies: **registration** (attestation) creates and stores a credential for a signed-in user; **authentication** (assertion) verifies a challenge signed by the authenticator's private key. The private key never leaves the device.
- The server issues a fresh, single-use **challenge** for every ceremony and validates the returned signature, the RP ID, and the origin. Never reuse challenges.
- The browser side calls `navigator.credentials.create()` / `.get()`; .NET serializes the options and parses the response via the Identity passkey APIs (`PasskeyCreationOptions` / `PerformPasskeyAssertion`).
- Store credentials per user (credential ID, public key, sign-count); reject a sign-count that goes backwards (cloned authenticator).
- Treat passkeys as a primary factor; keep a recovery path (a second passkey or a recovery code), not a password fallback that reintroduces phishing risk.

## Example

```csharp
// Registration: produce options the browser passes to navigator.credentials.create
app.MapPost("/passkey/register/begin",
    async (UserManager<AppUser> users, SignInManager<AppUser> signIn,
           HttpContext ctx) =>
{
    var user = await users.GetUserAsync(ctx.User);
    var options = await signIn.MakePasskeyCreationOptionsAsync(
        new PasskeyCreationArgs(new PasskeyUserEntity(
            user!.Id, user.UserName!, displayName: user.UserName!)));
    return Results.Content(options.AsJson(), "application/json");
}).RequireAuthorization();

// Authentication: verify the assertion the browser returns.
app.MapPost("/passkey/login/finish",
    async (SignInManager<AppUser> signIn, [FromBody] string credentialJson) =>
{
    var result = await signIn.PerformPasskeyAssertionAsync(credentialJson);
    return result.Succeeded
        ? Results.Ok()
        : Results.Unauthorized();
});
```

```javascript
// wwwroot/passkey.js — browser ceremony (simplified)
const opts = await (await fetch('/passkey/register/begin', {method:'POST'})).json();
opts.challenge = base64UrlToBuffer(opts.challenge);
opts.user.id   = base64UrlToBuffer(opts.user.id);
const cred = await navigator.credentials.create({ publicKey: opts });
await fetch('/passkey/register/finish', {
  method: 'POST', headers: {'Content-Type':'application/json'},
  body: JSON.stringify(serializeCredential(cred)) });
```

## Gotchas

- **RP ID must match the registrable domain** — a passkey created on `app.example.com` will not work if RP ID is set to `example.com` incorrectly, and localhost vs 127.0.0.1 are distinct origins.
- Buffers (`challenge`, `user.id`, `rawId`) cross JS↔JSON as **base64url** — encode/decode both ways or the ceremony fails opaquely.
- Require **user verification** (PIN/biometric) for step-up actions; "preferred" silently downgrades on some authenticators.
- Persist and check the signature counter; ignoring it defeats clone detection.

## References

- https://learn.microsoft.com/en-us/aspnet/core/security/authentication/identity-passkeys
- https://www.w3.org/TR/webauthn-3/
