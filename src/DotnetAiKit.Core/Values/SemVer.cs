namespace DotnetAiKit.Core.Values;

/// <summary>A minimal MAJOR.MINOR.PATCH semantic version.</summary>
public readonly record struct SemVer(int Major, int Minor, int Patch) : IComparable<SemVer>
{
    public static SemVer Parse(string raw)
    {
        ArgumentNullException.ThrowIfNull(raw);
        var parts = raw.Trim().Split('.');
        if (parts.Length != 3
            || !int.TryParse(parts[0], out var major)
            || !int.TryParse(parts[1], out var minor)
            || !int.TryParse(parts[2], out var patch)
            || major < 0 || minor < 0 || patch < 0)
        {
            throw new DomainException($"Invalid semantic version '{raw}'. Expected MAJOR.MINOR.PATCH.");
        }
        return new SemVer(major, minor, patch);
    }

    public int CompareTo(SemVer other)
    {
        var c = Major.CompareTo(other.Major);
        if (c != 0) return c;
        c = Minor.CompareTo(other.Minor);
        return c != 0 ? c : Patch.CompareTo(other.Patch);
    }

    public static bool operator <(SemVer a, SemVer b) => a.CompareTo(b) < 0;

    public static bool operator >(SemVer a, SemVer b) => a.CompareTo(b) > 0;

    public static bool operator <=(SemVer a, SemVer b) => a.CompareTo(b) <= 0;

    public static bool operator >=(SemVer a, SemVer b) => a.CompareTo(b) >= 0;

    public override string ToString() => $"{Major}.{Minor}.{Patch}";
}
