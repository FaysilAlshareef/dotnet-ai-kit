using System.Text;
using System.Text.Json;
using DotnetAiKit.Application.Ports;
using DotnetAiKit.Core.Manifest;

namespace DotnetAiKit.Hosts;

/// <summary>
/// Emits a project-scoped, version-pinned <c>marketplace.json</c> at the build root (planning/22).
/// One entry, pointing at the generated plugin; deterministic JSON.
/// </summary>
internal static class MarketplaceWriter
{
    public const string RelativePath = "marketplace.json";

    public static ProjectedFile Write(PluginManifest manifest)
    {
        var sb = new StringBuilder();
        sb.Append("{\n");
        sb.Append("  \"name\": ").Append(Json(manifest.Name)).Append(",\n");
        sb.Append("  \"owner\": { \"name\": ").Append(Json("Faysil Alshareef")).Append(" },\n");
        sb.Append("  \"plugins\": [\n");
        sb.Append("    {\n");
        sb.Append("      \"name\": ").Append(Json(manifest.Name)).Append(",\n");
        sb.Append("      \"source\": \".\",\n");
        sb.Append("      \"version\": ").Append(Json(manifest.Version.ToString())).Append(",\n");
        sb.Append("      \"description\": ").Append(Json(manifest.Description)).Append('\n');
        sb.Append("    }\n");
        sb.Append("  ]\n");
        sb.Append("}\n");
        return new ProjectedFile(RelativePath, sb.ToString());
    }

    private static string Json(string value) => JsonSerializer.Serialize(value);
}
