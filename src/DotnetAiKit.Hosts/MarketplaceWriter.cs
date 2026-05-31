using System.Text;
using System.Text.Json;
using DotnetAiKit.Application.Ports;
using DotnetAiKit.Core.Manifest;

namespace DotnetAiKit.Hosts;

/// <summary>
/// Emits a project-scoped, version-pinned marketplace catalog at <c>.claude-plugin/marketplace.json</c>
/// (the spec-required location: the marketplace root is the dir containing <c>.claude-plugin/</c>, i.e.
/// <c>build/</c>). One entry whose <c>source</c> is <c>./claude</c> → the plugin root is <c>build/claude/</c>.
/// Deterministic JSON.
/// </summary>
internal static class MarketplaceWriter
{
    public const string RelativePath = ".claude-plugin/marketplace.json";

    public static ProjectedFile Write(PluginManifest manifest)
    {
        var sb = new StringBuilder();
        sb.Append("{\n");
        sb.Append("  \"name\": ").Append(Json(manifest.Name)).Append(",\n");
        sb.Append("  \"description\": ").Append(Json(manifest.Description)).Append(",\n");
        sb.Append("  \"owner\": { \"name\": ").Append(Json("Faysil Alshareef")).Append(" },\n");
        sb.Append("  \"plugins\": [\n");
        sb.Append("    {\n");
        sb.Append("      \"name\": ").Append(Json(manifest.Name)).Append(",\n");
        sb.Append("      \"source\": \"./claude\",\n");
        sb.Append("      \"version\": ").Append(Json(manifest.Version.ToString())).Append(",\n");
        sb.Append("      \"description\": ").Append(Json(manifest.Description)).Append('\n');
        sb.Append("    }\n");
        sb.Append("  ]\n");
        sb.Append("}\n");
        return new ProjectedFile(RelativePath, sb.ToString());
    }

    private static string Json(string value) => JsonSerializer.Serialize(value);
}
