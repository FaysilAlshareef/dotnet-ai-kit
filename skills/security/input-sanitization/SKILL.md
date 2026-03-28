---
name: input-sanitization
description: >
  Input sanitization and XSS prevention — HTML sanitization, CSP headers,
  output encoding, security headers middleware, and file upload validation.
  Trigger: XSS, sanitize, sanitization, CSP, Content-Security-Policy, HtmlSanitizer, security headers.
metadata:
  category: security
  agent: api-designer
---

# Input Sanitization & XSS Prevention

## Core Principles

- **Never trust input** — all data crossing a trust boundary (query strings, headers, form fields, file uploads, third-party APIs) is potentially hostile
- **Encode output** — context-aware encoding at the point of rendering is the primary XSS defense
- **Defense in depth** — combine input validation, output encoding, CSP headers, and security headers; no single layer is sufficient
- **Prefer rejection over cleaning** — validate first; only sanitize when you must accept rich content (e.g., user-authored HTML)
- **Fail closed** — if validation is ambiguous, reject the input rather than attempting to guess intent

## When to Use

- Accepting user-generated HTML (comments, rich-text editors, CMS content)
- Rendering dynamic content in Razor views, Blazor components, or API responses consumed by browsers
- Serving any web application that needs baseline security headers
- Accepting file uploads from untrusted users
- Building APIs consumed by SPAs or third-party clients

## When NOT to Use

- Internal service-to-service communication behind a trusted network boundary (still validate schemas, but XSS is not the threat model)
- CLI tools or background workers that never render output in a browser context
- Static file servers with no dynamic content

## Patterns

### HTML Sanitization

Use the `HtmlSanitizer` NuGet package when you must accept rich HTML input (e.g., blog posts, comments). Never write your own regex-based sanitizer.

```bash
dotnet add package HtmlSanitizer
```

```csharp
using Ganss.Xss;

public interface IContentSanitizer
{
    string Sanitize(string untrustedHtml);
}

public sealed class ContentSanitizer : IContentSanitizer
{
    private readonly HtmlSanitizer _sanitizer;

    public ContentSanitizer()
    {
        _sanitizer = new HtmlSanitizer();

        // Explicitly allow only safe tags
        _sanitizer.AllowedTags.Clear();
        _sanitizer.AllowedTags.Add("p");
        _sanitizer.AllowedTags.Add("br");
        _sanitizer.AllowedTags.Add("strong");
        _sanitizer.AllowedTags.Add("em");
        _sanitizer.AllowedTags.Add("ul");
        _sanitizer.AllowedTags.Add("ol");
        _sanitizer.AllowedTags.Add("li");
        _sanitizer.AllowedTags.Add("a");
        _sanitizer.AllowedTags.Add("code");
        _sanitizer.AllowedTags.Add("pre");
        _sanitizer.AllowedTags.Add("blockquote");

        // Restrict attributes
        _sanitizer.AllowedAttributes.Clear();
        _sanitizer.AllowedAttributes.Add("href");
        _sanitizer.AllowedAttributes.Add("class");

        // Only allow safe URI schemes
        _sanitizer.AllowedSchemes.Clear();
        _sanitizer.AllowedSchemes.Add("https");
        _sanitizer.AllowedSchemes.Add("mailto");
    }

    public string Sanitize(string untrustedHtml)
        => _sanitizer.Sanitize(untrustedHtml);
}

// Registration
builder.Services.AddSingleton<IContentSanitizer, ContentSanitizer>();
```

### Output Encoding

Razor auto-encodes `@` expressions — the danger is bypassing it.

```csharp
// SAFE — Razor auto-encodes this
<p>@Model.UserComment</p>

// DANGEROUS — renders raw HTML, enabling XSS
<p>@Html.Raw(Model.UserComment)</p>

// SAFE — only use Html.Raw with pre-sanitized content
<p>@Html.Raw(Model.SanitizedComment)</p>
```

For manual encoding in services or APIs:

```csharp
using System.Text.Encodings.Web;

public sealed class NotificationService(HtmlEncoder htmlEncoder)
{
    public string BuildSafeHtml(string userName, string message)
    {
        var safeName = htmlEncoder.Encode(userName);
        var safeMessage = htmlEncoder.Encode(message);
        return $"<p><strong>{safeName}</strong>: {safeMessage}</p>";
    }
}

// For JavaScript contexts
var jsEncoder = JavaScriptEncoder.Default;
var safeValue = jsEncoder.Encode(userInput);

// For URL contexts
var urlEncoder = UrlEncoder.Default;
var safeParam = urlEncoder.Encode(userInput);
```

### CSP Headers

Content-Security-Policy is the strongest browser-side XSS mitigation. Start strict, loosen only when needed.

```csharp
// Program.cs — Middleware approach
app.Use(async (context, next) =>
{
    context.Response.Headers.Append(
        "Content-Security-Policy",
        "default-src 'self'; " +
        "script-src 'self'; " +
        "style-src 'self'; " +
        "img-src 'self' data: https:; " +
        "font-src 'self'; " +
        "connect-src 'self'; " +
        "frame-ancestors 'none'; " +
        "base-uri 'self'; " +
        "form-action 'self'");

    await next();
});
```

For pages that require inline scripts, use nonce-based CSP:

```csharp
public sealed class CspNonceMiddleware(RequestDelegate next)
{
    public async Task InvokeAsync(HttpContext context)
    {
        var nonce = Convert.ToBase64String(
            RandomNumberGenerator.GetBytes(16));

        context.Items["CspNonce"] = nonce;

        context.Response.Headers.Append(
            "Content-Security-Policy",
            $"default-src 'self'; " +
            $"script-src 'self' 'nonce-{nonce}'; " +
            $"style-src 'self' 'nonce-{nonce}'; " +
            $"img-src 'self' data: https:; " +
            $"frame-ancestors 'none'; " +
            $"base-uri 'self'");

        await next(context);
    }
}

// In Razor views
<script nonce="@Context.Items["CspNonce"]">
    // Inline script allowed by nonce
</script>

// Registration
app.UseMiddleware<CspNonceMiddleware>();
```

### Security Headers Middleware

Add all recommended security headers in a single middleware:

```csharp
public sealed class SecurityHeadersMiddleware(RequestDelegate next)
{
    public async Task InvokeAsync(HttpContext context)
    {
        var headers = context.Response.Headers;

        // Prevent MIME-type sniffing
        headers.Append("X-Content-Type-Options", "nosniff");

        // Prevent clickjacking
        headers.Append("X-Frame-Options", "DENY");

        // Legacy XSS filter — set to 0 to avoid
        // false positives in older browsers
        headers.Append("X-XSS-Protection", "0");

        // Control referrer information leakage
        headers.Append("Referrer-Policy",
            "strict-origin-when-cross-origin");

        // Enforce HTTPS
        headers.Append("Strict-Transport-Security",
            "max-age=31536000; includeSubDomains");

        // Restrict browser features
        headers.Append("Permissions-Policy",
            "camera=(), microphone=(), geolocation=()");

        await next(context);
    }
}

// Registration — place before other middleware
app.UseMiddleware<SecurityHeadersMiddleware>();
```

### File Upload Validation

Never trust the file extension or Content-Type header alone. Validate magic bytes, enforce size limits, and store outside the web root.

```csharp
public sealed class FileUploadValidator
{
    private static readonly Dictionary<string, byte[]> MagicBytes = new()
    {
        [".png"] = [0x89, 0x50, 0x4E, 0x47],
        [".jpg"] = [0xFF, 0xD8, 0xFF],
        [".gif"] = [0x47, 0x49, 0x46, 0x38],
        [".pdf"] = [0x25, 0x50, 0x44, 0x46],
    };

    private static readonly HashSet<string> AllowedExtensions =
        [".png", ".jpg", ".jpeg", ".gif", ".pdf"];

    private const long MaxFileSizeBytes = 10 * 1024 * 1024; // 10 MB

    public Result Validate(IFormFile file)
    {
        // Check size
        if (file.Length == 0)
            return Result.Failure("File is empty.");
        if (file.Length > MaxFileSizeBytes)
            return Result.Failure(
                $"File exceeds {MaxFileSizeBytes / 1024 / 1024} MB limit.");

        // Check extension (case-insensitive)
        var extension = Path.GetExtension(file.FileName)
            .ToLowerInvariant();
        if (!AllowedExtensions.Contains(extension))
            return Result.Failure(
                $"Extension '{extension}' is not allowed.");

        // Verify magic bytes match claimed extension
        if (MagicBytes.TryGetValue(
            extension == ".jpeg" ? ".jpg" : extension,
            out var expected))
        {
            using var stream = file.OpenReadStream();
            var header = new byte[expected.Length];
            if (stream.Read(header, 0, header.Length) < header.Length
                || !header.AsSpan().StartsWith(expected))
            {
                return Result.Failure(
                    "File content does not match its extension.");
            }
        }

        return Result.Success();
    }
}
```

### Input Validation vs Sanitization

Choose the right strategy based on the data type:

```csharp
// VALIDATION — reject bad input (preferred for structured data)
public sealed class CreateUserRequestValidator
    : AbstractValidator<CreateUserRequest>
{
    public CreateUserRequestValidator()
    {
        RuleFor(x => x.Email).NotEmpty().EmailAddress().MaximumLength(256);
        RuleFor(x => x.DisplayName).NotEmpty().MaximumLength(100)
            .Matches(@"^[\w\s\-'.]+$")
            .WithMessage("Display name contains invalid characters.");
    }
}

// SANITIZATION — clean but accept (for rich content)
public string ProcessComment(string rawHtml)
{
    if (rawHtml.Length > 50_000)
        throw new ValidationException("Comment too long.");
    return _contentSanitizer.Sanitize(rawHtml);
}
```

| Data Type | Strategy | Rationale |
|-----------|----------|-----------|
| Email, phone, ID | **Validate** and reject | Structured format — any deviation is invalid |
| Display name | **Validate** with pattern | No HTML needed — reject outside `[\w\s\-'.]` |
| Plain-text comment | **Validate** length, **encode** on output | No markup needed — encoding prevents XSS |
| Rich-text / HTML | **Validate** length, **sanitize** HTML | User needs formatting — allow safe subset |
| File upload | **Validate** extension, size, magic bytes | Binary content — cannot sanitize, must verify |

## Decision Guide

| Scenario | Primary Defense | Supporting Layers |
|----------|----------------|-------------------|
| Razor view rendering user data | Auto-encoding (`@`) | CSP, security headers |
| API returning HTML content | `HtmlSanitizer` | CSP on consuming SPA |
| SPA with user-generated content | CSP `script-src 'self'` | Output encoding in API |
| File uploads | Extension + magic byte validation | Size limits, antivirus scan |
| Form submissions | FluentValidation / DataAnnotations | Anti-forgery tokens |
| Rich-text editor | `HtmlSanitizer` with tag allowlist | CSP, output encoding |
| Inline scripts required | Nonce-based CSP | Security headers, SRI |
| Third-party scripts | `script-src` with hash or domain | Subresource Integrity (SRI) |

## Anti-Patterns

| Anti-Pattern | Problem | Correct Approach |
|--------------|---------|------------------|
| `@Html.Raw(userInput)` | Renders unescaped HTML — direct XSS | Sanitize first or use `@` auto-encoding |
| Regex-based HTML sanitizer | Impossible to cover all edge cases | Use `HtmlSanitizer` NuGet package |
| `Content-Security-Policy: unsafe-inline` | Defeats the purpose of CSP entirely | Use nonce-based or hash-based CSP |
| Checking only file extension | Attacker renames `.exe` to `.jpg` | Validate magic bytes and extension together |
| Trusting `Content-Type` header | Client controls this header | Check magic bytes server-side |
| Sanitizing on input, rendering raw | Data may be modified after sanitization | Encode/sanitize at the point of output |
| Blocklist approach (strip `<script>`) | Countless bypass vectors exist | Use allowlist of safe tags and attributes |
| No size limit on uploads | Denial of service via large files | Enforce `MaxFileSizeBytes` and `RequestSizeLimit` |
| Missing `X-Content-Type-Options` | Browser may MIME-sniff responses as HTML | Always send `nosniff` header |
| `X-XSS-Protection: 1; mode=block` | Can introduce side-channel attacks in older browsers | Set to `0` and rely on CSP instead |

## Detect Existing Patterns

1. Search for `Html.Raw` usage across Razor views — each occurrence needs review
2. Check `Program.cs` for `Content-Security-Policy` header or CSP middleware
3. Look for `HtmlSanitizer` NuGet in `.csproj` files
4. Search for `X-Content-Type-Options` to verify security headers are set
5. Look for `HtmlEncoder`, `JavaScriptEncoder`, or `UrlEncoder` usage

## Adding to Existing Project

1. **Add security headers middleware** — immediate win with no code changes elsewhere
2. **Audit `Html.Raw` calls** — replace with sanitized output or auto-encoding
3. **Add CSP header** — start with `Report-Only` mode, then enforce
4. **Install `HtmlSanitizer`** if the app accepts rich HTML content
5. **Add file upload validation** — extension allowlist, size limits, magic bytes
6. **Add input validation** with FluentValidation or DataAnnotations

## References

- https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
- https://learn.microsoft.com/en-us/aspnet/core/security/cross-site-scripting
- https://github.com/mganss/HtmlSanitizer
- https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP
