---
name: dotnet-ai-file-storage
description: >
  File storage abstraction with Azure Blob Storage and local file system support.
  Covers IFileStorage interface, blob operations, and SAS token generation.
  Trigger: file storage, blob storage, Azure Blob, file upload, download.
category: infra
agent: dotnet-architect
---

# File Storage — Azure Blob & Local Abstraction

## Core Principles

- `IFileStorage` abstracts storage provider from application logic
- Support Azure Blob Storage (production) and local file system (development)
- SAS tokens for secure, time-limited file access
- Structured paths: `{container}/{entity-type}/{entity-id}/{filename}`
- Content type detection and validation
- Maximum file size enforcement

## Key Patterns

### File Storage Interface

```csharp
namespace {Company}.{Domain}.Application.Interfaces;

public interface IFileStorage
{
    Task<string> UploadAsync(string path, Stream content,
        string contentType, CancellationToken ct = default);
    Task<Stream> DownloadAsync(string path, CancellationToken ct = default);
    Task DeleteAsync(string path, CancellationToken ct = default);
    Task<bool> ExistsAsync(string path, CancellationToken ct = default);
    string GetPublicUrl(string path, TimeSpan? expiry = null);
}
```

### Azure Blob Storage Implementation

```csharp
namespace {Company}.{Domain}.Infrastructure.Storage;

public sealed class AzureBlobFileStorage(
    BlobServiceClient blobClient,
    IOptions<StorageOptions> options) : IFileStorage
{
    public async Task<string> UploadAsync(string path, Stream content,
        string contentType, CancellationToken ct)
    {
        var container = blobClient.GetBlobContainerClient(
            options.Value.ContainerName);
        await container.CreateIfNotExistsAsync(cancellationToken: ct);

        var blob = container.GetBlobClient(path);
        await blob.UploadAsync(content, new BlobHttpHeaders
        {
            ContentType = contentType
        }, cancellationToken: ct);

        return blob.Uri.ToString();
    }

    public async Task<Stream> DownloadAsync(string path, CancellationToken ct)
    {
        var container = blobClient.GetBlobContainerClient(
            options.Value.ContainerName);
        var blob = container.GetBlobClient(path);
        var response = await blob.DownloadStreamingAsync(cancellationToken: ct);
        return response.Value.Content;
    }

    public async Task DeleteAsync(string path, CancellationToken ct)
    {
        var container = blobClient.GetBlobContainerClient(
            options.Value.ContainerName);
        var blob = container.GetBlobClient(path);
        await blob.DeleteIfExistsAsync(cancellationToken: ct);
    }

    public async Task<bool> ExistsAsync(string path, CancellationToken ct)
    {
        var container = blobClient.GetBlobContainerClient(
            options.Value.ContainerName);
        var blob = container.GetBlobClient(path);
        return await blob.ExistsAsync(ct);
    }

    public string GetPublicUrl(string path, TimeSpan? expiry = null)
    {
        var container = blobClient.GetBlobContainerClient(
            options.Value.ContainerName);
        var blob = container.GetBlobClient(path);

        var sasBuilder = new BlobSasBuilder
        {
            BlobContainerName = options.Value.ContainerName,
            BlobName = path,
            Resource = "b",
            ExpiresOn = DateTimeOffset.UtcNow.Add(expiry ?? TimeSpan.FromHours(1))
        };
        sasBuilder.SetPermissions(BlobSasPermissions.Read);

        return blob.GenerateSasUri(sasBuilder).ToString();
    }
}
```

### Local File System Implementation (Development)

```csharp
namespace {Company}.{Domain}.Infrastructure.Storage;

public sealed class LocalFileStorage(
    IOptions<StorageOptions> options) : IFileStorage
{
    private string BasePath => options.Value.LocalBasePath
        ?? Path.Combine(Path.GetTempPath(), "file-storage");

    public async Task<string> UploadAsync(string path, Stream content,
        string contentType, CancellationToken ct)
    {
        var fullPath = Path.Combine(BasePath, path);
        Directory.CreateDirectory(Path.GetDirectoryName(fullPath)!);

        await using var fileStream = File.Create(fullPath);
        await content.CopyToAsync(fileStream, ct);
        return fullPath;
    }

    public Task<Stream> DownloadAsync(string path, CancellationToken ct)
    {
        var fullPath = Path.Combine(BasePath, path);
        return Task.FromResult<Stream>(File.OpenRead(fullPath));
    }

    public Task DeleteAsync(string path, CancellationToken ct)
    {
        var fullPath = Path.Combine(BasePath, path);
        if (File.Exists(fullPath)) File.Delete(fullPath);
        return Task.CompletedTask;
    }

    public Task<bool> ExistsAsync(string path, CancellationToken ct)
        => Task.FromResult(File.Exists(Path.Combine(BasePath, path)));

    public string GetPublicUrl(string path, TimeSpan? expiry = null)
        => Path.Combine(BasePath, path);
}
```

### Registration

```csharp
if (builder.Environment.IsDevelopment())
    services.AddSingleton<IFileStorage, LocalFileStorage>();
else
{
    services.AddSingleton(new BlobServiceClient(connectionString));
    services.AddSingleton<IFileStorage, AzureBlobFileStorage>();
}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Direct BlobClient in handlers | Use IFileStorage abstraction |
| No file size validation | Enforce limits before upload |
| Permanent public URLs | Use SAS tokens with expiry |
| No content type validation | Whitelist allowed content types |

## Detect Existing Patterns

```bash
# Find file storage interface
grep -r "IFileStorage\|IBlobStorage" --include="*.cs" src/

# Find Azure Blob usage
grep -r "BlobServiceClient\|BlobClient" --include="*.cs" src/

# Find storage configuration
grep -r "StorageOptions\|BlobStorage" --include="*.json" src/
```

## Adding to Existing Project

1. **Check for existing `IFileStorage`** interface
2. **Use the configured provider** based on environment
3. **Follow path conventions** for organized storage
4. **Validate file size and content type** before upload
5. **Use SAS tokens** for time-limited access URLs
