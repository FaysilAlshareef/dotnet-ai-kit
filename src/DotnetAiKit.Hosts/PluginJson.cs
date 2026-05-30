using System.Text;
using System.Text.Json;

namespace DotnetAiKit.Hosts;

/// <summary>Deterministic, hand-emitted plugin.json shared by all host manifest writers (FR-010:
/// one descriptor → every host's manifest; no auto-discovered hooks/mcpServers/lspServers keys).</summary>
internal static class PluginJson
{
    public static string Write(string name, string version, string description, IReadOnlyList<string> keywords)
    {
        var sb = new StringBuilder();
        sb.Append("{\n");
        sb.Append("  \"name\": ").Append(Json(name)).Append(",\n");
        sb.Append("  \"version\": ").Append(Json(version)).Append(",\n");
        sb.Append("  \"description\": ").Append(Json(description)).Append(",\n");
        sb.Append("  \"keywords\": ").Append(Array(keywords)).Append('\n');
        sb.Append("}\n");
        return sb.ToString();
    }

    private static string Json(string value) => JsonSerializer.Serialize(value);

    private static string Array(IReadOnlyList<string> values) =>
        values.Count == 0 ? "[]" : "[" + string.Join(", ", values.Select(Json)) + "]";
}
