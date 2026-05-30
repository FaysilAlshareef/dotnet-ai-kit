using System.Text.RegularExpressions;

namespace DotnetAiKit.Core.Policies;

/// <summary>
/// Project-metadata token substitution: <c>${Company}</c>, <c>${detected_paths.entities}</c>, …
/// Regex token replacement over a metadata dictionary — NOT a template engine (FR-005).
/// Unknown tokens are left intact so <see cref="FindUnresolved"/> can flag them.
/// </summary>
public static partial class SubstitutionEngine
{
    [GeneratedRegex(@"\$\{([^}]+)\}", RegexOptions.CultureInvariant)]
    private static partial Regex TokenRegex();

    public static string Render(string template, IReadOnlyDictionary<string, string> values)
    {
        if (string.IsNullOrEmpty(template))
            return template ?? string.Empty;

        return TokenRegex().Replace(template, match =>
        {
            var key = match.Groups[1].Value.Trim();
            return values.TryGetValue(key, out var replacement) ? replacement : match.Value;
        });
    }

    /// <summary>Distinct unresolved token keys remaining in already-rendered text.</summary>
    public static IReadOnlyList<string> FindUnresolved(string rendered)
    {
        if (string.IsNullOrEmpty(rendered))
            return [];

        var keys = new List<string>();
        var seen = new HashSet<string>(StringComparer.Ordinal);
        foreach (Match m in TokenRegex().Matches(rendered))
        {
            var key = m.Groups[1].Value.Trim();
            if (seen.Add(key))
                keys.Add(key);
        }

        return keys;
    }
}
