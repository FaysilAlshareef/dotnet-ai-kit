using System.Text;
using System.Text.Json;
using DotnetAiKit.Application.Ports;
using DotnetAiKit.Core.Artifacts;
using DotnetAiKit.Core.Values;

namespace DotnetAiKit.Hosts.Cursor;

/// <summary>
/// Projects to Cursor's shape: skills, <c>.mdc</c> rules (alwaysApply for universal, globs for domain),
/// command markdown, and <c>.cursor-plugin/plugin.json</c> (with an agents field).
/// </summary>
public sealed class CursorProjector : IHostProjector
{
    public HostName Host => HostName.Cursor;

    public IEnumerable<ProjectedFile> Project(ArtifactCorpus corpus)
    {
        foreach (var skill in corpus.Skills)
        {
            if (skill.SkillKind == SkillKind.Command)
                yield return new ProjectedFile(
                    $"cursor/commands/{skill.Name.Value}.md",
                    new FrontmatterWriter().Quoted("description", skill.Description.Value).Compose(skill.Body));
            else
            {
                yield return new ProjectedFile(
                    $"cursor/skills/{skill.Name.Value}/SKILL.md",
                    new FrontmatterWriter()
                        .Scalar("name", skill.Name.Value)
                        .Quoted("description", skill.Description.Value)
                        .Compose(skill.Body));
                foreach (var resource in SkillResourceProjection.Emit(skill, "cursor/skills"))
                    yield return resource;
            }
        }

        foreach (var rule in corpus.Rules)
            yield return ProjectRule(rule);

        if (corpus.Manifest is { } manifest)
            yield return ProjectManifest(manifest, corpus.Agents);
    }

    private static ProjectedFile ProjectRule(Rule rule)
    {
        var fm = new FrontmatterWriter().Quoted("description", rule.Description.Value);
        if (rule.Scope == RuleScope.Domain && rule.Paths.Count > 0)
            fm.Quoted("globs", string.Join(",", rule.Paths.Select(p => p.Value))).Flag("alwaysApply", false);
        else
            fm.Flag("alwaysApply", true);

        return new ProjectedFile($"cursor/rules/{rule.Name.Value}.mdc", fm.Compose(rule.Body));
    }

    private static ProjectedFile ProjectManifest(Core.Manifest.PluginManifest manifest, IReadOnlyList<Agent> agents)
    {
        var sb = new StringBuilder();
        sb.Append("{\n");
        sb.Append("  \"name\": ").Append(Json(manifest.Name)).Append(",\n");
        sb.Append("  \"version\": ").Append(Json(manifest.Version.ToString())).Append(",\n");
        sb.Append("  \"description\": ").Append(Json(manifest.Description)).Append(",\n");
        sb.Append("  \"agents\": ").Append(JsonArray(agents.Select(a => $"./agents/{a.Name.Value}.md").ToList())).Append('\n');
        sb.Append("}\n");
        return new ProjectedFile(".cursor-plugin/plugin.json", sb.ToString());
    }

    private static string Json(string value) => JsonSerializer.Serialize(value);

    private static string JsonArray(IReadOnlyList<string> values) =>
        values.Count == 0 ? "[]" : "[" + string.Join(", ", values.Select(Json)) + "]";
}
