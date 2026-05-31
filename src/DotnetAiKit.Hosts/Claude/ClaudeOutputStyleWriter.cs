using DotnetAiKit.Application.Ports;

namespace DotnetAiKit.Hosts.Claude;

/// <summary>
/// Emits a forced output-style at <c>claude/output-styles/dotnet-ai-conventions.md</c> (plugins-reference:
/// an <c>output-styles/&lt;name&gt;.md</c> applies automatically while the plugin is enabled). This is the
/// additional Claude-native rule-delivery channel from AR-10 / FR-022-16 — it complements the advisory
/// rules (<c>.claude/rules</c>), the PreToolUse injection, and the analyzer, restating the always-on
/// conventions as a persistent output style.
/// </summary>
internal static class ClaudeOutputStyleWriter
{
    public const string RelativePath = "claude/output-styles/dotnet-ai-conventions.md";

    public static ProjectedFile Write()
    {
        const string content =
            "---\n"
            + "name: dotnet-ai-conventions\n"
            + "description: Always-on dotnet-ai-kit .NET conventions and enforcement discipline.\n"
            + "---\n"
            + "# dotnet-ai-kit conventions (always-on)\n\n"
            + "While this plugin is enabled, when working in this .NET solution:\n\n"
            + "- Follow the projected domain rules in `.claude/rules/*.md` for the file you are editing "
            + "(they load by `paths:` scope); universal rules always apply.\n"
            + "- Respect the detected architecture profile's boundaries; do not cross layer/dependency lines.\n"
            + "- Mechanical conventions are enforced by the shipped Roslyn analyzer (DAK0001 no `async void`; "
            + "DAK0004 aggregates expose no public setters) — write code that compiles clean under them.\n"
            + "- Do not claim a task done without fresh build + test evidence (the Stop gate verifies this).\n"
            + "- Prefer the bundled skill examples/scripts over improvising; never auto-run a bundled script "
            + "without consent.\n";
        return new ProjectedFile(RelativePath, content);
    }
}
