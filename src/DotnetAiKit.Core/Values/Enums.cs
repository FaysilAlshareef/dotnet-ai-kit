namespace DotnetAiKit.Core.Values;

/// <summary>The four supported AI coding assistants (projection targets).</summary>
public enum HostName { Claude, Codex, Cursor, Copilot }

/// <summary>Whether a skill is auto-fireable knowledge or a user-invoked command.</summary>
public enum SkillKind { Knowledge, Command }

/// <summary>A rule applies everywhere (always loaded) or only to a path scope (JIT).</summary>
public enum RuleScope { Universal, Domain }

/// <summary>Model/user invocation policy — the token-budget lever.</summary>
public enum InvocationPolicy
{
    /// <summary>User- and model-invocable, appears in the always-loaded listing (costs budget).</summary>
    Default,

    /// <summary>User-invocable only, off the always-loaded listing (side-effecting commands).</summary>
    DisableModelInvocation,

    /// <summary>Model-invocable background knowledge, not user-listed.</summary>
    UserInvocableFalse,
}

/// <summary>The distinct artifact types (the projection decides each host's surface).</summary>
public enum ArtifactKind { Skill, Agent, Rule, Profile, Fragment, Knowledge, Command }

/// <summary>Edges in the artifact graph.</summary>
public enum EdgeKind { OwnedBy, RelatesTo, TriggeredBy, EnforcedBy }

/// <summary>Maturity tag for a host capability.</summary>
public enum CapabilityMaturity { Ga, Preview, Experimental, Unsupported }

/// <summary>Parsing/formatting helpers for <see cref="HostName"/>.</summary>
public static class HostNames
{
    public static IReadOnlyList<HostName> All { get; } =
        [HostName.Claude, HostName.Codex, HostName.Cursor, HostName.Copilot];

    public static string ToSlug(this HostName host) => host switch
    {
        HostName.Claude => "claude",
        HostName.Codex => "codex",
        HostName.Cursor => "cursor",
        HostName.Copilot => "copilot",
        _ => throw new DomainException($"Unknown host: {host}"),
    };

    public static HostName Parse(string raw)
    {
        ArgumentNullException.ThrowIfNull(raw);
        return raw.Trim().ToLowerInvariant() switch
        {
            "claude" => HostName.Claude,
            "codex" => HostName.Codex,
            "cursor" => HostName.Cursor,
            "copilot" => HostName.Copilot,
            _ => throw new DomainException($"Unknown host name '{raw}'. Expected: claude|codex|cursor|copilot."),
        };
    }
}
