---
name: extensions-ai-embeddings
description: "Generates vector embeddings with Microsoft.Extensions.AI IEmbeddingGenerator and stores/queries them in a vector store for RAG and semantic search. Use when building retrieval, similarity search, or grounding a chat feature with your own documents. Do NOT use for chat completions, tool calling, or the conversation pipeline (use extensions-ai-chat)."
metadata:
  category: "ai"
  agent: "ai-engineer"
---
# Extensions.AI Embeddings & Vector Store

`IEmbeddingGenerator<string, Embedding<float>>` (Microsoft.Extensions.AI GA 10.6.0) turns text into vectors behind a provider-agnostic abstraction. Pair it with a vector store to index documents once and retrieve the most relevant chunks at query time (RAG).

## Conventions
- Depend on `IEmbeddingGenerator<string, Embedding<float>>`; never reference a provider type in app code.
- Default to a local/OSS embedding model (e.g. Ollama `nomic-embed-text`); hosted models (Azure OpenAI / OpenAI) are opt-in config.
- Default vector store to OSS: in-memory (`Microsoft.Extensions.VectorData` + `Microsoft.SemanticKernel.Connectors.InMemory`) for dev, **pgvector** or **Qdrant** for persistence. Treat Azure AI Search as the cloud opt-in.
- Use the unified `Microsoft.Extensions.VectorData` abstractions (`VectorStoreCollection<TKey, TRecord>`) so the store is swappable like the generator.
- Chunk documents before embedding (a few hundred tokens with overlap); embed in batches via `GenerateAsync(IEnumerable<string>)` to cut round-trips.
- Keep the **same model** for indexing and querying — vectors from different models are not comparable. Store the source text + metadata on the record for grounding.

## Example
```csharp
// Provider + store registered once; callers see only the abstractions
builder.Services.AddEmbeddingGenerator(_ =>
    new OllamaEmbeddingGenerator(new Uri("http://localhost:11434"), "nomic-embed-text"));

public sealed record DocChunk
{
    [VectorStoreKey] public Guid Id { get; init; }
    [VectorStoreData] public string Text { get; init; } = "";
    [VectorStoreVector(768)] public ReadOnlyMemory<float> Vector { get; init; }
}

public sealed class DocSearch(
    IEmbeddingGenerator<string, Embedding<float>> embedder,
    VectorStoreCollection<Guid, DocChunk> store)
{
    public async Task<IReadOnlyList<DocChunk>> SearchAsync(
        string query, CancellationToken ct)
    {
        var q = await embedder.GenerateVectorAsync(query, cancellationToken: ct);
        var results = store.SearchAsync(q, top: 5, cancellationToken: ct);
        return await results.Select(r => r.Record).ToListAsync(ct);
    }
}
```

## Anti-Patterns
- Embedding the index with one model and queries with another.
- Storing only the vector and losing the source text needed to ground the answer.
- Embedding whole documents instead of chunks (poor recall, large vectors).
- Reaching for a managed vector DB when in-memory/pgvector covers the workload.

## References
- https://learn.microsoft.com/en-us/dotnet/ai/conceptual/embeddings
