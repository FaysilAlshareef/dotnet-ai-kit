using System.CommandLine;
using DotnetAiKit.Cli.Commands;

var root = new RootCommand("dotnet-ai — single-source artifact engine for .NET AI coding assistants.");
root.Subcommands.Add(GenerateCommand.Create());
root.Subcommands.Add(InitCommand.Create());
root.Subcommands.Add(CheckCommand.Create());
root.Subcommands.Add(RenderCommand.Create());
root.Subcommands.Add(DetectCommand.Create());
root.Subcommands.Add(MigrateCommand.Create());
root.Subcommands.Add(ConfigureCommand.Create());
root.Subcommands.Add(UpgradeCommand.Create());

return await root.Parse(args).InvokeAsync();
