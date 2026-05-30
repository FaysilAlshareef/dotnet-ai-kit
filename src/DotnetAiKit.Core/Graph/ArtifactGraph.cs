using DotnetAiKit.Core.Values;

namespace DotnetAiKit.Core.Graph;

/// <summary>A node in the artifact graph.</summary>
public sealed record ArtifactNode(ArtifactName Id, ArtifactKind Kind);

/// <summary>A directed edge between two artifacts.</summary>
public sealed record ArtifactEdge(ArtifactName From, ArtifactName To, EdgeKind Kind);

/// <summary>The outcome of building a graph: the graph, or the list of broken edges.</summary>
public sealed record GraphBuildResult(ArtifactGraph? Graph, IReadOnlyList<string> BrokenEdges)
{
    public bool Ok => BrokenEdges.Count == 0;
}

/// <summary>
/// The artifact knowledge graph (nodes = artifacts, edges = owns/relates/triggers/enforced-by).
/// Built from frontmatter, never hand-authored. A reference to a non-existent artifact is a broken
/// edge and fails the build (FR-006).
/// </summary>
public sealed class ArtifactGraph
{
    private readonly Dictionary<ArtifactName, ArtifactNode> _nodes;
    private readonly List<ArtifactEdge> _edges;

    private ArtifactGraph(Dictionary<ArtifactName, ArtifactNode> nodes, List<ArtifactEdge> edges)
    {
        _nodes = nodes;
        _edges = edges;
    }

    public IReadOnlyCollection<ArtifactNode> Nodes => _nodes.Values;
    public IReadOnlyList<ArtifactEdge> Edges => _edges;

    public static GraphBuildResult Build(IEnumerable<ArtifactNode> nodes, IEnumerable<ArtifactEdge> edges)
    {
        var nodeMap = new Dictionary<ArtifactName, ArtifactNode>();
        foreach (var n in nodes)
            nodeMap[n.Id] = n;

        var edgeList = edges.ToList();
        var broken = new List<string>();
        foreach (var e in edgeList)
        {
            if (!nodeMap.ContainsKey(e.From))
                broken.Add($"Edge {e.Kind} from unknown artifact '{e.From}' -> '{e.To}'.");
            if (!nodeMap.ContainsKey(e.To))
                broken.Add($"Edge {e.Kind} '{e.From}' -> references unknown artifact '{e.To}'.");
        }

        return broken.Count > 0
            ? new GraphBuildResult(null, broken)
            : new GraphBuildResult(new ArtifactGraph(nodeMap, edgeList), []);
    }

    /// <summary>Outgoing neighbors of a node, optionally filtered by edge kind (disambiguation/see-also).</summary>
    public IEnumerable<ArtifactName> Neighbors(ArtifactName from, EdgeKind? kind = null) =>
        _edges.Where(e => e.From == from && (kind is null || e.Kind == kind)).Select(e => e.To);
}
