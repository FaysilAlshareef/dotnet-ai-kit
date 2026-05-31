using DotnetAiKit.Application.Ports;
using DotnetAiKit.Application.UseCases;
using DotnetAiKit.Hosts;
using DotnetAiKit.Hosts.Claude;
using DotnetAiKit.Infrastructure;
using Xunit;

namespace DotnetAiKit.Acceptance.Tests;

/// <summary>SC-001 completeness: a generated file that is no longer produced (orphan) is deleted in
/// write mode and reported as drift in check mode, so build/ exactly matches the corpus.</summary>
public class OrphanCleanupTests
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

    private static GenerateService Build()
    {
        var fs = new PhysicalFileSystem();
        var engine = new ProjectionEngine(new HostRegistry(new IHostProjector[] { new ClaudeProjector() }));
        return new GenerateService(new FileSystemArtifactRepository(fs, new YamlFrontmatterParser()), engine, fs);
    }

    [Fact]
    public void Write_mode_deletes_orphans_and_check_mode_flags_them()
    {
        var temp = Path.Combine(Path.GetTempPath(), "dak-orphan-" + Guid.NewGuid().ToString("N"));
        try
        {
            var service = Build();
            var artifacts = Path.Combine(RepoRoot(), "artifacts");
            service.Run(artifacts, temp, checkOnly: false);

            var orphan = Path.Combine(temp, "claude", "skills", "ghost", "SKILL.md");
            Directory.CreateDirectory(Path.GetDirectoryName(orphan)!);
            File.WriteAllText(orphan, "stale\n");

            // check mode flags the orphan as drift
            var checkResult = service.Run(artifacts, temp, checkOnly: true);
            Assert.False(checkResult.Ok);
            Assert.Contains(checkResult.Drifts, d => d.Contains("ghost", StringComparison.Ordinal));

            // write mode removes it
            service.Run(artifacts, temp, checkOnly: false);
            Assert.False(File.Exists(orphan), "orphan was not deleted on regeneration");
            Assert.True(service.Run(artifacts, temp, checkOnly: true).Ok);
        }
        finally
        {
            if (Directory.Exists(temp))
                Directory.Delete(temp, recursive: true);
        }
    }
}
