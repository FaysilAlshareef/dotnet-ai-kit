using System.Text;
using DotnetAiKit.Application.Ports;
using DotnetAiKit.Core.Artifacts;
using DotnetAiKit.Core.Values;

namespace DotnetAiKit.Hosts.Claude;

/// <summary>
/// Projects the corpus into Claude Code's native shape: markdown skills (commands merged into skills),
/// agents, path-scoped rules, and the plugin manifest. Emits only Claude-understood frontmatter fields;
/// per-host <c>x-*</c> blocks are dropped. Deterministic ordering + fixed LF newline.
/// </summary>
public sealed class ClaudeProjector : IHostProjector
{
    public HostName Host => HostName.Claude;

    public IEnumerable<ProjectedFile> Project(ArtifactCorpus corpus)
    {
        foreach (var skill in corpus.Skills)
        {
            yield return ProjectSkill(skill);
            foreach (var resource in SkillResourceProjection.Emit(skill, "claude/skills"))
                yield return resource;
        }

        foreach (var agent in corpus.Agents)
            yield return ProjectAgent(agent);
        foreach (var rule in corpus.Rules)
            yield return ProjectRule(rule);
        if (corpus.Manifest is { } manifest)
            yield return ClaudeManifestWriter.Write(manifest);

        // Claude-scoped enforcement hooks (planning/24 T1/T2/T4): PreToolUse injection/deny + Stop gate.
        yield return ClaudeHooksWriter.Write();

        // Forced output-style channel (AR-10 / FR-022-16): always-on conventions while the plugin is enabled.
        yield return ClaudeOutputStyleWriter.Write();
    }

    private static ProjectedFile ProjectSkill(Skill skill)
    {
        var fm = new FrontmatterBuilder()
            .Add("name", skill.Name.Value)
            .AddQuoted("description", skill.Description.Value)
            .AddList("paths", skill.Paths.Select(p => p.Value))
            .AddFlag("disable-model-invocation", skill.Invocation == InvocationPolicy.DisableModelInvocation ? true : (bool?)null)
            .AddFlag("user-invocable", skill.Invocation == InvocationPolicy.UserInvocableFalse ? false : (bool?)null);

        return new ProjectedFile($"claude/skills/{skill.Name.Value}/SKILL.md", fm.Compose(skill.Body));
    }

    private static ProjectedFile ProjectAgent(Agent agent)
    {
        var fm = new FrontmatterBuilder()
            .Add("name", agent.Name.Value)
            .AddQuoted("description", agent.Description.Value)
            .AddList("skills", agent.ReferencedSkills.Select(s => s.Value));

        return new ProjectedFile($"claude/agents/{agent.Name.Value}.md", fm.Compose(agent.Body));
    }

    private static ProjectedFile ProjectRule(Rule rule)
    {
        var fm = new FrontmatterBuilder()
            .Add("name", rule.Name.Value)
            .AddQuoted("description", rule.Description.Value)
            .AddList("paths", rule.Paths.Select(p => p.Value));

        return new ProjectedFile($"claude/rules/{rule.Name.Value}.md", fm.Compose(rule.Body));
    }

    /// <summary>Builds deterministic YAML frontmatter (fixed field order, LF, double-quoted scalars).</summary>
    private sealed class FrontmatterBuilder
    {
        private readonly StringBuilder _sb = new();

        public FrontmatterBuilder Add(string key, string value)
        {
            _sb.Append(key).Append(": ").Append(value).Append('\n');
            return this;
        }

        public FrontmatterBuilder AddQuoted(string key, string value)
        {
            _sb.Append(key).Append(": ").Append(Quote(value)).Append('\n');
            return this;
        }

        public FrontmatterBuilder AddList(string key, IEnumerable<string> values)
        {
            var list = values.ToList();
            if (list.Count == 0)
                return this;
            _sb.Append(key).Append(":\n");
            foreach (var v in list)
                _sb.Append("  - ").Append(Quote(v)).Append('\n');
            return this;
        }

        public FrontmatterBuilder AddFlag(string key, bool? value)
        {
            if (value is { } b)
                _sb.Append(key).Append(": ").Append(b ? "true" : "false").Append('\n');
            return this;
        }

        public string Compose(string body)
        {
            var sb = new StringBuilder();
            sb.Append("---\n").Append(_sb).Append("---\n");
            sb.Append(body);
            if (body.Length == 0 || body[^1] != '\n')
                sb.Append('\n');
            return sb.ToString();
        }

        private static string Quote(string value) =>
            "\"" + value.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"";
    }
}
