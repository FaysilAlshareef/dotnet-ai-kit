---
name: extensions-ai-chat
description: "Wires Microsoft.Extensions.AI IChatClient behind a provider abstraction with a middleware pipeline — DI registration, automatic tool/function invocation, OpenTelemetry, and distributed caching. Use when adding chat/completions or tool-using LLM features to a .NET app. Do NOT use for embeddings, vector stores, or semantic search (use extensions-ai-embeddings)."
metadata:
  category: "ai"
  agent: "ai-engineer"
---
# Extensions.AI Chat Client

`Microsoft.Extensions.AI` (GA 10.6.0) gives one `IChatClient` abstraction over every provider. Compose cross-cutting behaviour as middleware with `ChatClientBuilder`, so caching/telemetry/tool-calling are added once and the app code never sees the concrete provider.

## Conventions
- Depend on `IChatClient` only; never reference a provider type in application code. Swap providers in DI without touching callers.
- Default to a local/OSS provider for dev (e.g. Ollama via `Microsoft.Extensions.AI.Ollama`); treat hosted providers (Azure OpenAI, OpenAI) as opt-in config — license-light by default.
- Build the pipeline with `ChatClientBuilder`: `.UseFunctionInvocation()` for tool calling, `.UseOpenTelemetry()` for traces/metrics, `.UseDistributedCache()` to cache identical requests.
- Order matters — cache outermost (skips the model on a hit), telemetry around the call, function-invocation innermost (it re-calls the model per tool round-trip).
- Expose tools as plain C# methods wrapped with `AIFunctionFactory.Create(...)` and pass them in `ChatOptions.Tools`; the pipeline runs the tool loop automatically.
- Always thread `CancellationToken`; prefer `GetStreamingResponseAsync` for UI-facing chat.

## Example
```csharp
// Program.cs — provider chosen here, hidden from the rest of the app
builder.Services.AddDistributedMemoryCache();
builder.Services.AddChatClient(sp =>
    new OllamaChatClient(new Uri("http://localhost:11434"), "llama3.1")) // OSS default
        // .Use(new AzureOpenAIClient(...).AsChatClient("gpt-4o"))       // opt-in
    .UseDistributedCache()
    .UseOpenTelemetry()
    .UseFunctionInvocation();

// A use-case depends only on IChatClient
public sealed class SupportAssistant(IChatClient chat)
{
    private readonly ChatOptions _options = new()
    {
        Tools = [AIFunctionFactory.Create(LookupOrder)]
    };

    public Task<ChatResponse> AskAsync(string prompt, CancellationToken ct) =>
        chat.GetResponseAsync(prompt, _options, ct);

    [Description("Look up an order's status by id")]
    private static string LookupOrder(string orderId) => /* ... */ "Shipped";
}
```

## Anti-Patterns
- Referencing `AzureOpenAIClient`/`OpenAIClient` outside the DI registration.
- Hand-rolling the tool-call loop instead of `.UseFunctionInvocation()`.
- Caching after function-invocation (caches tool-loop intermediates, not the final answer).
- Defaulting to a paid provider when local Ollama covers development.

## References
- https://learn.microsoft.com/en-us/dotnet/ai/microsoft-extensions-ai
