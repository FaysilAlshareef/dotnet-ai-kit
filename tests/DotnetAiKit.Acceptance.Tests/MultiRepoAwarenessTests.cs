using DotnetAiKit.Application.UseCases;
using DotnetAiKit.Infrastructure;
using Xunit;

namespace DotnetAiKit.Acceptance.Tests;

/// <summary>SC-009 / FR-G8: after orchestrate, every service-map repo has a feature-brief with the matching id.</summary>
public class MultiRepoAwarenessTests
{
    [Fact]
    public void Every_service_map_repo_gets_a_brief_with_matching_feature_id()
    {
        var roots = new[] { "command", "query", "processor" }
            .Select(role => (role, path: Path.Combine(Path.GetTempPath(), $"dak-mr-{role}-{Guid.NewGuid():N}")))
            .ToList();
        foreach (var (_, path) in roots)
            Directory.CreateDirectory(path);

        try
        {
            var serviceMap = new List<AffectedRepo>
            {
                new(roots[0].path, "command", [], ["OrderPlaced"]),
                new(roots[1].path, "query", ["OrderPlaced"], []),
                new(roots[2].path, "processor", ["OrderPlaced"], ["OrderConfirmed"]),
            };

            var result = new OrchestrateService(new PhysicalFileSystem())
                .Run("042", "order placement flow", serviceMap, dryRun: false);

            Assert.True(result.Ok);
            Assert.Equal(3, result.BriefsWritten.Count);

            foreach (var (_, path) in roots)
            {
                var brief = Path.Combine(path, ".dotnet-ai-kit", "features", "042", "feature-brief.md");
                Assert.True(File.Exists(brief), $"missing brief in {path}");
                Assert.Contains("feature_id: 042", File.ReadAllText(brief), StringComparison.Ordinal);
            }
        }
        finally
        {
            foreach (var (_, path) in roots)
                if (Directory.Exists(path))
                    Directory.Delete(path, recursive: true);
        }
    }

    [Fact]
    public void Missing_repo_is_skipped_not_fatal()
    {
        var serviceMap = new List<AffectedRepo>
        {
            new(Path.Combine(Path.GetTempPath(), "dak-nope-" + Guid.NewGuid().ToString("N")), "command", [], []),
        };

        var result = new OrchestrateService(new PhysicalFileSystem()).Run("001", "x", serviceMap, dryRun: false);

        Assert.True(result.Ok);
        Assert.Single(result.Skipped);
        Assert.Empty(result.BriefsWritten);
    }
}
