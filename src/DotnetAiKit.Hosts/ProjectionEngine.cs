using DotnetAiKit.Application.Ports;
using DotnetAiKit.Core.Artifacts;
using DotnetAiKit.Core.Values;

namespace DotnetAiKit.Hosts;

/// <summary>Maps a <see cref="HostName"/> to its projector (replaces keyed DI; AOT-safe).</summary>
public sealed class HostRegistry
{
    private readonly Dictionary<HostName, IHostProjector> _projectors;

    public HostRegistry(IEnumerable<IHostProjector> projectors) =>
        _projectors = projectors.ToDictionary(p => p.Host);

    public IReadOnlyCollection<IHostProjector> Projectors => _projectors.Values;

    public IHostProjector? Get(HostName host) => _projectors.GetValueOrDefault(host);
}

/// <summary>Drives every registered host projector over the corpus, producing a deterministic file set.</summary>
public sealed class ProjectionEngine(HostRegistry registry) : IProjectionEngine
{
    public IReadOnlyList<ProjectedFile> ProjectAll(ArtifactCorpus corpus)
    {
        var files = new List<ProjectedFile>();
        foreach (var projector in registry.Projectors.OrderBy(p => p.Host))
            files.AddRange(projector.Project(corpus));

        if (corpus.Manifest is { } manifest)
            files.Add(MarketplaceWriter.Write(manifest));

        files.Sort((a, b) => string.CompareOrdinal(a.RelativePath, b.RelativePath));
        return files;
    }
}
