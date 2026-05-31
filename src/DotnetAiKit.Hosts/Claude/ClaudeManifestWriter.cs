using DotnetAiKit.Application.Ports;
using DotnetAiKit.Core.Manifest;

namespace DotnetAiKit.Hosts.Claude;

/// <summary>
/// Renders the Claude plugin manifest at <c>claude/.claude-plugin/plugin.json</c>. The plugin root is
/// <c>build/claude/</c> (the marketplace entry's <c>source</c> is <c>./claude</c>), so skills/, agents/,
/// and hooks/hooks.json sit at the plugin root and are auto-discovered with no path declarations
/// (plugins-reference: components live at the plugin root, not inside <c>.claude-plugin/</c>).
/// </summary>
internal static class ClaudeManifestWriter
{
    public const string RelativePath = "claude/.claude-plugin/plugin.json";

    public static ProjectedFile Write(PluginManifest manifest) =>
        new(RelativePath, PluginJson.Write(
            manifest.Name, manifest.Version.ToString(), manifest.Description, manifest.Keywords));
}
