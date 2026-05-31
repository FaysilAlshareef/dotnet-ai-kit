using System.CommandLine;
using DotnetAiKit.Core;
using DotnetAiKit.Core.Values;

namespace DotnetAiKit.Cli.Commands;

/// <summary>The <c>init</c> verb: write the per-solution footprint, including .claude/rules with paths:.</summary>
internal static class InitCommand
{
    public static Command Create()
    {
        var pathArgument = new Argument<string>("path")
        {
            Description = "Target solution root.",
            DefaultValueFactory = _ => ".",
            Arity = ArgumentArity.ZeroOrOne,
        };
        var hostOption = new Option<string>("--host")
        {
            Description = "Target host (claude).",
            DefaultValueFactory = _ => "claude",
        };
        var artifactsOption = new Option<string>("--artifacts")
        {
            Description = "Authored artifacts root (corpus source).",
            DefaultValueFactory = _ => "artifacts",
        };
        var dryRunOption = new Option<bool>("--dry-run")
        {
            Description = "Preview the files that would be written; write nothing.",
        };

        var command = new Command("init", "Initialize the per-solution footprint (writes .claude/rules/*.md with paths:).");
        command.Arguments.Add(pathArgument);
        command.Options.Add(hostOption);
        command.Options.Add(artifactsOption);
        command.Options.Add(dryRunOption);

        command.SetAction(parseResult =>
        {
            var path = parseResult.GetValue(pathArgument)!;
            var artifacts = parseResult.GetValue(artifactsOption)!;
            var dryRun = parseResult.GetValue(dryRunOption);

            var reporter = CompositionRoot.Reporter;

            HostName host;
            try { host = HostNames.Parse(parseResult.GetValue(hostOption)!); }
            catch (DomainException ex) { reporter.Error(ex.Message); return 2; }

            var result = CompositionRoot.BuildInitService(host).Run(path, artifacts, dryRun);
            if (!result.Ok)
            {
                foreach (var error in result.Errors)
                    reporter.Error(error);
                return 1;
            }

            var verb = dryRun ? "would write" : "wrote";
            reporter.Success($"init: {verb} {result.Write!.Written.Count} file(s){(dryRun ? " (dry-run)" : "")}.");
            foreach (var file in result.Write.Written)
                reporter.Info($"  {file}");
            return 0;
        });

        return command;
    }
}
