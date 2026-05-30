using DotnetAiKit.Application.UseCases;
using DotnetAiKit.Hosts.Claude;
using DotnetAiKit.Infrastructure;
using Xunit;

namespace DotnetAiKit.Acceptance.Tests;

/// <summary>SC-002 (the v1 bug fix) + SC-011: init writes .claude/rules/*.md with paths: and a bounded footprint.</summary>
public class RuleDeliveryTests
{
    private const int FootprintBound = 18;

    private static string RepoRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir is not null)
        {
            if (File.Exists(Path.Combine(dir.FullName, "dotnet-ai-kit.slnx")))
                return dir.FullName;
            dir = dir.Parent;
        }

        throw new InvalidOperationException("Could not locate repo root (dotnet-ai-kit.slnx).");
    }

    private static InitService BuildInit()
    {
        var fs = new PhysicalFileSystem();
        return new InitService(
            new DotnetProjectDetector(fs),
            new FileSystemArtifactRepository(fs, new YamlFrontmatterParser()),
            new ClaudeHostAdapter(fs));
    }

    [Fact]
    public void Init_writes_domain_rules_with_paths_and_universal_rules_without()
    {
        var temp = Path.Combine(Path.GetTempPath(), "dak-init-" + Guid.NewGuid().ToString("N"));
        try
        {
            var result = BuildInit().Run(temp, Path.Combine(RepoRoot(), "artifacts"), dryRun: false);
            Assert.True(result.Ok, string.Join("; ", result.Errors));

            // SC-002: the v1 defect is fixed — a domain rule exists with path-scope metadata.
            var domainRule = Path.Combine(temp, ".claude", "rules", "error-handling.md");
            Assert.True(File.Exists(domainRule), "domain rule was not written to .claude/rules/");
            var domainContent = File.ReadAllText(domainRule);
            Assert.Contains("name: error-handling", domainContent, StringComparison.Ordinal);
            Assert.Contains("paths:", domainContent, StringComparison.Ordinal);

            // A universal rule is always-on (no path scope).
            var universalRule = Path.Combine(temp, ".claude", "rules", "security.md");
            Assert.True(File.Exists(universalRule));
            Assert.DoesNotContain("paths:", File.ReadAllText(universalRule), StringComparison.Ordinal);

            // SC-011: bounded footprint (the corpus is not copied per project).
            var fileCount = Directory.EnumerateFiles(temp, "*", SearchOption.AllDirectories).Count();
            Assert.True(fileCount <= FootprintBound, $"footprint of {fileCount} exceeds bound of {FootprintBound}");
        }
        finally
        {
            if (Directory.Exists(temp))
                Directory.Delete(temp, recursive: true);
        }
    }

    [Fact]
    public void Init_dry_run_writes_nothing_but_reports_planned_files()
    {
        var temp = Path.Combine(Path.GetTempPath(), "dak-init-dry-" + Guid.NewGuid().ToString("N"));
        try
        {
            var result = BuildInit().Run(temp, Path.Combine(RepoRoot(), "artifacts"), dryRun: true);
            Assert.True(result.Ok);
            Assert.NotEmpty(result.Write!.Written);
            Assert.False(Directory.Exists(temp), "dry-run must not write any files");
        }
        finally
        {
            if (Directory.Exists(temp))
                Directory.Delete(temp, recursive: true);
        }
    }
}
