using DotnetAiKit.Core.Values;

namespace DotnetAiKit.Core.Manifest;

/// <summary>Which artifacts the plugin exposes, by kind.</summary>
public sealed record ComponentMap
{
    public IReadOnlyList<ArtifactName> Skills { get; init; } = [];
    public IReadOnlyList<ArtifactName> Agents { get; init; } = [];
    public IReadOnlyList<ArtifactName> Rules { get; init; } = [];
    public IReadOnlyList<ArtifactName> Commands { get; init; } = [];
}

/// <summary>One row of the host capability matrix.</summary>
public sealed record CapabilityEntry(HostName Host, string Capability, CapabilityMaturity Maturity);

/// <summary>Machine-readable record of which host supports which capability at which maturity (FR-012).</summary>
public sealed record HostCapabilityMatrix
{
    public IReadOnlyList<CapabilityEntry> Entries { get; init; } = [];

    public CapabilityMaturity? Lookup(HostName host, string capability)
    {
        foreach (var e in Entries)
            if (e.Host == host && string.Equals(e.Capability, capability, StringComparison.OrdinalIgnoreCase))
                return e.Maturity;
        return null;
    }

    public bool Supports(HostName host, string capability)
    {
        var m = Lookup(host, capability);
        return m is CapabilityMaturity.Ga or CapabilityMaturity.Preview or CapabilityMaturity.Experimental;
    }
}

/// <summary>The single manifest descriptor → one per-host plugin manifest each.</summary>
public sealed record PluginManifest
{
    public required string Name { get; init; }
    public required SemVer Version { get; init; }
    public string Description { get; init; } = string.Empty;
    public IReadOnlyList<string> Keywords { get; init; } = [];
    public ComponentMap Components { get; init; } = new();
    public HostCapabilityMatrix Capabilities { get; init; } = new();
}
