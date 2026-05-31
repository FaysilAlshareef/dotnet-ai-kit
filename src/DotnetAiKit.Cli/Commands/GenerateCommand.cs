using System.CommandLine;

namespace DotnetAiKit.Cli.Commands;

/// <summary>The <c>generate</c> verb: project <c>artifacts/</c> to every host under <c>build/</c>.</summary>
internal static class GenerateCommand
{
    public static Command Create()
    {
        var artifactsOption = new Option<string>("--artifacts")
        {
            Description = "Authored artifacts root.",
            DefaultValueFactory = _ => "artifacts",
        };
        var outOption = new Option<string>("--out")
        {
            Description = "Output root for generated host files.",
            DefaultValueFactory = _ => "build",
        };
        var checkOption = new Option<bool>("--check")
        {
            Description = "Assert no drift against committed outputs; do not write (CI gate).",
        };

        var command = new Command("generate", "Project artifacts/ to every host under build/ (CI drift gate).");
        command.Options.Add(artifactsOption);
        command.Options.Add(outOption);
        command.Options.Add(checkOption);

        command.SetAction(parseResult =>
        {
            var artifacts = parseResult.GetValue(artifactsOption)!;
            var output = parseResult.GetValue(outOption)!;
            var checkOnly = parseResult.GetValue(checkOption);

            var reporter = CompositionRoot.Reporter;
            var result = CompositionRoot.BuildGenerateService().Run(artifacts, output, checkOnly);

            if (result.Errors.Count > 0)
            {
                foreach (var error in result.Errors)
                    reporter.Error(error);
                return 1;
            }

            if (checkOnly)
            {
                if (result.Drifts.Count > 0)
                {
                    foreach (var drift in result.Drifts)
                        reporter.Warn($"drift: {drift}");
                    reporter.Error($"{result.Drifts.Count} generated file(s) drifted from the committed baseline.");
                    return 3;
                }

                reporter.Success("generate --check: no drift.");
                return 0;
            }

            reporter.Success($"generate: wrote {result.FilesWritten} file(s) to {output}/.");
            return 0;
        });

        return command;
    }
}
