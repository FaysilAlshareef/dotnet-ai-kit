namespace DotnetAiKit.Core.Values;

/// <summary>A non-empty path glob, normalized to forward slashes (cross-platform).</summary>
public readonly record struct Glob
{
    public string Value { get; }

    private Glob(string value) => Value = value;

    public static Glob From(string raw)
    {
        var value = (raw ?? string.Empty).Trim().Replace('\\', '/');
        if (value.Length == 0)
            throw new DomainException("Glob pattern must not be empty.");
        return new Glob(value);
    }

    public override string ToString() => Value;
}
