using System.Text;

namespace DotnetAiKit.Hosts;

/// <summary>Builds deterministic YAML frontmatter (fixed field order, LF, double-quoted scalars).</summary>
internal sealed class FrontmatterWriter
{
    private readonly StringBuilder _sb = new();

    public FrontmatterWriter Scalar(string key, string value)
    {
        _sb.Append(key).Append(": ").Append(value).Append('\n');
        return this;
    }

    public FrontmatterWriter Quoted(string key, string value)
    {
        _sb.Append(key).Append(": ").Append(Quote(value)).Append('\n');
        return this;
    }

    public FrontmatterWriter Flag(string key, bool? value)
    {
        if (value is { } b)
            _sb.Append(key).Append(": ").Append(b ? "true" : "false").Append('\n');
        return this;
    }

    public FrontmatterWriter List(string key, IEnumerable<string> values)
    {
        var list = values.ToList();
        if (list.Count == 0)
            return this;
        _sb.Append(key).Append(":\n");
        foreach (var v in list)
            _sb.Append("  - ").Append(Quote(v)).Append('\n');
        return this;
    }

    public string Compose(string body)
    {
        var sb = new StringBuilder();
        sb.Append("---\n").Append(_sb).Append("---\n").Append(body);
        if (body.Length == 0 || body[^1] != '\n')
            sb.Append('\n');
        return sb.ToString();
    }

    public static string Quote(string value) =>
        "\"" + value.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"";
}
