using DotnetAiKit.Application.UseCases;
using DotnetAiKit.Infrastructure;
using Xunit;

namespace DotnetAiKit.Application.Tests;

public class BudgetServiceTests
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

    private static BudgetService Build() =>
        new(new FileSystemArtifactRepository(new PhysicalFileSystem(), new YamlFrontmatterParser()), new TiktokenTokenizer());

    [Fact]
    public void Listing_is_within_a_generous_budget_and_commands_are_off_listing()
    {
        var report = Build().Measure(ArtifactsRoot(), limit: 100_000);

        Assert.True(report.Within, $"listing {report.ListingTokens} tokens exceeded {report.Limit}");
        Assert.True(report.ListingTokens > 0);
        Assert.True(report.CommandsOffListing >= 1, "the specify command-skill must be off the always-loaded listing");
        Assert.True(report.ModelInvocableSkills >= 2);
    }

    [Fact]
    public void Budget_regression_is_detected_when_over_limit()
    {
        var report = Build().Measure(ArtifactsRoot(), limit: 1);
        Assert.False(report.Within);
    }
}
