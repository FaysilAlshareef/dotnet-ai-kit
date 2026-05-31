---
name: ai-integration
description: "Guides Microsoft.Extensions.AI usage and provider/preview pinning for LLM features. Use when adding AI integration code (chat, embeddings, tool calling) in C# files. Do NOT use for general async correctness (use async-concurrency)."
metadata:
  paths: "**/*.cs"
---
# AI Integration (domain)

Standardize LLM integration on Microsoft.Extensions.AI behind a provider abstraction.

## MUST
- Use `IChatClient` / `IEmbeddingGenerator` behind a provider port; never bind app code to a single vendor SDK.
- Pin provider/preview package versions explicitly (the surface is moving).
- Route tool/function calling, caching, and telemetry through the middleware pipeline.
- Keep prompts/evals versioned alongside the code.

## MUST NOT
- Leak provider-specific types into domain/application layers.
- Depend on unpinned preview packages.
