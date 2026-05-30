using DotnetAiKit.Application.Ports;
using DotnetAiKit.Application.UseCases;
using DotnetAiKit.Hosts;
using DotnetAiKit.Hosts.Claude;
using DotnetAiKit.Infrastructure;

namespace DotnetAiKit.Cli;

/// <summary>Manual DI composition (no Generic Host / keyed DI — AOT-safe). Expanded per phase.</summary>
internal static class CompositionRoot
{
    public static IFileSystem FileSystem { get; } = new PhysicalFileSystem();

    public static HostRegistry HostRegistry { get; } = new(
    [
        new ClaudeProjector(),
        // Codex/Cursor/Copilot projectors registered in P4.
    ]);

    public static GenerateService BuildGenerateService()
    {
        IArtifactSerializer serializer = new YamlFrontmatterParser();
        IArtifactRepository repository = new FileSystemArtifactRepository(FileSystem, serializer);
        IProjectionEngine engine = new ProjectionEngine(HostRegistry);
        return new GenerateService(repository, engine, FileSystem);
    }
}
