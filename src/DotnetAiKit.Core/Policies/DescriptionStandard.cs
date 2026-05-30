using DotnetAiKit.Core.Values;

namespace DotnetAiKit.Core.Policies;

/// <summary>
/// Validates an artifact description against the description standard (FR-026):
/// action-verb-first / third person, an explicit "Use when…" trigger, an explicit negative
/// scope ("Do NOT use… use X"), within the character cap. Pure + deterministic (CI-gated).
/// </summary>
public static class DescriptionStandard
{
    public static IReadOnlyList<string> Validate(string description)
    {
        var d = (description ?? string.Empty).Trim();
        var violations = new List<string>();

        if (d.Length == 0)
        {
            violations.Add("Description is empty.");
            return violations;
        }

        if (d.Length > Description.MaxLength)
            violations.Add($"Description exceeds {Description.MaxLength} characters ({d.Length}).");

        if (!char.IsUpper(d[0]))
            violations.Add("Description must start with a capitalized action verb (e.g. \"Generates…\").");

        if (d.IndexOf("use when", StringComparison.OrdinalIgnoreCase) < 0)
            violations.Add("Description must contain an explicit \"Use when…\" trigger.");

        var hasNegative =
            d.IndexOf("do not use", StringComparison.OrdinalIgnoreCase) >= 0
            || d.IndexOf("don't use", StringComparison.OrdinalIgnoreCase) >= 0
            || d.IndexOf("do NOT use", StringComparison.Ordinal) >= 0;
        if (!hasNegative)
            violations.Add("Description must name an explicit negative scope (\"Do NOT use… use X instead\").");

        return violations;
    }

    public static bool IsValid(string description) => Validate(description).Count == 0;
}
