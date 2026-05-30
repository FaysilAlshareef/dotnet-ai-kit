using System.Text;
using DotnetAiKit.Application.Ports;
using DotnetAiKit.Core.Artifacts;
using DotnetAiKit.Core.Policies;
using DotnetAiKit.Core.Project;
using DotnetAiKit.Core.Values;

namespace DotnetAiKit.Hosts.Claude;

/// <summary>
/// Writes Claude Code's per-solution footprint at <c>init</c> time: <c>.dotnet-ai-kit/*</c>,
/// <c>.claude/settings.json</c>, and — the v1 defect fix — <c>.claude/rules/*.md</c> with
/// <c>paths:</c> frontmatter so domain rules load JIT and universal rules are always-on (FR-019, SC-002).
/// </summary>
public sealed class ClaudeHostAdapter(IFileSystem fileSystem) : IHostAdapter
{
    public HostName Host => HostName.Claude;

    public HostWriteResult WritePerSolution(
        string solutionRoot, ArtifactCorpus corpus, ProjectMetadata metadata, bool dryRun)
    {
        var written = new List<string>();
        var tokens = metadata.ToTokenMap();

        void Write(string relativePath, string content)
        {
            if (!dryRun)
                fileSystem.WriteAllText(Path.Combine(solutionRoot, relativePath), content);
            written.Add(relativePath);
        }

        // The rule-delivery fix: domain rules carry paths: (JIT); universal rules are always-on.
        foreach (var rule in corpus.Rules)
            Write($".claude/rules/{rule.Name.Value}.md", RenderRule(rule, tokens));

        Write(".claude/settings.json", "{\n  \"$schema\": \"https://json.schemastore.org/claude-code-settings.json\"\n}\n");

        Write(".dotnet-ai-kit/version.txt", corpus.Manifest?.Version.ToString() ?? "2.0.0");
        Write(".dotnet-ai-kit/config.yml", RenderConfig(metadata));
        Write(".dotnet-ai-kit/project.yml", RenderProject(metadata));
        Write(".dotnet-ai-kit/manifest.json", "{\n  \"host\": \"claude\",\n  \"rules\": " + corpus.Rules.Count + "\n}\n");

        return new HostWriteResult { Written = written };
    }

    private static string RenderRule(Rule rule, IReadOnlyDictionary<string, string> tokens)
    {
        var sb = new StringBuilder();
        sb.Append("---\n");
        sb.Append("name: ").Append(rule.Name.Value).Append('\n');
        sb.Append("description: ").Append(Quote(rule.Description.Value)).Append('\n');
        if (rule.Scope == RuleScope.Domain && rule.Paths.Count > 0)
        {
            sb.Append("paths:\n");
            foreach (var glob in rule.Paths)
                sb.Append("  - ").Append(Quote(glob.Value)).Append('\n');
        }

        sb.Append("---\n");
        var body = SubstitutionEngine.Render(rule.Body, tokens);
        sb.Append(body);
        if (body.Length == 0 || body[^1] != '\n')
            sb.Append('\n');
        return sb.ToString();
    }

    private static string RenderConfig(ProjectMetadata metadata)
    {
        var sb = new StringBuilder();
        sb.Append("enabled_hosts:\n  - claude\n");
        sb.Append("permission_profile: standard\n");
        sb.Append("plugin_version: 2.0.0\n");
        return sb.ToString();
    }

    private static string RenderProject(ProjectMetadata metadata)
    {
        var sb = new StringBuilder();
        sb.Append("architecture: ").Append(metadata.Architecture.Length > 0 ? metadata.Architecture : "generic").Append('\n');
        sb.Append("dotnet_version: ").Append(Quote(metadata.DotnetVersion)).Append('\n');
        sb.Append("company: ").Append(Quote(metadata.Company)).Append('\n');
        return sb.ToString();
    }

    private static string Quote(string value) =>
        "\"" + value.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"";
}
