using DotnetAiKit.Application.Ports;
using DotnetAiKit.Application.UseCases;
using DotnetAiKit.Core.Project;
using DotnetAiKit.Infrastructure;
using Xunit;

namespace DotnetAiKit.Application.Tests;

public sealed class RenderServiceTests : IDisposable
{
    private readonly string _root = Path.Combine(Path.GetTempPath(), "dak-render-" + Guid.NewGuid().ToString("N"));
    private readonly PhysicalFileSystem _fs = new();

    public void Dispose()
    {
        if (Directory.Exists(_root))
            Directory.Delete(_root, recursive: true);
    }

    private sealed class FakeDetector(ProjectMetadata metadata) : IDetectionProvider
    {
        public ProjectMetadata Detect(string projectRoot) => metadata;
    }

    [Fact]
    public void Render_substitutes_project_metadata_tokens()
    {
        var skillDir = Path.Combine(_root, "artifacts", "skills", "api", "minimal-api-patterns");
        _fs.WriteAllText(Path.Combine(skillDir, "SKILL.md"), """
        ---
        name: minimal-api-patterns
        description: "Generates endpoints. Use when adding routes. Do NOT use for MVC (use controller-patterns)."
        ---
        namespace ${Company}.Api;
        """);

        var repo = new FileSystemArtifactRepository(_fs, new YamlFrontmatterParser());
        var detector = new FakeDetector(new ProjectMetadata { Company = "Acme" });
        var result = new RenderService(repo, detector).Render(Path.Combine(_root, "artifacts"), "skill", "minimal-api-patterns", _root);

        Assert.True(result.Ok, string.Join("; ", result.Errors));
        Assert.Contains("namespace Acme.Api;", result.Body!, StringComparison.Ordinal);
        Assert.Empty(result.UnresolvedTokens);
    }

    [Fact]
    public void Render_reports_not_found()
    {
        _fs.CreateDirectory(Path.Combine(_root, "artifacts", "skills"));
        var repo = new FileSystemArtifactRepository(_fs, new YamlFrontmatterParser());
        var result = new RenderService(repo, new FakeDetector(new ProjectMetadata()))
            .Render(Path.Combine(_root, "artifacts"), "skill", "ghost", _root);

        Assert.False(result.Ok);
        Assert.Contains(result.Errors, e => e.Contains("ghost", StringComparison.Ordinal));
    }
}
