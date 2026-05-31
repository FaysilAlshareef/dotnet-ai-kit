using System.CommandLine;

namespace DotnetAiKit.Cli.Commands;

/// <summary>The <c>migrate</c> verb: clean v1 layout artifacts with rotated backups.</summary>
internal static class MigrateCommand
{
    public static Command Create()
    {
        var pathArgument = new Argument<string>("path") { Description = "Solution root.", DefaultValueFactory = _ => ".", Arity = ArgumentArity.ZeroOrOne };
        var keepOption = new Option<int>("--keep") { Description = "Backup generations to retain.", DefaultValueFactory = _ => 3 };
        var dryRunOption = new Option<bool>("--dry-run") { Description = "Preview; write nothing." };

        var command = new Command("migrate", "Clean v1 layout artifacts with rotated backups (legacy alias migration).");
        command.Arguments.Add(pathArgument);
        command.Options.Add(keepOption);
        command.Options.Add(dryRunOption);

        command.SetAction(parseResult =>
        {
            var path = parseResult.GetValue(pathArgument)!;
            var keep = parseResult.GetValue(keepOption);
            var dryRun = parseResult.GetValue(dryRunOption);
            var reporter = CompositionRoot.Reporter;

            var result = CompositionRoot.BuildMigrateService().Run(path, keep, dryRun);
            if (!result.Ok)
            {
                foreach (var error in result.Errors)
                    reporter.Error(error);
                return 1;
            }

            if (result.Migrated.Count == 0)
            {
                reporter.Info("migrate: nothing to migrate.");
            }
            else
            {
                reporter.Success($"migrate: {(dryRun ? "would migrate" : "migrated")} {result.Migrated.Count} item(s).");
                foreach (var item in result.Migrated)
                    reporter.Info($"  {item}");
            }

            return 0;
        });

        return command;
    }
}
