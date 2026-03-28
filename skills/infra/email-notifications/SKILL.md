---
name: email-notifications
description: >
  Email service abstraction with template rendering. Covers IEmailService interface,
  SendGrid/SES integration, HTML templates, and queue-based sending.
  Trigger: email, notification, SendGrid, SES, template, SMTP.
metadata:
  category: infra
  agent: dotnet-architect
---

# Email Notifications — Service Abstraction & Templates

## Core Principles

- `IEmailService` abstracts email sending from provider implementation
- Support multiple providers: SendGrid, AWS SES, SMTP
- HTML templates with placeholder replacement
- Queue-based sending for reliability (fire-and-forget from handlers)
- Structured email models with strong typing

## Key Patterns

### Email Service Interface

```csharp
namespace {Company}.{Domain}.Application.Interfaces;

public interface IEmailService
{
    Task SendAsync(EmailMessage message, CancellationToken ct = default);
    Task SendTemplatedAsync(string templateName, object model,
        string toEmail, string? toName = null, CancellationToken ct = default);
}

public sealed record EmailMessage(
    string ToEmail,
    string ToName,
    string Subject,
    string HtmlBody,
    string? PlainTextBody = null);
```

### SendGrid Implementation

```csharp
namespace {Company}.{Domain}.Infrastructure.Email;

public sealed class SendGridEmailService(
    IOptions<EmailOptions> options,
    ILogger<SendGridEmailService> logger) : IEmailService
{
    private readonly SendGridClient _client = new(options.Value.ApiKey);

    public async Task SendAsync(EmailMessage message, CancellationToken ct)
    {
        var msg = new SendGridMessage
        {
            From = new EmailAddress(options.Value.FromEmail, options.Value.FromName),
            Subject = message.Subject,
            HtmlContent = message.HtmlBody,
            PlainTextContent = message.PlainTextBody
        };
        msg.AddTo(new EmailAddress(message.ToEmail, message.ToName));

        var response = await _client.SendEmailAsync(msg, ct);

        if (!response.IsSuccessStatusCode)
        {
            var body = await response.Body.ReadAsStringAsync(ct);
            logger.LogError("SendGrid error: {Status} {Body}",
                response.StatusCode, body);
        }
    }

    public async Task SendTemplatedAsync(string templateName, object model,
        string toEmail, string? toName, CancellationToken ct)
    {
        var template = await LoadTemplateAsync(templateName);
        var html = RenderTemplate(template, model);
        var subject = ExtractSubject(template, model);

        await SendAsync(new EmailMessage(toEmail, toName ?? "", subject, html), ct);
    }

    private static string RenderTemplate(string template, object model)
    {
        var result = template;
        foreach (var prop in model.GetType().GetProperties())
        {
            var value = prop.GetValue(model)?.ToString() ?? "";
            result = result.Replace($"{{{{{prop.Name}}}}}", value);
        }
        return result;
    }
}
```

### Email Options

```csharp
public sealed class EmailOptions
{
    public const string SectionName = "Email";

    [Required]
    public string Provider { get; init; } = "SendGrid"; // SendGrid, SES, SMTP

    [Required]
    public string ApiKey { get; init; } = string.Empty;

    [Required, EmailAddress]
    public string FromEmail { get; init; } = string.Empty;

    public string FromName { get; init; } = "{Company}";
}
```

### Template Files

```
templates/
  order-confirmation.html
  welcome.html
  password-reset.html
```

```html
<!-- templates/order-confirmation.html -->
<html>
<body>
  <h1>Order Confirmation</h1>
  <p>Dear {{CustomerName}},</p>
  <p>Your order #{{OrderNumber}} has been confirmed.</p>
  <p>Total: {{Total}}</p>
</body>
</html>
```

### Registration

```csharp
services.AddOptions<EmailOptions>()
    .BindConfiguration(EmailOptions.SectionName)
    .ValidateDataAnnotations()
    .ValidateOnStart();

services.AddScoped<IEmailService, SendGridEmailService>();
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Direct SendGrid calls in handlers | Use IEmailService abstraction |
| Synchronous email sending in request | Fire-and-forget via background job |
| Hardcoded email content | Use HTML templates with placeholders |
| Missing error handling | Log failures, don't throw to caller |

## Detect Existing Patterns

```bash
# Find email service
grep -r "IEmailService\|EmailService" --include="*.cs" src/

# Find SendGrid/SES
grep -r "SendGrid\|SES\|SmtpClient" --include="*.cs" src/

# Find email templates
find . -name "*.html" -path "*/templates/*"
```

## Adding to Existing Project

1. **Check for existing `IEmailService`** — extend, don't replace
2. **Use the configured provider** from EmailOptions
3. **Add new templates** in the templates directory
4. **Queue emails** via Hangfire or BackgroundJob for reliability
5. **Test with a sandbox** — SendGrid has sandbox mode for testing
