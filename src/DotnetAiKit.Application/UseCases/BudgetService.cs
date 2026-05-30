using DotnetAiKit.Application.Ports;
using DotnetAiKit.Core.Policies;

namespace DotnetAiKit.Application.UseCases;

public sealed record BudgetReport(
    int ListingTokens, int Limit, bool Within, int ModelInvocableSkills, int CommandsOffListing);

/// <summary>
/// Measures the always-loaded model listing against the token budget (FR-029, SC-006): sums the
/// description tokens of skills that count against the listing; command-skills are off-listing.
/// CI fails when the listing exceeds the limit. No network (local tokenizer).
/// </summary>
public sealed class BudgetService(IArtifactRepository repository, ITokenizer tokenizer)
{
    public BudgetReport Measure(string artifactsRoot, int limit)
    {
        var load = repository.Load(artifactsRoot);
        if (load.Corpus is null)
            return new BudgetReport(0, limit, true, 0, 0);

        var counted = load.Corpus.Skills.Select(s => (Skill: s, Tokens: tokenizer.CountTokens(s.Description.Value))).ToList();
        var budget = TokenBudgetPolicy.ListingBudget(counted, limit);

        var modelInvocable = load.Corpus.Skills.Count(s => s.CountsAgainstListing);
        var commandsOff = load.Corpus.Skills.Count(s => !s.CountsAgainstListing);
        return new BudgetReport(budget.Tokens, limit, budget.IsWithin, modelInvocable, commandsOff);
    }
}
