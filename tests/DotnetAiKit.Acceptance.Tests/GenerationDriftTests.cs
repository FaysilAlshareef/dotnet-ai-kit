using DotnetAiKit.Application.Ports;
using DotnetAiKit.Application.UseCases;
using DotnetAiKit.Hosts;
using DotnetAiKit.Hosts.Claude;
using DotnetAiKit.Infrastructure;
using Xunit;

namespace DotnetAiKit.Acceptance.Tests;

/// <summary>SC-001: the drift gate. The committed build/ outputs must match a fresh generation,
/// and a deleted generated file must be restored byte-identically.</summary>
public class GenerationDriftTests
{
    private static GenerateService BuildService()
    {
        IFileSystem fs = new PhysicalFileSystem();
        IArtifactSerializer serializer = new YamlFrontmatterParser();
        IArtifactRepository repository = new FileSystemArtifactRepository(fs, serializer);
        IProjectionEngine engine = new ProjectionEngine(new HostRegistry([new ClaudeProjector()]));
        return new GenerateService(repository, engine, fs);
    }

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

    [Fact]
    public void Committed_build_matches_a_fresh_generation()
    {
        var root = RepoRoot();
        var result = BuildService().Run(Path.Combine(root, "artifacts"), Path.Combine(root, "build"), checkOnly: true);
        Assert.True(result.Ok, "Drift detected: " + string.Join(", ", result.Drifts));
    }

    [Fact]
    public void Deleting_a_generated_file_and_regenerating_restores_it_byte_identically()
    {
        var root = RepoRoot();
        var temp = Path.Combine(Path.GetTempPath(), "dak-gen-" + Guid.NewGuid().ToString("N"));
        try
        {
            var service = BuildService();
            var artifacts = Path.Combine(root, "artifacts");
            service.Run(artifacts, temp, checkOnly: false);

            var target = Path.Combine(temp, "claude", "skills", "specify", "SKILL.md");
            Assert.True(File.Exists(target));
            var original = File.ReadAllText(target);

            File.Delete(target);
            service.Run(artifacts, temp, checkOnly: false);

            Assert.True(File.Exists(target), "Regeneration did not restore the deleted file.");
            Assert.Equal(original, File.ReadAllText(target));
        }
        finally
        {
            if (Directory.Exists(temp))
                Directory.Delete(temp, recursive: true);
        }
    }
}
