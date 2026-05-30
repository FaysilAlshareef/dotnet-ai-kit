using DotnetAiKit.Core.Artifacts;
using DotnetAiKit.Infrastructure;
using Xunit;

namespace DotnetAiKit.Triggering.Evals;

/// <summary>
/// SC-005 / FR-028: the triggering oracle over the ambiguous clusters. A deterministic lexical
/// selector (description-keyword overlap) stands in for model selection in CI — its job is to prove
/// that authored descriptions are distinguishable: the correct skill fires and its siblings do not.
/// (The full LLM-based eval with 20 queries/skill is a follow-on; this gates description drift now.)
/// </summary>
public class TriggeringOracleTests
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

    private static IReadOnlyList<Skill> LoadSkills()
    {
        var result = new FileSystemArtifactRepository(new PhysicalFileSystem(), new YamlFrontmatterParser()).Load(ArtifactsRoot());
        Assert.True(result.Ok, string.Join("; ", result.Errors));
        return result.Corpus!.Skills;
    }

    private static string Select(IReadOnlyList<Skill> skills, string query)
    {
        var queryWords = Tokenize(query);
        return skills
            .Select(s => (s.Name.Value, Score: Score(queryWords, s.Description.Value)))
            .OrderByDescending(x => x.Score)
            .ThenBy(x => x.Value, StringComparer.Ordinal)
            .First()
            .Value;
    }

    private static HashSet<string> Tokenize(string text) =>
        text.ToLowerInvariant()
            .Split([' ', '\t', '\n', ',', '.', ';', ':', '(', ')', '"', '/', '-'], StringSplitOptions.RemoveEmptyEntries)
            .Where(w => w.Length >= 4)
            .ToHashSet(StringComparer.Ordinal);

    private static int Score(HashSet<string> queryWords, string description)
    {
        var lower = description.ToLowerInvariant();
        return queryWords.Count(w => lower.Contains(w, StringComparison.Ordinal));
    }

    [Theory]
    [InlineData("add a new HTTP endpoint to my minimal API project", "minimal-api-patterns")]
    [InlineData("add an event-sourced aggregate root with domain events", "add-aggregate")]
    [InlineData("create a feature specification from a description", "specify")]
    public void Correct_skill_fires_for_its_query(string query, string expected)
    {
        var skills = LoadSkills();
        Assert.Equal(expected, Select(skills, query));
    }

    [Fact]
    public void Siblings_stay_silent_confusion_matrix()
    {
        var skills = LoadSkills();
        // The aggregate query must NOT select the API skill, and vice-versa.
        Assert.NotEqual("add-aggregate", Select(skills, "add a new HTTP endpoint to my minimal API"));
        Assert.NotEqual("minimal-api-patterns", Select(skills, "add an event-sourced aggregate root"));
    }
}
