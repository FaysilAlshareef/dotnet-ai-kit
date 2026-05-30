using DotnetAiKit.Core.Values;

namespace DotnetAiKit.Core.Frontmatter;

/// <summary>A host-specific extension block (the <c>x-&lt;host&gt;</c> stanza), stripped/translated at projection.</summary>
public sealed record HostExtensionBlock
{
    public required HostName Host { get; init; }

    /// <summary>Arbitrary host-specific fields (e.g. cursor <c>alwaysApply</c>). Known structured fields
    /// (paths, invocation) are first-class on the artifact; this holds the remainder.</summary>
    public IReadOnlyDictionary<string, string> Fields { get; init; } =
        new Dictionary<string, string>(StringComparer.Ordinal);

    public string? Get(string key) => Fields.TryGetValue(key, out var v) ? v : null;
}

/// <summary>Portable core frontmatter fields plus per-host extension blocks.</summary>
public sealed record ArtifactFrontmatter
{
    public required ArtifactName Name { get; init; }
    public required Description Description { get; init; }
    public string? License { get; init; }
    public string? Compatibility { get; init; }
    public SemVer SchemaVersion { get; init; } = new(1, 0, 0);

    public IReadOnlyDictionary<string, string> Metadata { get; init; } =
        new Dictionary<string, string>(StringComparer.Ordinal);

    public IReadOnlyList<HostExtensionBlock> HostExtensions { get; init; } = [];

    public HostExtensionBlock? ForHost(HostName host) =>
        HostExtensions.FirstOrDefault(b => b.Host == host);

    public string? MetadataValue(string key) =>
        Metadata.TryGetValue(key, out var v) ? v : null;
}
