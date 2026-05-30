using System.Text;
using DotnetAiKit.Application.Ports;
using DotnetAiKit.Core;
using DotnetAiKit.Core.Frontmatter;
using DotnetAiKit.Core.Values;
using YamlDotNet.Core;
using YamlDotNet.Serialization;

namespace DotnetAiKit.Infrastructure;

/// <summary>
/// Parses/emits YAML frontmatter + body. Uses YamlDotNet for parsing (reflection-based — acceptable
/// while AOT is deferred, behind this seam) and a deterministic hand-written emitter for composing
/// (stable key ordering, fixed quoting — FR-011).
/// </summary>
public sealed class YamlFrontmatterParser : IArtifactSerializer
{
    private static readonly IDeserializer Deserializer = new DeserializerBuilder().Build();

    public FrontmatterDocument Split(string fileText)
    {
        var text = (fileText ?? string.Empty).Replace("\r\n", "\n");
        if (!text.StartsWith("---\n", StringComparison.Ordinal))
            return new FrontmatterDocument(string.Empty, text);

        var close = text.IndexOf("\n---", 3, StringComparison.Ordinal);
        if (close < 0)
            return new FrontmatterDocument(string.Empty, text);

        var frontmatter = text.Substring(4, close - 4);
        var afterDelim = close + 4;
        var newline = text.IndexOf('\n', afterDelim);
        var body = newline >= 0 ? text[(newline + 1)..] : string.Empty;
        return new FrontmatterDocument(frontmatter, body);
    }

    public ArtifactFrontmatter ParseFrontmatter(string fileText)
    {
        var doc = Split(fileText);
        Dictionary<object, object?> map;
        try
        {
            map = Deserializer.Deserialize<Dictionary<object, object?>>(doc.Frontmatter)
                  ?? new Dictionary<object, object?>();
        }
        catch (YamlException ex)
        {
            throw new DomainException($"Invalid frontmatter YAML: {ex.Message}");
        }

        object? Lookup(string key) => map.TryGetValue(key, out var v) ? v : null;

        var hostExtensions = new List<HostExtensionBlock>();
        foreach (var kv in map)
        {
            var key = AsString(kv.Key);
            if (!key.StartsWith("x-", StringComparison.Ordinal))
                continue;
            var hostSlug = key[2..];
            if (!TryParseHost(hostSlug, out var host))
                continue;
            hostExtensions.Add(new HostExtensionBlock { Host = host, Fields = AsStringMap(kv.Value) });
        }

        var schemaRaw = AsString(Lookup("schema-version"));

        return new ArtifactFrontmatter
        {
            Name = ArtifactName.From(AsString(Lookup("name"))),
            Description = Description.From(AsString(Lookup("description"))),
            License = NullIfEmpty(AsString(Lookup("license"))),
            Compatibility = NullIfEmpty(AsString(Lookup("compatibility"))),
            SchemaVersion = schemaRaw.Length > 0 ? SemVer.Parse(schemaRaw) : new SemVer(1, 0, 0),
            Metadata = AsStringMap(Lookup("metadata")),
            HostExtensions = hostExtensions,
        };
    }

    public string ComposeFrontmatter(ArtifactFrontmatter frontmatter)
    {
        var sb = new StringBuilder();
        sb.Append("name: ").Append(frontmatter.Name.Value).Append('\n');
        sb.Append("description: ").Append(Quote(frontmatter.Description.Value)).Append('\n');
        if (!string.IsNullOrEmpty(frontmatter.License))
            sb.Append("license: ").Append(Quote(frontmatter.License)).Append('\n');
        if (!string.IsNullOrEmpty(frontmatter.Compatibility))
            sb.Append("compatibility: ").Append(Quote(frontmatter.Compatibility)).Append('\n');
        sb.Append("schema-version: ").Append(frontmatter.SchemaVersion).Append('\n');

        if (frontmatter.Metadata.Count > 0)
        {
            sb.Append("metadata:\n");
            foreach (var kv in frontmatter.Metadata.OrderBy(k => k.Key, StringComparer.Ordinal))
                sb.Append("  ").Append(kv.Key).Append(": ").Append(Quote(kv.Value)).Append('\n');
        }

        foreach (var block in frontmatter.HostExtensions.OrderBy(b => b.Host))
        {
            sb.Append("x-").Append(block.Host.ToSlug()).Append(":\n");
            foreach (var kv in block.Fields.OrderBy(k => k.Key, StringComparer.Ordinal))
                sb.Append("  ").Append(kv.Key).Append(": ").Append(Quote(kv.Value)).Append('\n');
        }

        return sb.ToString();
    }

    private static bool TryParseHost(string slug, out HostName host)
    {
        try { host = HostNames.Parse(slug); return true; }
        catch (DomainException) { host = default; return false; }
    }

    private static string AsString(object? value) => value?.ToString()?.Trim() ?? string.Empty;

    private static string? NullIfEmpty(string value) => value.Length == 0 ? null : value;

    private static Dictionary<string, string> AsStringMap(object? value)
    {
        var result = new Dictionary<string, string>(StringComparer.Ordinal);
        if (value is IDictionary<object, object> dict)
            foreach (var kv in dict)
                result[AsString(kv.Key)] = AsString(kv.Value);
        return result;
    }

    private static string Quote(string value) =>
        "\"" + value.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"";
}
