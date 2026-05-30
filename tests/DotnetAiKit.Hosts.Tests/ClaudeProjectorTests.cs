using DotnetAiKit.Application.Ports;
using DotnetAiKit.Core.Artifacts;
using DotnetAiKit.Core.Frontmatter;
using DotnetAiKit.Core.Manifest;
using DotnetAiKit.Core.Values;
using DotnetAiKit.Hosts.Claude;
using Xunit;

namespace DotnetAiKit.Hosts.Tests;

public class ClaudeProjectorTests
{
    private static ArtifactFrontmatter Fm(string name, string desc) => new()
    {
        Name = ArtifactName.From(name),
        Description = Description.From(desc),
    };

    private static IReadOnlyDictionary<string, ProjectedFile> Project(ArtifactCorpus corpus) =>
        new ClaudeProjector().Project(corpus).ToDictionary(f => f.RelativePath);

    [Fact]
    public void Knowledge_skill_projects_paths_and_no_invocation_flag()
    {
        const string desc = "Generates endpoints. Use when adding routes. Do NOT use for MVC (use controller-patterns).";
        var corpus = new ArtifactCorpus
        {
            Skills =
            [
                new Skill
                {
                    Name = ArtifactName.From("minimal-api-patterns"),
                    Description = Description.From(desc),
                    Frontmatter = Fm("minimal-api-patterns", desc),
                    Body = "# body\n",
                    Paths = [Glob.From("**/Endpoints/**/*.cs")],
                },
            ],
        };

        var file = Project(corpus)["claude/skills/minimal-api-patterns/SKILL.md"];
        Assert.Contains("name: minimal-api-patterns", file.Content, StringComparison.Ordinal);
        Assert.Contains("paths:\n  - \"**/Endpoints/**/*.cs\"", file.Content, StringComparison.Ordinal);
        Assert.DoesNotContain("disable-model-invocation", file.Content, StringComparison.Ordinal);
    }

    [Fact]
    public void Command_skill_projects_disable_model_invocation()
    {
        const string desc = "Creates a spec. Use when starting a feature. Do NOT use for planning (use plan).";
        var corpus = new ArtifactCorpus
        {
            Skills =
            [
                new Skill
                {
                    Name = ArtifactName.From("specify"),
                    Description = Description.From(desc),
                    Frontmatter = Fm("specify", desc),
                    Body = "# /specify\n",
                    SkillKind = SkillKind.Command,
                    Invocation = InvocationPolicy.DisableModelInvocation,
                },
            ],
        };

        var file = Project(corpus)["claude/skills/specify/SKILL.md"];
        Assert.Contains("disable-model-invocation: true", file.Content, StringComparison.Ordinal);
    }

    [Fact]
    public void Domain_rule_projects_paths()
    {
        const string desc = "Applies error handling. Use when adding error paths. Do NOT use for logging (use observability).";
        var corpus = new ArtifactCorpus
        {
            Rules =
            [
                new Rule
                {
                    Name = ArtifactName.From("error-handling"),
                    Description = Description.From(desc),
                    Body = "# rule\n",
                    Scope = RuleScope.Domain,
                    Paths = [Glob.From("**/*.cs")],
                },
            ],
        };

        var file = Project(corpus)["claude/rules/error-handling.md"];
        Assert.Contains("paths:\n  - \"**/*.cs\"", file.Content, StringComparison.Ordinal);
    }

    [Fact]
    public void Manifest_has_no_auto_discovered_keys()
    {
        var corpus = new ArtifactCorpus
        {
            Manifest = new PluginManifest
            {
                Name = "dotnet-ai-kit",
                Version = new SemVer(2, 0, 0),
                Description = "desc",
                Keywords = ["dotnet", "ai"],
            },
        };

        var file = Project(corpus)[".claude-plugin/plugin.json"];
        Assert.Contains("\"name\": \"dotnet-ai-kit\"", file.Content, StringComparison.Ordinal);
        Assert.Contains("\"version\": \"2.0.0\"", file.Content, StringComparison.Ordinal);
        Assert.DoesNotContain("hooks", file.Content, StringComparison.Ordinal);
        Assert.DoesNotContain("mcpServers", file.Content, StringComparison.Ordinal);
        Assert.DoesNotContain("lspServers", file.Content, StringComparison.Ordinal);
    }
}
