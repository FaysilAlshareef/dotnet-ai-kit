using DotnetAiKit.Application.Ports;
using DotnetAiKit.Core.Artifacts;
using DotnetAiKit.Core.Policies;
using DotnetAiKit.Hosts;
using DotnetAiKit.Hosts.Claude;
using DotnetAiKit.Hosts.Codex;
using DotnetAiKit.Hosts.Copilot;
using DotnetAiKit.Hosts.Cursor;
using DotnetAiKit.Infrastructure;
using Xunit;
using Xunit.Abstractions;

namespace DotnetAiKit.Acceptance.Tests;

/// <summary>
/// SC-002 / FR-013: the high-coverage gate over the FULL authored corpus. Every artifact must load,
/// the graph must build with zero broken edges, and the corpus must project to all four hosts with no
/// per-host path collisions. DescriptionStandard is a HARD gate for the entire skill corpus (021/C9:
/// every migrated description was brought to standard) and a reported metric for non-skill artifacts.
/// </summary>
public class CorpusIntegrityTests(ITestOutputHelper output)
{

    private static string ArtifactsRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir is not null)
        {
            if (File.Exists(Path.Combine(dir.FullName, "dotnet-ai-kit.slnx")))
                return Path.Combine(dir.FullName, "artifacts");
            dir = dir.Parent;
        }

        throw new InvalidOperationException("repo root not found");
    }

    private static ArtifactCorpus LoadCorpus()
    {
        var result = new FileSystemArtifactRepository(new PhysicalFileSystem(), new YamlFrontmatterParser())
            .Load(ArtifactsRoot());
        Assert.True(result.Ok, "corpus load errors: " + string.Join("; ", result.Errors));
        Assert.NotNull(result.Corpus);
        return result.Corpus!;
    }

    [Fact]
    public void Corpus_loads_with_zero_broken_edges_and_a_real_population()
    {
        var corpus = LoadCorpus();
        Assert.NotNull(corpus.Graph);
        Assert.True(corpus.Skills.Count >= 140, $"expected the full skill corpus, got {corpus.Skills.Count}");
        Assert.True(corpus.Agents.Count >= 15);
        Assert.True(corpus.Rules.Count >= 21);
        Assert.True(corpus.Profiles.Count >= 12);
    }

    [Fact]
    public void Every_skill_name_equals_its_invariants()
    {
        var corpus = LoadCorpus();
        foreach (var artifact in corpus.AllArtifacts())
            Assert.Empty(artifact.Validate());
    }

    [Fact]
    public void Every_host_projects_the_whole_corpus_without_path_collisions()
    {
        var corpus = LoadCorpus();
        IHostProjector[] projectors =
            [new ClaudeProjector(), new CodexProjector(), new CursorProjector(), new CopilotProjector()];

        foreach (var projector in projectors)
        {
            var files = projector.Project(corpus).ToList();
            Assert.NotEmpty(files);
            var dupes = files.GroupBy(f => f.RelativePath, StringComparer.OrdinalIgnoreCase)
                .Where(g => g.Count() > 1).Select(g => g.Key).ToList();
            Assert.True(dupes.Count == 0, $"{projector.Host} path collisions: {string.Join(", ", dupes)}");
        }
    }

    [Fact]
    public void Every_skill_passes_the_description_standard()
    {
        // FR-026 / SC-012: skills are model-selected by their description, so the ENTIRE skill corpus
        // is a hard gate (action-verb-first + "Use when…" + "Do NOT use… (use <sibling>)").
        var corpus = LoadCorpus();
        var failures = new List<string>();
        foreach (var skill in corpus.Skills)
        {
            var violations = DescriptionStandard.Validate(skill.Description.Value);
            if (violations.Count > 0)
                failures.Add($"{skill.Name}: {string.Join("; ", violations)}");
        }

        Assert.True(
            failures.Count == 0,
            $"{failures.Count}/{corpus.Skills.Count} skills violate the description standard:\n"
                + string.Join("\n", failures));
    }

    [Fact]
    public void Non_skill_description_compliance_is_reported_as_a_metric()
    {
        // Rules (path-scoped/always-loaded) and profiles are not model-selected by a "Use when…" trigger,
        // so the standard is reported for them, not gated.
        var corpus = LoadCorpus();
        var all = corpus.AllArtifacts().ToList();
        var compliant = all.Count(a => DescriptionStandard.IsValid(a.Description.Value));
        output.WriteLine(
            $"DescriptionStandard: skills hard-gated; full-corpus compliance {compliant}/{all.Count}.");
    }
}
