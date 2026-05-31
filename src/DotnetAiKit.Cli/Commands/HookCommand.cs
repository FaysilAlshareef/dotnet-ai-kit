using System.CommandLine;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using DotnetAiKit.Application.UseCases;

namespace DotnetAiKit.Cli.Commands;

/// <summary>
/// The <c>hook</c> verb: the runtime backend for Claude's enforcement hooks (planning/24, Claude-scoped).
/// <c>hook pretooluse</c> reads a PreToolUse event on stdin and emits T1 rule/profile injection or a T2
/// deny; <c>hook stop</c> runs the T4 completion gate (build + tests). Both read the Claude hook protocol
/// on stdin and write it on stdout; both exit 0 even on internal error so a hook never wedges the host.
/// </summary>
internal static class HookCommand
{
    public static Command Create()
    {
        var command = new Command("hook", "Runtime backend for Claude enforcement hooks (pretooluse, stop).");
        command.Subcommands.Add(CreatePreToolUse());
        command.Subcommands.Add(CreateStop());
        return command;
    }

    private static Command CreatePreToolUse()
    {
        var cmd = new Command("pretooluse", "PreToolUse: inject active rules (T1) or deny generated-file edits (T2).");
        cmd.SetAction(_ =>
        {
            try
            {
                var input = Console.In.ReadToEnd();
                var filePath = ReadFilePath(input);
                var rules = LoadRules(Environment.CurrentDirectory);
                var decision = PreToolUseHookService.Decide(filePath, rules);

                if (decision.DenyReason is { } deny)
                    Emit(PreToolUseOutput(permissionDecision: "deny", reason: deny, context: null));
                else if (decision.AdditionalContext is { } ctx)
                    Emit(PreToolUseOutput(permissionDecision: null, reason: null, context: ctx));
            }
            catch
            {
                // Never block the host on a hook failure.
            }

            return 0;
        });
        return cmd;
    }

    private static Command CreateStop()
    {
        var cmd = new Command("stop", "Stop/SubagentStop: block completion until build + tests are green (T4).");
        cmd.SetAction(async (_, cancellationToken) =>
        {
            try
            {
                // If Claude is already in a Stop-hook continuation, do NOT re-block — otherwise a
                // persistently-red build (WIP tests, env issue) wedges the session in a loop it can't
                // escape. Claude sets stop_hook_active for exactly this guard.
                if (StopHookAlreadyActive(Console.In.ReadToEnd()))
                    return 0;

                var gate = await CompositionRoot.BuildVerificationGateService()
                    .EvaluateAsync(Environment.CurrentDirectory, cancellationToken);
                if (!gate.Allowed)
                    Emit(new JsonObject
                    {
                        ["decision"] = "block",
                        ["reason"] = gate.Summary
                            + " — run `dotnet build` and `dotnet test`, fix failures, then finish.",
                    });
            }
            catch
            {
                // Never block the host on a hook failure.
            }

            return 0;
        });
        return cmd;
    }

    private static string? ReadFilePath(string stdin)
    {
        if (string.IsNullOrWhiteSpace(stdin))
            return null;
        var root = JsonNode.Parse(stdin);
        return root?["tool_input"]?["file_path"]?.GetValue<string>();
    }

    private static bool StopHookAlreadyActive(string stdin)
    {
        if (string.IsNullOrWhiteSpace(stdin))
            return false;
        try { return JsonNode.Parse(stdin)?["stop_hook_active"]?.GetValue<bool>() == true; }
        catch { return false; }
    }

    private static JsonObject PreToolUseOutput(string? permissionDecision, string? reason, string? context)
    {
        var specific = new JsonObject { ["hookEventName"] = "PreToolUse" };
        if (permissionDecision is not null)
        {
            specific["permissionDecision"] = permissionDecision;
            specific["permissionDecisionReason"] = reason;
        }

        if (context is not null)
            specific["additionalContext"] = context;

        return new JsonObject { ["hookSpecificOutput"] = specific };
    }

    private static void Emit(JsonNode node) => Console.Out.Write(node.ToJsonString());

    /// <summary>
    /// Loads <c>.claude/rules/*.md</c> into <see cref="HookRule"/>s: <c>paths:</c> globs (empty ⇒ universal)
    /// + the body after the frontmatter. Minimal, dependency-free parsing — robust to missing dir/files.
    /// </summary>
    private static IReadOnlyList<HookRule> LoadRules(string solutionRoot)
    {
        var fs = CompositionRoot.FileSystem;
        var dir = Path.Combine(solutionRoot, ".claude", "rules");
        if (!fs.DirectoryExists(dir))
            return [];

        var rules = new List<HookRule>();
        foreach (var path in fs.EnumerateFiles(dir, "*.md", recursive: false).OrderBy(p => p, StringComparer.Ordinal))
        {
            var text = fs.ReadAllText(path);
            var match = Regex.Match(text, "^---\\r?\\n(.*?)\\r?\\n---\\r?\\n(.*)$", RegexOptions.Singleline);
            if (!match.Success)
                continue;

            var globs = Regex.Matches(match.Groups[1].Value, "-\\s*\"([^\"]+)\"")
                .Select(m => m.Groups[1].Value).ToList();
            rules.Add(new HookRule(globs, match.Groups[2].Value.Trim()));
        }

        return rules;
    }
}
