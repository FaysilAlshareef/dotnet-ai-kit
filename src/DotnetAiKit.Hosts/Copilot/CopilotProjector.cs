using System.Text;
using DotnetAiKit.Application.Ports;
using DotnetAiKit.Core.Artifacts;
using DotnetAiKit.Core.Values;

namespace DotnetAiKit.Hosts.Copilot;

/// <summary>
/// Projects to GitHub Copilot's render-only (cloud agent) shape under <c>copilot/.github/</c>:
/// path-scoped <c>*.instructions.md</c> (applyTo), aggregated <c>copilot-instructions.md</c> for
/// universal rules, <c>*.prompt.md</c> for commands, and <c>*.agent.md</c> for agents. The Copilot
/// CLI/VS Code path reuses <c>.claude-plugin/plugin.json</c>, so no separate manifest is emitted.
/// </summary>
public sealed class CopilotProjector : IHostProjector
{
    public HostName Host => HostName.Copilot;

    public IEnumerable<ProjectedFile> Project(ArtifactCorpus corpus)
    {
        foreach (var skill in corpus.Skills)
        {
            if (skill.SkillKind == SkillKind.Command)
                yield return new ProjectedFile(
                    $"copilot/.github/prompts/{skill.Name.Value}.prompt.md",
                    new FrontmatterWriter().Quoted("description", skill.Description.Value).Compose(skill.Body));
            else
                yield return new ProjectedFile(
                    $"copilot/skills/{skill.Name.Value}/SKILL.md",
                    new FrontmatterWriter()
                        .Scalar("name", skill.Name.Value)
                        .Quoted("description", skill.Description.Value)
                        .Compose(skill.Body));
        }

        foreach (var agent in corpus.Agents)
            yield return new ProjectedFile(
                $"copilot/.github/agents/{agent.Name.Value}.agent.md",
                new FrontmatterWriter().Quoted("description", agent.Description.Value).Compose(agent.Body));

        foreach (var rule in corpus.Rules.Where(r => r.Scope == RuleScope.Domain))
            yield return new ProjectedFile(
                $"copilot/.github/instructions/{rule.Name.Value}.instructions.md",
                new FrontmatterWriter()
                    .Quoted("applyTo", string.Join(",", rule.Paths.Select(p => p.Value)))
                    .Compose(rule.Body));

        var universal = corpus.Rules.Where(r => r.Scope == RuleScope.Universal).ToList();
        if (universal.Count > 0)
            yield return ProjectUniversalInstructions(universal);
    }

    private static ProjectedFile ProjectUniversalInstructions(IReadOnlyList<Rule> universalRules)
    {
        var sb = new StringBuilder();
        sb.Append("# Copilot Instructions\n\n");
        foreach (var rule in universalRules)
            sb.Append("## ").Append(rule.Name.Value).Append("\n\n").Append(rule.Body.TrimEnd('\n')).Append("\n\n");
        return new ProjectedFile("copilot/.github/copilot-instructions.md", sb.ToString());
    }
}
