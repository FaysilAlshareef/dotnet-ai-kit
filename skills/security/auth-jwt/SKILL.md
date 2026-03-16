---
name: auth-jwt
description: >
  JWT authentication setup, token generation with claims, refresh token flow,
  and token validation configuration.
  Trigger: JWT, authentication, token, Bearer, claims, refresh token.
category: security
agent: api-designer
---

# JWT Authentication

## Core Principles

- Short-lived access tokens (15-60 min) with longer-lived refresh tokens
- Validate issuer, audience, lifetime, and signing key on every request
- Use `JsonWebTokenHandler` (.NET 10+) or `JwtSecurityTokenHandler` for token generation
- Store signing keys in user secrets (dev) or Key Vault (prod) — never in appsettings
- Refresh tokens must be rotated on use and revocable

## Patterns

### JWT Bearer Authentication Setup

```csharp
// Program.cs
builder.Services.AddAuthentication(
    JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters =
            new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer = builder.Configuration["Jwt:Issuer"],
            ValidAudience = builder.Configuration["Jwt:Audience"],
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(
                    builder.Configuration["Jwt:Key"]!)),
            ClockSkew = TimeSpan.FromSeconds(30) // default is 5 min
        };
    });

builder.Services.AddAuthorization();

var app = builder.Build();

app.UseAuthentication();
app.UseAuthorization();
```

### JWT Options Class

```csharp
public sealed class JwtOptions
{
    public const string SectionName = "Jwt";

    [Required]
    public required string Issuer { get; init; }

    [Required]
    public required string Audience { get; init; }

    [Required, MinLength(32)]
    public required string Key { get; init; }

    [Range(1, 1440)]
    public int AccessTokenExpiryMinutes { get; init; } = 60;

    [Range(1, 43200)]
    public int RefreshTokenExpiryMinutes { get; init; } = 10080; // 7 days
}

// Registration
builder.Services.AddOptions<JwtOptions>()
    .BindConfiguration(JwtOptions.SectionName)
    .ValidateDataAnnotations()
    .ValidateOnStart();
```

### Token Generation Service

```csharp
public interface ITokenService
{
    TokenResponse GenerateTokens(
        User user, IEnumerable<string> permissions);
}

public sealed class TokenService(IOptions<JwtOptions> options)
    : ITokenService
{
    public TokenResponse GenerateTokens(
        User user, IEnumerable<string> permissions)
    {
        var claims = new List<Claim>
        {
            new(JwtRegisteredClaimNames.Sub, user.Id.ToString()),
            new(JwtRegisteredClaimNames.Email, user.Email),
            new(JwtRegisteredClaimNames.Jti,
                Guid.NewGuid().ToString()),
            new("permissions", string.Join(",", permissions))
        };

        foreach (var role in user.Roles)
            claims.Add(new Claim(ClaimTypes.Role, role));

        var key = new SymmetricSecurityKey(
            Encoding.UTF8.GetBytes(options.Value.Key));
        var credentials = new SigningCredentials(
            key, SecurityAlgorithms.HmacSha256);
        var expiry = DateTime.UtcNow.AddMinutes(
            options.Value.AccessTokenExpiryMinutes);

        var token = new JwtSecurityToken(
            issuer: options.Value.Issuer,
            audience: options.Value.Audience,
            claims: claims,
            expires: expiry,
            signingCredentials: credentials);

        return new TokenResponse(
            AccessToken: new JwtSecurityTokenHandler().WriteToken(token),
            ExpiresAt: expiry,
            RefreshToken: GenerateRefreshToken());
    }

    private static string GenerateRefreshToken()
        => Convert.ToBase64String(RandomNumberGenerator.GetBytes(64));
}

public sealed record TokenResponse(
    string AccessToken,
    DateTime ExpiresAt,
    string RefreshToken);
```

### Refresh Token Flow

```csharp
public sealed record RefreshTokenCommand(
    string RefreshToken) : IRequest<Result<TokenResponse>>;

internal sealed class RefreshTokenHandler(
    ITokenService tokenService,
    IRefreshTokenRepository refreshTokenRepo,
    IUserRepository userRepo)
    : IRequestHandler<RefreshTokenCommand, Result<TokenResponse>>
{
    public async Task<Result<TokenResponse>> Handle(
        RefreshTokenCommand request, CancellationToken ct)
    {
        var stored = await refreshTokenRepo
            .FindByTokenAsync(request.RefreshToken, ct);

        if (stored is null || stored.IsExpired || stored.IsRevoked)
            return Result<TokenResponse>.Failure(
                Error.Unauthorized("Token.Invalid",
                    "Invalid or expired refresh token"));

        // Rotate: revoke old token
        stored.Revoke();

        var user = await userRepo.FindAsync(stored.UserId, ct);
        var permissions = await userRepo
            .GetPermissionsAsync(user!.Id, ct);

        var newToken = tokenService.GenerateTokens(
            user!, permissions);

        // Store new refresh token
        await refreshTokenRepo.StoreAsync(
            new RefreshToken(user!.Id, newToken.RefreshToken,
                DateTime.UtcNow.AddDays(7)),
            ct);

        await refreshTokenRepo.SaveChangesAsync(ct);

        return Result<TokenResponse>.Success(newToken);
    }
}
```

### Login Endpoint

```csharp
app.MapPost("/auth/login", async (
    LoginRequest request,
    ISender sender, CancellationToken ct) =>
{
    var result = await sender.Send(
        new LoginCommand(request.Email, request.Password), ct);

    return result.Match(
        token => Results.Ok(token),
        error => Results.Unauthorized());
});

app.MapPost("/auth/refresh", async (
    RefreshTokenRequest request,
    ISender sender, CancellationToken ct) =>
{
    var result = await sender.Send(
        new RefreshTokenCommand(request.RefreshToken), ct);

    return result.Match(
        token => Results.Ok(token),
        error => Results.Unauthorized());
});
```

### Accessing Claims in Handlers

```csharp
public interface ICurrentUserService
{
    Guid UserId { get; }
    string Email { get; }
    IReadOnlyList<string> Roles { get; }
    IReadOnlyList<string> Permissions { get; }
}

internal sealed class CurrentUserService(
    IHttpContextAccessor httpContextAccessor)
    : ICurrentUserService
{
    private ClaimsPrincipal User =>
        httpContextAccessor.HttpContext?.User
        ?? throw new UnauthorizedAccessException();

    public Guid UserId => Guid.Parse(
        User.FindFirstValue(JwtRegisteredClaimNames.Sub)!);

    public string Email =>
        User.FindFirstValue(JwtRegisteredClaimNames.Email)!;

    public IReadOnlyList<string> Roles =>
        User.FindAll(ClaimTypes.Role)
            .Select(c => c.Value).ToList();

    public IReadOnlyList<string> Permissions =>
        (User.FindFirstValue("permissions") ?? "")
            .Split(',', StringSplitOptions.RemoveEmptyEntries)
            .ToList();
}
```

## Anti-Patterns

- Storing JWT signing keys in appsettings.json (use user secrets / Key Vault)
- Default ClockSkew of 5 minutes (reduce to 30 seconds)
- No refresh token rotation (allows token reuse after theft)
- Long-lived access tokens (> 60 minutes)
- Storing sensitive data in JWT claims (tokens are Base64 encoded, not encrypted)
- Not validating issuer and audience

## Detect Existing Patterns

1. Search for `AddJwtBearer` in `Program.cs`
2. Look for `JwtSecurityTokenHandler` or `JsonWebTokenHandler` usage
3. Check for `TokenValidationParameters` configuration
4. Look for `ITokenService` or similar abstraction
5. Check for `[Authorize]` attributes on controllers/endpoints

## Adding to Existing Project

1. **Add JWT Bearer authentication** with full validation parameters
2. **Create options class** with `ValidateOnStart` for JWT configuration
3. **Implement token service** for access + refresh token generation
4. **Add refresh token storage** and rotation logic
5. **Create `ICurrentUserService`** for claim access in handlers
6. **Move signing key** to user secrets or Key Vault

## References

- https://learn.microsoft.com/en-us/aspnet/core/security/authentication/jwt
- https://datatracker.ietf.org/doc/html/rfc7519
