namespace DotnetAiKit.Application.UseCases;

public sealed record UpgradeResult(bool Ok, string Message);

/// <summary>
/// Upgrade is a no-op for plugin-native hosts — the corpus is delivered from the plugin install path,
/// so there is nothing per-solution to re-copy (FR-015 amends v1). <c>--copilot</c> signals that the
/// render-only Copilot files should be regenerated (the only host that is not plugin-native).
/// </summary>
public sealed class UpgradeService
{
    public UpgradeResult Run(bool copilotOnly) =>
        copilotOnly
            ? new UpgradeResult(true, "Re-render Copilot files via `generate` (Copilot cloud agent is render-only).")
            : new UpgradeResult(true, "No-op: plugin-native hosts (Claude/Codex/Cursor) upgrade via the plugin manager.");
}
