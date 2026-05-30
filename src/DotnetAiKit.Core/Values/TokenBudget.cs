namespace DotnetAiKit.Core.Values;

/// <summary>A token count measured against a budget limit.</summary>
public readonly record struct TokenBudget
{
    public int Tokens { get; }
    public int Limit { get; }

    private TokenBudget(int tokens, int limit)
    {
        Tokens = tokens;
        Limit = limit;
    }

    public static TokenBudget Of(int tokens, int limit)
    {
        if (tokens < 0)
            throw new DomainException("Token count must be non-negative.");
        if (limit < 0)
            throw new DomainException("Token limit must be non-negative.");
        return new TokenBudget(tokens, limit);
    }

    public bool IsWithin => Tokens <= Limit;

    public int Overflow => Math.Max(0, Tokens - Limit);
}
