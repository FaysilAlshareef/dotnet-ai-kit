using System.CommandLine;
using DotnetAiKit.Cli.Commands;
using Xunit;

namespace DotnetAiKit.Cli.Tests;

/// <summary>
/// FR-014/SC-007: the exit-code contract must hold at the *command pipeline* level — i.e. the value
/// SetAction returns must propagate through InvokeAsync (the real process exit code), not just inside
/// the use-case. These tests drive the actual System.CommandLine tree.
/// </summary>
public class CliExitCodeTests
{
    private static string RepoRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir is not null)
        {
            if (File.Exists(Path.Combine(dir.FullName, "dotnet-ai-kit.slnx")))
                return dir.FullName;
            dir = dir.Parent;
        }

        throw new InvalidOperationException("repo root not found");
    }

    [Fact]
    public async Task Check_verb_propagates_exit_10_for_uninitialized_directory()
    {
        var temp = Path.Combine(Path.GetTempPath(), "dak-cli-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(temp);
        try
        {
            var root = new RootCommand();
            root.Subcommands.Add(CheckCommand.Create());
            var exit = await root.Parse(["check", temp]).InvokeAsync();
            Assert.Equal(10, exit);
        }
        finally { Directory.Delete(temp, recursive: true); }
    }

    [Fact]
    public async Task Generate_check_propagates_exit_0_when_no_drift()
    {
        var temp = Path.Combine(Path.GetTempPath(), "dak-cli-gen-" + Guid.NewGuid().ToString("N"));
        try
        {
            var artifacts = Path.Combine(RepoRoot(), "artifacts");
            var root = new RootCommand();
            root.Subcommands.Add(GenerateCommand.Create());

            await root.Parse(["generate", "--artifacts", artifacts, "--out", temp]).InvokeAsync();
            var exit = await root.Parse(["generate", "--check", "--artifacts", artifacts, "--out", temp]).InvokeAsync();
            Assert.Equal(0, exit);
        }
        finally { if (Directory.Exists(temp)) Directory.Delete(temp, recursive: true); }
    }

    [Fact]
    public async Task Hook_pretooluse_runs_the_v2_backend_and_emits_deny_protocol()
    {
        // FR-022-11: prove the `hook` verb actually runs end-to-end (stdin → Claude hook protocol),
        // not just that hooks.json is discovered. A generated/build-output path → permissionDecision: deny.
        var origIn = Console.In;
        var origOut = Console.Out;
        var captured = new StringWriter();
        try
        {
            Console.SetIn(new StringReader("{\"tool_input\":{\"file_path\":\"src/obj/Debug/App.g.cs\"}}"));
            Console.SetOut(captured);
            var root = new RootCommand();
            root.Subcommands.Add(HookCommand.Create());
            var exit = await root.Parse(["hook", "pretooluse"]).InvokeAsync();
            Assert.Equal(0, exit);
        }
        finally
        {
            Console.SetIn(origIn);
            Console.SetOut(origOut);
        }

        var output = captured.ToString();
        Assert.Contains("\"hookEventName\":\"PreToolUse\"", output, StringComparison.Ordinal);
        Assert.Contains("\"permissionDecision\":\"deny\"", output, StringComparison.Ordinal);
    }
}
