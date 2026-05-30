using System.CommandLine;

namespace DotnetAiKit.Cli.Commands;

/// <summary>The <c>render</c> verb: resolve a skill/rule and substitute project metadata into its body.</summary>
internal static class RenderCommand
{
    public static Command Create()
    {
        var kindArgument = new Argument<string>("kind") { Description = "skill | rule" };
        var nameArgument = new Argument<string>("name") { Description = "Artifact name." };
        var pathOption = new Option<string>("--path") { Description = "Project root for metadata.", DefaultValueFactory = _ => "." };
        var artifactsOption = new Option<string>("--artifacts") { Description = "Authored artifacts root.", DefaultValueFactory = _ => "artifacts" };

        var command = new Command("render", "Render a skill or rule body with current project metadata substituted.");
        command.Arguments.Add(kindArgument);
        command.Arguments.Add(nameArgument);
        command.Options.Add(pathOption);
        command.Options.Add(artifactsOption);

        command.SetAction(parseResult =>
        {
            var kind = parseResult.GetValue(kindArgument)!;
            var name = parseResult.GetValue(nameArgument)!;
            var path = parseResult.GetValue(pathOption)!;
            var artifacts = parseResult.GetValue(artifactsOption)!;

            var result = CompositionRoot.BuildRenderService().Render(artifacts, kind, name, path);
            if (!result.Ok)
            {
                foreach (var error in result.Errors)
                    Console.Error.WriteLine($"error: {error}");
                return 1;
            }

            Console.Write(result.Body);
            if (result.UnresolvedTokens.Count > 0)
                Console.Error.WriteLine($"warning: unresolved tokens: {string.Join(", ", result.UnresolvedTokens)}");
            return 0;
        });

        return command;
    }
}
