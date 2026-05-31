using DotnetAiKit.Application.Ports;
using DotnetAiKit.Application.UseCases;
using DotnetAiKit.Cli.Output;
using DotnetAiKit.Core.Values;
using DotnetAiKit.Hosts;
using DotnetAiKit.Hosts.Claude;
using DotnetAiKit.Hosts.Codex;
using DotnetAiKit.Hosts.Copilot;
using DotnetAiKit.Hosts.Cursor;
using DotnetAiKit.Infrastructure;

namespace DotnetAiKit.Cli;

/// <summary>Manual DI composition (no Generic Host / keyed DI — AOT-safe). Expanded per phase.</summary>
internal static class CompositionRoot
{
    public static IFileSystem FileSystem { get; } = new PhysicalFileSystem();

    public static IConsoleReporter Reporter { get; } = new SpectreConsoleReporter();

    public static HostRegistry HostRegistry { get; } = new(
    [
        new ClaudeProjector(),
        new CodexProjector(),
        new CursorProjector(),
        new CopilotProjector(),
    ]);

    private static IArtifactRepository BuildRepository() =>
        new FileSystemArtifactRepository(FileSystem, new YamlFrontmatterParser());

    private static IDetectionProvider BuildDetector() => new DotnetProjectDetector(FileSystem);

    public static GenerateService BuildGenerateService() =>
        new(BuildRepository(), new ProjectionEngine(HostRegistry), FileSystem);

    public static CheckService BuildCheckService() => new(FileSystem);

    public static RenderService BuildRenderService() => new(BuildRepository(), BuildDetector());

    public static DetectService BuildDetectService() => new(BuildDetector());

    public static MigrateService BuildMigrateService() => new(FileSystem, new BackupRotationService(FileSystem));

    public static ConfigureService BuildConfigureService() => new(FileSystem);

    public static InitService BuildInitService(HostName host)
    {
        IDetectionProvider detector = BuildDetector();
        IHostAdapter adapter = host switch
        {
            HostName.Claude => new ClaudeHostAdapter(FileSystem),
            _ => throw new NotSupportedException($"init for host '{host}' is not implemented yet."),
        };
        return new InitService(detector, BuildRepository(), adapter);
    }
}
