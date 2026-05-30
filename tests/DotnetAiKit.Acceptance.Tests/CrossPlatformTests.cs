using DotnetAiKit.Application.Ports;
using DotnetAiKit.Application.UseCases;
using DotnetAiKit.Hosts;
using DotnetAiKit.Hosts.Claude;
using DotnetAiKit.Infrastructure;
using Xunit;

namespace DotnetAiKit.Acceptance.Tests;

/// <summary>SC-012: generated content uses a fixed LF newline regardless of host OS.</summary>
public class CrossPlatformTests
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
    public void Generated_files_use_lf_newlines_only()
    {
        var temp = Path.Combine(Path.GetTempPath(), "dak-nl-" + Guid.NewGuid().ToString("N"));
        try
        {
            var fs = new PhysicalFileSystem();
            var engine = new ProjectionEngine(new HostRegistry(new IHostProjector[] { new ClaudeProjector() }));
            new GenerateService(new FileSystemArtifactRepository(fs, new YamlFrontmatterParser()), engine, fs)
                .Run(Path.Combine(RepoRoot(), "artifacts"), temp, checkOnly: false);

            foreach (var file in Directory.EnumerateFiles(temp, "*", SearchOption.AllDirectories))
            {
                // Read raw bytes — no normalization — to assert the generator wrote LF only.
                var content = File.ReadAllText(file);
                Assert.DoesNotContain('\r', content);
            }
        }
        finally
        {
            if (Directory.Exists(temp))
                Directory.Delete(temp, recursive: true);
        }
    }
}
