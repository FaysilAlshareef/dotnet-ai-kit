using System.CommandLine;

namespace DotnetAiKit.Cli.Commands;

/// <summary>The <c>configure</c> verb: set a key in the per-solution config.yml.</summary>
internal static class ConfigureCommand
{
    public static Command Create()
    {
        var pathArgument = new Argument<string>("path") { Description = "Solution root.", DefaultValueFactory = _ => ".", Arity = ArgumentArity.ZeroOrOne };
        var setOption = new Option<string>("--set") { Description = "key=value to set.", Required = true };
        var dryRunOption = new Option<bool>("--dry-run") { Description = "Preview; write nothing." };

        var command = new Command("configure", "Set a configuration value in .dotnet-ai-kit/config.yml.");
        command.Arguments.Add(pathArgument);
        command.Options.Add(setOption);
        command.Options.Add(dryRunOption);

        command.SetAction(parseResult =>
        {
            var path = parseResult.GetValue(pathArgument)!;
            var setExpr = parseResult.GetValue(setOption)!;
            var dryRun = parseResult.GetValue(dryRunOption);
            var reporter = CompositionRoot.Reporter;

            var separator = setExpr.IndexOf('=');
            if (separator <= 0)
            {
                reporter.Error("--set expects key=value.");
                return 2;
            }

            var key = setExpr[..separator].Trim();
            var value = setExpr[(separator + 1)..].Trim();
            var result = CompositionRoot.BuildConfigureService().Set(path, key, value, dryRun);
            if (!result.Ok)
            {
                foreach (var error in result.Errors)
                    reporter.Error(error);
                return 1;
            }

            reporter.Success($"configure: {(dryRun ? "would set" : "set")} {result.Message}");
            return 0;
        });

        return command;
    }
}
