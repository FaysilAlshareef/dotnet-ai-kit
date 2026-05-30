using DotnetAiKit.Core.Artifacts;
using DotnetAiKit.Core.Frontmatter;
using DotnetAiKit.Core.Graph;
using DotnetAiKit.Core.Policies;
using DotnetAiKit.Core.Values;
using Xunit;

namespace DotnetAiKit.Core.Tests;

public class DomainModelTests
{
    private static ArtifactFrontmatter Fm(string name, string desc) => new()
    {
        Name = ArtifactName.From(name),
        Description = Description.From(desc),
    };

    private static Skill MakeSkill(string name, string body, SkillKind kind = SkillKind.Knowledge,
        InvocationPolicy invocation = InvocationPolicy.Default)
    {
        const string desc = "Generates a thing. Use when adding a thing. Do NOT use for other things (use other-skill).";
        return new Skill
        {
            Name = ArtifactName.From(name),
            Description = Description.From(desc),
            Frontmatter = Fm(name, desc),
            Body = body,
            SkillKind = kind,
            Invocation = invocation,
        };
    }

    [Fact]
    public void Skill_with_valid_body_has_no_violations() =>
        Assert.Empty(MakeSkill("query-entity", "line1\nline2").Validate());

    [Fact]
    public void Skill_body_over_500_lines_is_a_violation()
    {
        var body = string.Join('\n', Enumerable.Repeat("x", 501));
        var violations = MakeSkill("big-skill", body).Validate();
        Assert.Contains(violations, v => v.Contains("max 500", StringComparison.Ordinal));
    }

    [Fact]
    public void Command_skill_must_disable_model_invocation()
    {
        var bad = MakeSkill("pr", "body", SkillKind.Command, InvocationPolicy.Default);
        Assert.Contains(bad.Validate(), v => v.Contains("disable-model-invocation", StringComparison.Ordinal));

        var ok = MakeSkill("pr", "body", SkillKind.Command, InvocationPolicy.DisableModelInvocation);
        Assert.Empty(ok.Validate());
        Assert.False(ok.CountsAgainstListing);
    }

    [Fact]
    public void Domain_rule_requires_paths()
    {
        var noPaths = new Rule
        {
            Name = ArtifactName.From("error-handling"),
            Description = Description.From("d"),
            Scope = RuleScope.Domain,
        };
        Assert.Contains(noPaths.Validate(), v => v.Contains("path", StringComparison.OrdinalIgnoreCase));
    }

    [Fact]
    public void Universal_rule_must_be_whitelisted()
    {
        var notWhitelisted = new Rule
        {
            Name = ArtifactName.From("made-up"),
            Description = Description.From("d"),
            Scope = RuleScope.Universal,
        };
        Assert.NotEmpty(notWhitelisted.Validate());

        var whitelisted = new Rule
        {
            Name = ArtifactName.From("security"),
            Description = Description.From("d"),
            Scope = RuleScope.Universal,
        };
        Assert.Empty(whitelisted.Validate());
    }

    [Theory]
    [InlineData("Generates a read-model entity. Use when adding a projection. Do NOT use for aggregates (use add-aggregate).", true)]
    [InlineData("generates stuff lowercase start", false)]
    [InlineData("Generates stuff but has no triggers.", false)]
    public void DescriptionStandard_enforces_shape(string description, bool valid) =>
        Assert.Equal(valid, DescriptionStandard.IsValid(description));

    [Fact]
    public void SubstitutionEngine_replaces_known_tokens_and_flags_unknown()
    {
        var values = new Dictionary<string, string>
        {
            ["Company"] = "Acme",
            ["detected_paths.entities"] = "src/Entities",
        };
        var rendered = SubstitutionEngine.Render(
            "namespace ${Company}.Domain; // ${detected_paths.entities} and ${Unknown}", values);

        Assert.Contains("Acme.Domain", rendered, StringComparison.Ordinal);
        Assert.Contains("src/Entities", rendered, StringComparison.Ordinal);

        var unresolved = SubstitutionEngine.FindUnresolved(rendered);
        Assert.Equal(["Unknown"], unresolved);
    }

    [Fact]
    public void ArtifactGraph_builds_when_edges_resolve()
    {
        ArtifactNode[] nodes =
        [
            new(ArtifactName.From("query-architect"), ArtifactKind.Agent),
            new(ArtifactName.From("query-entity"), ArtifactKind.Skill),
        ];
        ArtifactEdge[] edges =
        [
            new(ArtifactName.From("query-architect"), ArtifactName.From("query-entity"), EdgeKind.OwnedBy),
        ];

        var result = ArtifactGraph.Build(nodes, edges);

        Assert.True(result.Ok);
        Assert.NotNull(result.Graph);
        Assert.Equal([ArtifactName.From("query-entity")],
            result.Graph!.Neighbors(ArtifactName.From("query-architect")).ToArray());
    }

    [Fact]
    public void ArtifactGraph_fails_on_broken_edge()
    {
        ArtifactNode[] nodes = [new(ArtifactName.From("query-architect"), ArtifactKind.Agent)];
        ArtifactEdge[] edges =
        [
            new(ArtifactName.From("query-architect"), ArtifactName.From("ghost-skill"), EdgeKind.OwnedBy),
        ];

        var result = ArtifactGraph.Build(nodes, edges);

        Assert.False(result.Ok);
        Assert.Null(result.Graph);
        Assert.Contains(result.BrokenEdges, e => e.Contains("ghost-skill", StringComparison.Ordinal));
    }
}
