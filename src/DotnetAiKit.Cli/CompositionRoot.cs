using DotnetAiKit.Application.Ports;
using DotnetAiKit.Application.UseCases;
using DotnetAiKit.Core.Values;
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

    private static IArtifactRepository BuildRepository() =>
        new FileSystemArtifactRepository(FileSystem, new YamlFrontmatterParser());

    public static GenerateService BuildGenerateService() =>
        new(BuildRepository(), new ProjectionEngine(HostRegistry), FileSystem);

    public static InitService BuildInitService(HostName host)
    {
        IDetectionProvider detector = new DotnetProjectDetector(FileSystem);
        IHostAdapter adapter = host switch
        {
            HostName.Claude => new ClaudeHostAdapter(FileSystem),
            _ => throw new NotSupportedException($"init for host '{host}' is not implemented yet."),
        };
        return new InitService(detector, BuildRepository(), adapter);
    }
}
