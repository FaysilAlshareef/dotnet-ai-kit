using DotnetAiKit.Application.Ports;

namespace DotnetAiKit.Hosts.Claude;

/// <summary>
/// Emits Claude Code's plugin <c>hooks/hooks.json</c> (planning/22, planning/24 — Claude-scoped tiers
/// T1/T2/T4). Wires the two enforcement tiers that are hooks rather than the analyzer:
/// <list type="bullet">
/// <item><b>PreToolUse</b> on Write/Edit → <c>dotnet-ai hook pretooluse</c> (T1 rule/profile injection +
/// T2 deny on generated files).</item>
/// <item><b>Stop / SubagentStop</b> → <c>dotnet-ai hook stop</c> (T4 completion gate: block "done" until
/// build + tests are green).</item>
/// </list>
/// The command is the on-PATH <c>dotnet-ai</c> tool, so the hook is cross-platform (no bash/python/pwsh).
/// Deterministic JSON, fixed key order, LF newlines.
/// </summary>
internal static class ClaudeHooksWriter
{
    public const string RelativePath = "claude/hooks/hooks.json";

    private const string PreToolUseCommand = "dotnet-ai hook pretooluse";
    private const string StopCommand = "dotnet-ai hook stop";

    // T2 judgment hook (planning/24): the command hook does mechanical checks (inject rules + deny
    // generated files); this fast-model prompt hook judges violations the analyzer cannot. Defaults to a
    // fast model (no explicit model field). $ARGUMENTS is the PreToolUse payload. Claude-scoped (AR-3).
    private const string PromptHook =
        "Review the pending file Write/Edit in $ARGUMENTS for a clear architecture-boundary or "
        + "banned-API violation that a build-time analyzer cannot catch. Only if there is a clear, "
        + "high-confidence violation, deny it with a one-sentence reason; otherwise allow.";

    public static ProjectedFile Write()
    {
        const string json =
            "{\n"
            + "  \"hooks\": {\n"
            + "    \"PreToolUse\": [\n"
            + "      {\n"
            + "        \"matcher\": \"Edit|Write|MultiEdit\",\n"
            + "        \"hooks\": [\n"
            + "          { \"type\": \"command\", \"command\": \"" + PreToolUseCommand + "\" },\n"
            + "          { \"type\": \"prompt\", \"prompt\": \"" + PromptHook + "\" }\n"
            + "        ]\n"
            + "      }\n"
            + "    ],\n"
            + "    \"Stop\": [\n"
            + "      {\n"
            + "        \"hooks\": [\n"
            + "          { \"type\": \"command\", \"command\": \"" + StopCommand + "\" }\n"
            + "        ]\n"
            + "      }\n"
            + "    ],\n"
            + "    \"SubagentStop\": [\n"
            + "      {\n"
            + "        \"hooks\": [\n"
            + "          { \"type\": \"command\", \"command\": \"" + StopCommand + "\" }\n"
            + "        ]\n"
            + "      }\n"
            + "    ]\n"
            + "  }\n"
            + "}\n";
        return new ProjectedFile(RelativePath, json);
    }
}
