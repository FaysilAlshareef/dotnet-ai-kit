using DotnetAiKit.Core.Artifacts;
using DotnetAiKit.Core.Values;

namespace DotnetAiKit.Core.Policies;

/// <summary>
/// Budget math for the always-loaded model listing. Token counts come from an external tokenizer
/// (Infrastructure <c>ITokenizer</c>); this pure policy only sums and compares (FR-029).
/// </summary>
public static class TokenBudgetPolicy
{
    /// <summary>Sum the token counts of skills that appear in the always-loaded listing.</summary>
    public static TokenBudget ListingBudget(IEnumerable<(Skill Skill, int Tokens)> skills, int limit)
    {
        var total = 0;
        foreach (var (skill, tokens) in skills)
        {
            if (skill.CountsAgainstListing)
                total += tokens;
        }

        return TokenBudget.Of(total, limit);
    }
}
