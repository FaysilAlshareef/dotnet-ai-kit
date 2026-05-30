using DotnetAiKit.Core.Values;

namespace DotnetAiKit.Core.Project;

/// <summary>Detected per-project path map (e.g. entities, aggregates, endpoints).</summary>
public sealed record DetectedPaths
{
    public IReadOnlyDictionary<string, string> Paths { get; init; } =
        new Dictionary<string, string>(StringComparer.Ordinal);

    public string? Get(string key) => Paths.TryGetValue(key, out var v) ? v : null;
}

/// <summary>Detected project metadata — the substitution source.</summary>
public sealed record ProjectMetadata
{
    public string Company { get; init; } = string.Empty;
    public string Domain { get; init; } = string.Empty;
    public string Architecture { get; init; } = string.Empty;
    public string DotnetVersion { get; init; } = string.Empty;
    public DetectedPaths DetectedPaths { get; init; } = new();

    /// <summary>Flatten to the substitution dictionary (<c>${Company}</c>, <c>${detected_paths.x}</c>).</summary>
    public IReadOnlyDictionary<string, string> ToTokenMap()
    {
        var map = new Dictionary<string, string>(StringComparer.Ordinal)
        {
            ["Company"] = Company,
            ["Domain"] = Domain,
            ["Architecture"] = Architecture,
            ["DotnetVersion"] = DotnetVersion,
        };
        foreach (var (k, v) in DetectedPaths.Paths)
            map[$"detected_paths.{k}"] = v;
        return map;
    }
}

/// <summary>The user-owned config.yml contract (honors the ai_tools → enabled_hosts legacy alias on read).</summary>
public sealed record UserConfig
{
    public IReadOnlyList<HostName> EnabledHosts { get; init; } = [];
    public string PermissionProfile { get; init; } = "standard";
    public int Retention { get; init; } = 3;
    public SemVer PluginVersion { get; init; } = new(2, 0, 0);
}
