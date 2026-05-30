using System.Text;
using System.Text.Json;
using DotnetAiKit.Application.Ports;
using DotnetAiKit.Core.Manifest;

namespace DotnetAiKit.Hosts.Claude;

/// <summary>
/// Renders <c>.claude-plugin/plugin.json</c> from the single <see cref="PluginManifest"/>.
/// Deterministic, hand-emitted JSON with fixed key order and LF newlines. Auto-discovered keys
/// (hooks/mcpServers/lspServers) are intentionally absent (FR-010).
/// </summary>
internal static class ClaudeManifestWriter
{
    public const string RelativePath = ".claude-plugin/plugin.json";

    public static ProjectedFile Write(PluginManifest manifest)
    {
        var sb = new StringBuilder();
        sb.Append("{\n");
        sb.Append("  \"name\": ").Append(Json(manifest.Name)).Append(",\n");
        sb.Append("  \"version\": ").Append(Json(manifest.Version.ToString())).Append(",\n");
        sb.Append("  \"description\": ").Append(Json(manifest.Description)).Append(",\n");
        sb.Append("  \"keywords\": ").Append(JsonArray(manifest.Keywords)).Append('\n');
        sb.Append("}\n");
        return new ProjectedFile(RelativePath, sb.ToString());
    }

    private static string Json(string value) => JsonSerializer.Serialize(value);

    private static string JsonArray(IReadOnlyList<string> values)
    {
        if (values.Count == 0)
            return "[]";
        return "[" + string.Join(", ", values.Select(Json)) + "]";
    }
}
