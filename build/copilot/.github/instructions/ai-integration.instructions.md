---
applyTo: "**/*.cs"
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
