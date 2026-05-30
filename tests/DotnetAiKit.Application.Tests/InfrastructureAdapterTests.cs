using DotnetAiKit.Core.Frontmatter;
using DotnetAiKit.Core.Values;
using DotnetAiKit.Infrastructure;
using Xunit;

namespace DotnetAiKit.Application.Tests;

public sealed class InfrastructureAdapterTests : IDisposable
{
    private readonly string _root = Path.Combine(Path.GetTempPath(), "dak-tests-" + Guid.NewGuid().ToString("N"));
    private readonly PhysicalFileSystem _fs = new();
    private readonly YamlFrontmatterParser _serializer = new();

    public void Dispose()
    {
        if (Directory.Exists(_root))
            Directory.Delete(_root, recursive: true);
    }

    [Fact]
    public void YamlFrontmatterParser_round_trips_core_fields()
    {
        var original = new ArtifactFrontmatter
        {
            Name = ArtifactName.From("query-entity"),
            Description = Description.From("Generates a thing. Use when X. Do NOT use for Y (use z)."),
            License = "MIT",
            SchemaVersion = new SemVer(1, 2, 3),
            Metadata = new Dictionary<string, string> { ["category"] = "microservice/query", ["agent"] = "query-architect" },
            HostExtensions = [new HostExtensionBlock { Host = HostName.Claude, Fields = new Dictionary<string, string> { ["paths"] = "src/**/*.cs" } }],
        };

        var fileText = "---\n" + _serializer.ComposeFrontmatter(original) + "---\nthe body\n";
        var parsed = _serializer.ParseFrontmatter(fileText);

        Assert.Equal(original.Name, parsed.Name);
        Assert.Equal(original.Description, parsed.Description);
        Assert.Equal("MIT", parsed.License);
        Assert.Equal(new SemVer(1, 2, 3), parsed.SchemaVersion);
        Assert.Equal("query-architect", parsed.MetadataValue("agent"));
        Assert.Equal("src/**/*.cs", parsed.ForHost(HostName.Claude)?.Get("paths"));
        Assert.Equal("the body\n", _serializer.Split(fileText).Body);
    }

    [Fact]
    public void Repository_loads_a_valid_corpus_and_builds_the_graph()
    {
        WriteSkill("query-entity", agent: "query-architect");
        WriteAgent("query-architect", skills: "query-entity");
        WriteUniversalRule("security");

        var repo = new FileSystemArtifactRepository(_fs, _serializer);
        var result = repo.Load(Path.Combine(_root, "artifacts"));

        Assert.True(result.Ok, string.Join("; ", result.Errors));
        Assert.NotNull(result.Corpus);
        Assert.Single(result.Corpus!.Skills);
        Assert.Single(result.Corpus.Agents);
        Assert.Single(result.Corpus.Rules);
        Assert.NotNull(result.Corpus.Graph);
        Assert.Contains(
            result.Corpus.Graph!.Neighbors(ArtifactName.From("query-architect")),
            n => n == ArtifactName.From("query-entity"));
    }

    [Fact]
    public void Repository_reports_broken_reference_as_error()
    {
        WriteSkill("query-entity", agent: "query-architect");
        WriteAgent("query-architect", skills: "ghost-skill");

        var repo = new FileSystemArtifactRepository(_fs, _serializer);
        var result = repo.Load(Path.Combine(_root, "artifacts"));

        Assert.False(result.Ok);
        Assert.Contains(result.Errors, e => e.Contains("ghost-skill", StringComparison.Ordinal));
    }

    private void WriteSkill(string name, string agent)
    {
        var dir = Path.Combine(_root, "artifacts", "skills", "sample", name);
        var text = $"""
        ---
        name: {name}
        description: "Generates a {name}. Use when adding one. Do NOT use for aggregates (use add-aggregate)."
        metadata:
          agent: {agent}
          paths: "src/**/*.cs"
        ---
        # {name}
        body
        """;
        _fs.WriteAllText(Path.Combine(dir, "SKILL.md"), text);
    }

    private void WriteAgent(string name, string skills)
    {
        var text = $"""
        ---
        name: {name}
        description: "Designs {name} work. Use when building. Do NOT use for the other side (use other-architect)."
        metadata:
          skills: "{skills}"
        ---
        body
        """;
        _fs.WriteAllText(Path.Combine(_root, "artifacts", "agents", name + ".md"), text);
    }

    private void WriteUniversalRule(string name)
    {
        var text = $"""
        ---
        name: {name}
        description: "Enforces {name}. Use when writing code. Do NOT use as review (use review)."
        ---
        body
        """;
        _fs.WriteAllText(Path.Combine(_root, "artifacts", "rules", "conventions", name + ".md"), text);
    }
}
