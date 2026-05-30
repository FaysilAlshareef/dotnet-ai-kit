namespace DotnetAiKit.Core.Values;

/// <summary>
/// A validated artifact name: lowercase-kebab, ≤64 chars, no leading/trailing/double hyphen.
/// Must equal the artifact's directory/file name (checked by the repository at load time).
/// </summary>
public readonly record struct ArtifactName
{
    public const int MaxLength = 64;

    public string Value { get; }

    private ArtifactName(string value) => Value = value;

    public static ArtifactName From(string raw)
    {
        var value = (raw ?? string.Empty).Trim();
        if (value.Length == 0)
            throw new DomainException("Artifact name must not be empty.");
        if (value.Length > MaxLength)
            throw new DomainException($"Artifact name '{value}' exceeds {MaxLength} characters.");
        if (!IsKebab(value))
            throw new DomainException(
                $"Artifact name '{value}' must be lowercase-kebab (a-z, 0-9, hyphen) with no leading/trailing/double hyphen.");
        return new ArtifactName(value);
    }

    public static bool TryFrom(string raw, out ArtifactName name)
    {
        try { name = From(raw); return true; }
        catch (DomainException) { name = default; return false; }
    }

    private static bool IsKebab(string value)
    {
        if (value[0] == '-' || value[^1] == '-')
            return false;
        var prevHyphen = false;
        foreach (var c in value)
        {
            var ok = c is (>= 'a' and <= 'z') or (>= '0' and <= '9') or '-';
            if (!ok)
                return false;
            if (c == '-')
            {
                if (prevHyphen)
                    return false;
                prevHyphen = true;
            }
            else
            {
                prevHyphen = false;
            }
        }
        return true;
    }

    public override string ToString() => Value;
}
