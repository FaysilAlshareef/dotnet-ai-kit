using System.Text.RegularExpressions;

namespace DotnetAiKit.Application.UseCases;

/// <summary>A rule visible to the PreToolUse hook: its path globs (empty ⇒ universal) and its body.</summary>
public sealed record HookRule(IReadOnlyList<string> Globs, string Body);

/// <summary>
/// The PreToolUse decision. A non-null <see cref="DenyReason"/> blocks the edit (T2); a non-null
/// <see cref="AdditionalContext"/> is injected into the model's context (T1). Both may be null (allow, no-op).
/// </summary>
public sealed record PreToolUseDecision(string? DenyReason, string? AdditionalContext)
{
    public static readonly PreToolUseDecision None = new(null, null);
}

/// <summary>
/// Pure decision logic for the Claude PreToolUse hook (planning/24 tiers T1+T2, Claude-scoped). On a
/// Write/Edit: (T2) deny edits to generated/output files that the build overwrites; (T1) inject the
/// active rule bodies — universal rules always, domain rules when the edited path matches their globs —
/// which is the runtime delivery half of the v1 rule-delivery fix. No I/O: the hook command supplies the
/// rules + path, so this stays deterministic and unit-testable.
/// </summary>
public static class PreToolUseHookService
{
    public static PreToolUseDecision Decide(string? filePath, IReadOnlyList<HookRule> rules)
    {
        var rel = (filePath ?? string.Empty).Replace('\\', '/').Trim();
        if (rel.Length == 0)
            return PreToolUseDecision.None;

        // T2 — deny hand-edits to generated / build-output files (regenerated; edits would be lost).
        if (IsGeneratedArtifact(rel))
            return new PreToolUseDecision(
                $"'{filePath}' is a generated/build-output file (obj/, bin/, *.g.cs, *.Designer.cs, "
                    + "*.AssemblyInfo.cs) and is overwritten by the build. Edit the source instead.",
                null);

        // T1 — inject universal rule bodies (no globs) + domain rules whose globs match the path.
        var parts = new List<string>();
        foreach (var rule in rules)
        {
            var applies = rule.Globs.Count == 0 || rule.Globs.Any(g => Matches(rel, g));
            if (applies && rule.Body.Trim().Length > 0)
                parts.Add(rule.Body.Trim());
        }

        return parts.Count == 0
            ? PreToolUseDecision.None
            : new PreToolUseDecision(null, string.Join("\n\n", parts));
    }

    private static bool IsGeneratedArtifact(string rel) =>
        rel == "obj" || rel == "bin"
        || rel.StartsWith("obj/", StringComparison.Ordinal) || rel.Contains("/obj/", StringComparison.Ordinal)
        || rel.StartsWith("bin/", StringComparison.Ordinal) || rel.Contains("/bin/", StringComparison.Ordinal)
        || rel.EndsWith(".g.cs", StringComparison.Ordinal) || rel.EndsWith(".g.i.cs", StringComparison.Ordinal)
        || rel.EndsWith(".Designer.cs", StringComparison.Ordinal)
        || rel.EndsWith(".AssemblyInfo.cs", StringComparison.Ordinal);

    /// <summary>Minimal, deterministic glob match (**, *, ?) on the full path or the basename.</summary>
    public static bool Matches(string rel, string glob)
    {
        var g = (glob ?? string.Empty).Replace('\\', '/').Trim();
        if (g.Length == 0)
            return false;

        if (Regex.IsMatch(rel, ToRegex(g)))
            return true;

        // A basename-only pattern (e.g. "*.cs") also matches a file anywhere by its name. Patterns that
        // carry directory structure (e.g. "**/Endpoints/**/*.cs") must match the full path only.
        if (g.Contains('/'))
            return false;

        var name = rel.Contains('/') ? rel[(rel.LastIndexOf('/') + 1)..] : rel;
        return Regex.IsMatch(name, ToRegex(g));
    }

    private static string ToRegex(string glob) =>
        "^" + Regex.Escape(glob)
            .Replace(@"\*\*/", ".*")
            .Replace(@"\*\*", ".*")
            .Replace(@"\*", "[^/]*")
            .Replace(@"\?", ".") + "$";
}
