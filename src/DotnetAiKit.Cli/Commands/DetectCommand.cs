using System.CommandLine;

namespace DotnetAiKit.Cli.Commands;

/// <summary>The <c>detect</c> verb: print detected architecture, .NET version, and path map.</summary>
internal static class DetectCommand
{
    public static Command Create()
    {
        var pathArgument = new Argument<string>("path")
        {
            Description = "Project root to inspect.",
            DefaultValueFactory = _ => ".",
            Arity = ArgumentArity.ZeroOrOne,
        };

        var command = new Command("detect", "Detect architecture, .NET version, and paths.");
        command.Arguments.Add(pathArgument);

        command.SetAction(parseResult =>
        {
            var path = parseResult.GetValue(pathArgument)!;
            var reporter = CompositionRoot.Reporter;
            var metadata = CompositionRoot.BuildDetectService().Run(path);

            reporter.Info($"architecture:   {(metadata.Architecture.Length > 0 ? metadata.Architecture : "(unknown)")}");
            reporter.Info($"dotnet_version: {(metadata.DotnetVersion.Length > 0 ? metadata.DotnetVersion : "(unknown)")}");
            reporter.Info($"detected_paths: {metadata.DetectedPaths.Paths.Count}");
            foreach (var (key, value) in metadata.DetectedPaths.Paths.OrderBy(p => p.Key, StringComparer.Ordinal))
                reporter.Info($"  {key} -> {value}");
            return 0;
        });

        return command;
    }
}
