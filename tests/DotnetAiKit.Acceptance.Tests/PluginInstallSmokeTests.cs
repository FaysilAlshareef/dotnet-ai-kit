using System.ComponentModel;
using System.Diagnostics;
using Xunit;
using Xunit.Abstractions;

namespace DotnetAiKit.Acceptance.Tests;

/// <summary>
/// FR-022-17/18 (AR-2): per-host install smoke. The Claude plugin + marketplace are validated by the
/// real <c>claude</c> CLI (skipped gracefully when the CLI is absent, so CI without it stays green).
/// Codex/Cursor use a different discovery model (planning/21), with no validator available here, so
/// their generated structure is asserted and the layout tension is recorded (FR-022-18, research §R7).
/// </summary>
public class PluginInstallSmokeTests(ITestOutputHelper output)
{
    private static string RepoRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir is not null && !File.Exists(Path.Combine(dir.FullName, "dotnet-ai-kit.slnx")))
            dir = dir.Parent;
        return dir?.FullName ?? throw new InvalidOperationException("repo root not found");
    }

    /// <summary>First <c>claude</c> launcher on PATH (claude / .exe / .cmd), or null if not installed.</summary>
    private static string? FindClaudeCli()
    {
        var pathDirs = (Environment.GetEnvironmentVariable("PATH") ?? string.Empty).Split(Path.PathSeparator);
        foreach (var dir in pathDirs.Where(d => !string.IsNullOrWhiteSpace(d)))
            foreach (var name in new[] { "claude", "claude.exe", "claude.cmd" })
            {
                var candidate = Path.Combine(dir, name);
                if (File.Exists(candidate))
                    return candidate;
            }

        return null;
    }

    private (int Exit, string Output)? RunClaudeValidate(string cli, string target)
    {
        try
        {
            var psi = new ProcessStartInfo(cli)
            {
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
            };
            psi.ArgumentList.Add("plugin");
            psi.ArgumentList.Add("validate");
            psi.ArgumentList.Add(target);
            psi.ArgumentList.Add("--strict");

            using var process = Process.Start(psi)!;
            var stdout = process.StandardOutput.ReadToEnd();
            var stderr = process.StandardError.ReadToEnd();
            process.WaitForExit(60_000);
            return (process.ExitCode, stdout + stderr);
        }
        catch (Win32Exception)
        {
            return null; // launcher not runnable → treat as absent
        }
    }

    [Fact]
    public void Claude_plugin_and_marketplace_pass_strict_validation_when_cli_present()
    {
        var cli = FindClaudeCli();
        if (cli is null)
        {
            output.WriteLine("claude CLI not on PATH — skipping plugin-validate smoke (CI-portable).");
            return;
        }

        var build = Path.Combine(RepoRoot(), "build");
        foreach (var target in new[] { Path.Combine(build, "claude"), build })
        {
            var result = RunClaudeValidate(cli, target);
            if (result is null)
            {
                output.WriteLine($"claude CLI present but not runnable — skipping {target}.");
                return;
            }

            Assert.True(result.Value.Exit == 0, $"`claude plugin validate {target} --strict` failed:\n{result.Value.Output}");
        }
    }

    [Fact]
    public void Codex_and_cursor_generated_trees_have_their_expected_structure()
    {
        var build = Path.Combine(RepoRoot(), "build");

        // Codex: plugin manifest + AGENTS.md + skills (note: manifest at build/.codex-plugin/, content under
        // build/codex/ — a different discovery model than Claude's marketplace; tracked in research §R7).
        Assert.True(File.Exists(Path.Combine(build, ".codex-plugin", "plugin.json")));
        Assert.True(File.Exists(Path.Combine(build, "codex", "AGENTS.md")));
        Assert.True(Directory.Exists(Path.Combine(build, "codex", "skills")));

        // Cursor: plugin manifest + agents + rules (.mdc) + commands + skills.
        Assert.True(File.Exists(Path.Combine(build, "cursor", ".cursor-plugin", "plugin.json")));
        Assert.True(Directory.Exists(Path.Combine(build, "cursor", ".cursor-plugin", "agents")));
        Assert.True(Directory.Exists(Path.Combine(build, "cursor", "rules")));
        Assert.True(Directory.Exists(Path.Combine(build, "cursor", "commands")));
        Assert.True(Directory.Exists(Path.Combine(build, "cursor", "skills")));
    }
}
