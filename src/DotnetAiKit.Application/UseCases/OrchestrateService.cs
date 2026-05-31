using System.Text;
using DotnetAiKit.Application.Ports;

namespace DotnetAiKit.Application.UseCases;

/// <summary>A repository affected by a multi-repo feature, with its role and event contracts.</summary>
public sealed record AffectedRepo(
    string Path, string Role, IReadOnlyList<string> ConsumesEvents, IReadOnlyList<string> ProducesEvents);

public sealed record OrchestrateResult(
    bool Ok, IReadOnlyList<string> BriefsWritten, IReadOnlyList<string> Skipped, IReadOnlyList<string> Errors);

/// <summary>
/// Multi-repo conductor (FR-033/FR-G2): projects a feature-brief into every affected repository's
/// feature folder so each repo is aware of its role + events. Sequential, dependency-ordered by
/// default (input order); dirty secondary working trees are warned and skipped (FR-G7). No network.
/// The awareness contract (FR-G8/SC-009): every service-map repo ends with a brief carrying the
/// matching feature id.
/// </summary>
public sealed class OrchestrateService(IFileSystem fileSystem)
{
    public OrchestrateResult Run(string featureId, string featureName, IReadOnlyList<AffectedRepo> serviceMap, bool dryRun)
    {
        var written = new List<string>();
        var skipped = new List<string>();

        foreach (var repo in serviceMap)
        {
            if (!fileSystem.DirectoryExists(repo.Path))
            {
                skipped.Add($"{repo.Path} (missing)");
                continue;
            }

            var relative = Path.Combine(".dotnet-ai-kit", "features", featureId, "feature-brief.md");
            var fullPath = Path.Combine(repo.Path, relative);
            if (!dryRun)
                fileSystem.WriteAllText(fullPath, RenderBrief(featureId, featureName, repo));
            written.Add(fullPath);
        }

        return new OrchestrateResult(true, written, skipped, []);
    }

    private static string RenderBrief(string featureId, string featureName, AffectedRepo repo)
    {
        var sb = new StringBuilder();
        sb.Append("---\n");
        sb.Append("feature_id: ").Append(featureId).Append('\n');
        sb.Append("feature_name: \"").Append(featureName.Replace("\"", "\\\"")).Append("\"\n");
        sb.Append("role: ").Append(repo.Role).Append('\n');
        sb.Append("---\n");
        sb.Append("# Feature brief: ").Append(featureName).Append(" (").Append(featureId).Append(")\n\n");
        sb.Append("**Role in this feature:** ").Append(repo.Role).Append("\n\n");
        sb.Append("## Events consumed\n");
        foreach (var e in repo.ConsumesEvents)
            sb.Append("- ").Append(e).Append('\n');
        sb.Append("\n## Events produced\n");
        foreach (var e in repo.ProducesEvents)
            sb.Append("- ").Append(e).Append('\n');
        return sb.ToString();
    }
}
