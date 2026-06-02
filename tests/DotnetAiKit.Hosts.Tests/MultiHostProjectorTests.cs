using DotnetAiKit.Application.Ports;
using DotnetAiKit.Core.Artifacts;
using DotnetAiKit.Core.Frontmatter;
using DotnetAiKit.Core.Manifest;
using DotnetAiKit.Core.Values;
using DotnetAiKit.Hosts.Codex;
using DotnetAiKit.Hosts.Copilot;
using DotnetAiKit.Hosts.Cursor;
using Xunit;

namespace DotnetAiKit.Hosts.Tests;

public class MultiHostProjectorTests
{
    internal static ArtifactCorpus Sample()
    {
        const string skillDesc = "Generates endpoints. Use when adding routes. Do NOT use for MVC (use controller-patterns).";
        const string cmdDesc = "Creates a spec. Use when starting a feature. Do NOT use for planning (use plan).";
        const string agentDesc = "Leads architecture. Use when designing. Do NOT use for read models (use query-architect).";
        const string ruleDesc = "Handles errors. Use when adding error paths. Do NOT use for logging (use observability).";
        const string secDesc = "Secures code. Use when writing code. Do NOT use as review (use review).";

        return new ArtifactCorpus
        {
            Skills =
            [
                new Skill
                {
                    Name = ArtifactName.From("minimal-api-patterns"),
                    Description = Description.From(skillDesc),
                    Frontmatter = new ArtifactFrontmatter { Name = ArtifactName.From("minimal-api-patterns"), Description = Description.From(skillDesc) },
                    Body = "# skill\n",
                },
                new Skill
                {
                    Name = ArtifactName.From("specify"),
                    Description = Description.From(cmdDesc),
                    Frontmatter = new ArtifactFrontmatter { Name = ArtifactName.From("specify"), Description = Description.From(cmdDesc) },
                    Body = "# cmd\n",
                    SkillKind = SkillKind.Command,
                    Invocation = InvocationPolicy.DisableModelInvocation,
                },
            ],
            Agents =
            [
                new Agent
                {
                    Name = ArtifactName.From("dotnet-architect"),
                    Description = Description.From(agentDesc),
                    Body = "# agent\n",
                    ReferencedSkills = [ArtifactName.From("minimal-api-patterns")],
                },
            ],
            Rules =
            [
                new Rule { Name = ArtifactName.From("security"), Description = Description.From(secDesc), Body = "# sec\n", Scope = RuleScope.Universal },
                new Rule { Name = ArtifactName.From("error-handling"), Description = Description.From(ruleDesc), Body = "# err\n", Scope = RuleScope.Domain, Paths = [Glob.From("**/*.cs")] },
            ],
            Manifest = new PluginManifest { Name = "dotnet-ai-kit", Version = new SemVer(2, 0, 0), Description = "d", Keywords = ["dotnet"] },
        };
    }

    private static IReadOnlyDictionary<string, ProjectedFile> Project(IHostProjector projector) =>
        projector.Project(Sample()).ToDictionary(f => f.RelativePath);

    [Fact]
    public void Codex_emits_toml_agents_aggregated_conventions_and_manifest_without_agents()
    {
        var files = Project(new CodexProjector());

        Assert.Contains("skills = [\"minimal-api-patterns\"]", files["codex/agents/dotnet-architect.toml"].Content, StringComparison.Ordinal);
        Assert.Contains("## security", files["codex/AGENTS.md"].Content, StringComparison.Ordinal);
        Assert.Contains("## error-handling", files["codex/AGENTS.md"].Content, StringComparison.Ordinal);
        Assert.DoesNotContain("\"agents\"", files[".codex-plugin/plugin.json"].Content, StringComparison.Ordinal);
    }

    [Fact]
    public void Cursor_emits_mdc_rules_with_globs_or_alwaysApply_and_manifest_with_agents()
    {
        var files = Project(new CursorProjector());

        Assert.Contains("alwaysApply: true", files["cursor/rules/security.mdc"].Content, StringComparison.Ordinal);
        var domain = files["cursor/rules/error-handling.mdc"].Content;
        Assert.Contains("globs: \"**/*.cs\"", domain, StringComparison.Ordinal);
        Assert.Contains("alwaysApply: false", domain, StringComparison.Ordinal);
        Assert.True(files.ContainsKey("cursor/commands/specify.md"));
        Assert.Contains("\"agents\"", files["cursor/.cursor-plugin/plugin.json"].Content, StringComparison.Ordinal);
        Assert.True(files.ContainsKey("cursor/.cursor-plugin/agents/dotnet-architect.md"));
    }

    [Fact]
    public void Copilot_emits_applyTo_instructions_prompts_agents_and_universal_instructions()
    {
        var files = Project(new CopilotProjector());

        Assert.Contains("applyTo: \"**/*.cs\"", files["copilot/.github/instructions/error-handling.instructions.md"].Content, StringComparison.Ordinal);
        Assert.True(files.ContainsKey("copilot/.github/prompts/specify.prompt.md"));
        Assert.True(files.ContainsKey("copilot/.github/agents/dotnet-architect.agent.md"));
        Assert.Contains("## security", files["copilot/.github/copilot-instructions.md"].Content, StringComparison.Ordinal);
    }

    [Fact]
    public void All_four_host_directories_are_populated()
    {
        var corpus = Sample();
        var hosts = new IHostProjector[]
        {
            new Claude.ClaudeProjector(), new CodexProjector(), new CursorProjector(), new CopilotProjector(),
        };
        foreach (var projector in hosts)
            Assert.NotEmpty(projector.Project(corpus));
    }
}
