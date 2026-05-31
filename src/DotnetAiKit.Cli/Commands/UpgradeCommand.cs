using System.CommandLine;

namespace DotnetAiKit.Cli.Commands;

/// <summary>The <c>upgrade</c> verb: no-op for plugin-native hosts; <c>--copilot</c> re-renders Copilot.</summary>
internal static class UpgradeCommand
{
    public static Command Create()
    {
        var pathArgument = new Argument<string>("path") { Description = "Solution root.", DefaultValueFactory = _ => ".", Arity = ArgumentArity.ZeroOrOne };
        var copilotOption = new Option<bool>("--copilot") { Description = "Re-render Copilot files only." };

        var command = new Command("upgrade", "Upgrade the per-solution install (no-op for plugin-native hosts).");
        command.Arguments.Add(pathArgument);
        command.Options.Add(copilotOption);

        command.SetAction(parseResult =>
        {
            var copilotOnly = parseResult.GetValue(copilotOption);
            var result = new Application.UseCases.UpgradeService().Run(copilotOnly);
            CompositionRoot.Reporter.Info($"upgrade: {result.Message}");
            return 0;
        });

        return command;
    }
}
