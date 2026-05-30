using DotnetAiKit.Application.Ports;
using DotnetAiKit.Core.Manifest;

namespace DotnetAiKit.Hosts.Claude;

/// <summary>Renders <c>.claude-plugin/plugin.json</c> from the single <see cref="PluginManifest"/>.</summary>
internal static class ClaudeManifestWriter
{
    public const string RelativePath = ".claude-plugin/plugin.json";

    public static ProjectedFile Write(PluginManifest manifest) =>
        new(RelativePath, PluginJson.Write(
            manifest.Name, manifest.Version.ToString(), manifest.Description, manifest.Keywords));
}
