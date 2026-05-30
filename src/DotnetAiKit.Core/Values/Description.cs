namespace DotnetAiKit.Core.Values;

/// <summary>
/// A validated artifact description: non-empty, ≤1536 chars (the hard cap).
/// The richer "description standard" shape (action-verb-first, "Use when", negative scope)
/// is checked by <see cref="DotnetAiKit.Core.Policies.DescriptionStandard"/>, not here, so
/// construction stays cheap.
/// </summary>
public readonly record struct Description
{
    public const int MaxLength = 1536;
    public const int PortableLength = 1024;

    public string Value { get; }

    private Description(string value) => Value = value;

    public static Description From(string raw)
    {
        var value = (raw ?? string.Empty).Trim();
        if (value.Length == 0)
            throw new DomainException("Description must not be empty.");
        if (value.Length > MaxLength)
            throw new DomainException($"Description exceeds {MaxLength} characters ({value.Length}).");
        return new Description(value);
    }

    public bool ExceedsPortableLength => Value.Length > PortableLength;

    public override string ToString() => Value;
}
