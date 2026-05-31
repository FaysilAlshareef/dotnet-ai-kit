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

    // ---- FR-022-06/07: authored evals/cases.jsonl + a discriminating confusion-matrix gate (SC-022-3) ----

    private sealed record EvalCase(string Skill, string Query, string Expect, int TopK);

    private static IReadOnlyList<EvalCase> LoadEvalCases(IReadOnlyList<Skill> skills)
    {
        var cases = new List<EvalCase>();
        foreach (var skill in skills)
            foreach (var file in skill.Resources.Evals.Where(e => e.RelativePath.EndsWith("cases.jsonl", StringComparison.Ordinal)))
                foreach (var line in file.Content.Split('\n').Select(l => l.Trim()).Where(l => l.Length > 0))
                {
                    var node = System.Text.Json.Nodes.JsonNode.Parse(line)!;
                    cases.Add(new EvalCase(
                        skill.Name.Value,
                        node["query"]!.GetValue<string>(),
                        node["expect"]!.GetValue<string>(),
                        node["topk"]?.GetValue<int>() ?? 1));
                }

        return cases;
    }

    private static IReadOnlyList<(string Name, int Score)> Rank(IReadOnlyList<Skill> skills, string query)
    {
        var queryWords = Tokenize(query);
        return skills
            .Select(s => (Name: s.Name.Value, Score: Score(queryWords, s.Description.Value)))
            .OrderByDescending(x => x.Score)
            .ThenBy(x => x.Name, StringComparer.Ordinal)
            .ToList();
    }

    [Fact]
    public void Authored_eval_cases_select_the_correct_skill_and_discriminate()
    {
        var skills = LoadSkills();
        var cases = LoadEvalCases(skills); // empty until clusters author evals/cases.jsonl; then this activates
        var failures = new List<string>();

        foreach (var c in cases)
        {
            if (skills.All(s => s.Name.Value != c.Expect))
            {
                failures.Add($"[{c.Skill}] case 'expect' names a non-existent skill: {c.Expect}");
                continue;
            }

            var ranked = Rank(skills, c.Query);
            var rank = ranked.ToList().FindIndex(r => r.Name == c.Expect);
            if (rank < 0 || rank >= c.TopK)
            {
                failures.Add($"[{c.Skill}] '{c.Query}' → want {c.Expect} in top {c.TopK}, got [{string.Join(", ", ranked.Take(3).Select(r => r.Name))}]");
                continue;
            }

            // Discrimination: a #1 hit must STRICTLY outrank the runner-up (a tie proves nothing).
            if (rank == 0 && ranked.Count > 1 && ranked[0].Score == ranked[1].Score)
                failures.Add($"[{c.Skill}] '{c.Query}' ties {c.Expect} with {ranked[1].Name} at score {ranked[0].Score} — not discriminating");
        }

        Assert.True(failures.Count == 0, $"{failures.Count}/{cases.Count} eval cases failed:\n" + string.Join("\n", failures));
    }
}
