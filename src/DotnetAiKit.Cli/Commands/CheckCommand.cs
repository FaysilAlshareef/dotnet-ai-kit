using System.CommandLine;

namespace DotnetAiKit.Cli.Commands;

/// <summary>The <c>check</c> verb: read-only validation returning the enumerated exit-code contract.</summary>
internal static class CheckCommand
{
    public static Command Create()
    {
        var pathArgument = new Argument<string>("path")
        {
            Description = "Solution root to validate.",
            DefaultValueFactory = _ => ".",
            Arity = ArgumentArity.ZeroOrOne,
        };
        var jsonOption = new Option<bool>("--json") { Description = "Emit a machine-readable report." };

        var command = new Command("check", "Validate the install (read-only); returns an enumerated exit code.");
        command.Arguments.Add(pathArgument);
        command.Options.Add(jsonOption);

        command.SetAction(parseResult =>
        {
            var path = parseResult.GetValue(pathArgument)!;
            var json = parseResult.GetValue(jsonOption);
            var result = CompositionRoot.BuildCheckService().Run(path);

            if (json)
            {
                // Machine-readable: raw stdout, no markup.
                Console.WriteLine($"{{ \"exitCode\": {result.ExitCode}, \"checks\": {result.Checks.Count} }}");
            }
            else
            {
                var reporter = CompositionRoot.Reporter;
                foreach (var check in result.Checks)
                    reporter.Info($"  [{check.Status}] {check.Name} {check.Details}".TrimEnd());
                if (result.Healthy)
                    reporter.Success("check: all checks pass (exit 0).");
                else
                    reporter.Error($"check: exit {result.ExitCode}.");
            }

            return result.ExitCode;
        });

        return command;
    }
}
