using System.Diagnostics;
using DotnetAiKit.Application.UseCases;
using DotnetAiKit.Hosts.Claude;
using DotnetAiKit.Infrastructure;
using Xunit;

namespace DotnetAiKit.Acceptance.Tests;

/// <summary>SC-010: check completes in under 10s and single-artifact render in under 2s.</summary>
public class PerformanceTests
{
    private static string RepoRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir is not null)
        {
            if (File.Exists(Path.Combine(dir.FullName, "dotnet-ai-kit.slnx")))
                return dir.FullName;
            dir = dir.Parent;
        }

        throw new InvalidOperationException("repo root not found");
    }

    [Fact]
    public void Check_under_10s_and_render_under_2s()
    {
        var fs = new PhysicalFileSystem();
        var artifacts = Path.Combine(RepoRoot(), "artifacts");
        var temp = Path.Combine(Path.GetTempPath(), "dak-perf-" + Guid.NewGuid().ToString("N"));
        try
        {
            new InitService(new DotnetProjectDetector(fs), new FileSystemArtifactRepository(fs, new YamlFrontmatterParser()), new ClaudeHostAdapter(fs, new BackupRotationService(fs), new ManifestIntegrityService()))
                .Run(temp, artifacts, dryRun: false);

            var checkSw = Stopwatch.StartNew();
            new CheckService(fs, new ManifestIntegrityService()).Run(temp);
            checkSw.Stop();
            Assert.True(checkSw.Elapsed.TotalSeconds < 10, $"check took {checkSw.Elapsed.TotalSeconds:F2}s");

            var renderSw = Stopwatch.StartNew();
            var render = new RenderService(new FileSystemArtifactRepository(fs, new YamlFrontmatterParser()), new DotnetProjectDetector(fs))
                .Render(artifacts, "skill", "minimal-api-patterns", temp);
            renderSw.Stop();
            Assert.True(render.Ok);
            Assert.True(renderSw.Elapsed.TotalSeconds < 2, $"render took {renderSw.Elapsed.TotalSeconds:F2}s");
        }
        finally
        {
            if (Directory.Exists(temp))
                Directory.Delete(temp, recursive: true);
        }
    }
}
