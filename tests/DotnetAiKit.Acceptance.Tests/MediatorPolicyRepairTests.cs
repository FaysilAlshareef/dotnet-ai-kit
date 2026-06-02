using Xunit;

namespace DotnetAiKit.Acceptance.Tests;

public sealed class MediatorPolicyRepairTests
{
    private static readonly string[][] TierADefaultFiles =
    [
        ["skills", "cqrs", "mediatr-handlers", "SKILL.md"],
        ["skills", "core", "dependency-injection", "SKILL.md"],
        ["skills", "core", "design-patterns", "SKILL.md"],
        ["skills", "core", "solid-principles", "SKILL.md"],
        ["skills", "data", "db-transactions", "SKILL.md"],
        ["skills", "cqrs", "command-generator", "SKILL.md"],
        ["skills", "cqrs", "pipeline-behaviors", "SKILL.md"],
        ["skills", "cqrs", "query-generator", "SKILL.md"],
        ["skills", "cqrs", "request-response", "SKILL.md"],
        ["skills", "architecture", "clean-architecture", "SKILL.md"],
        ["skills", "architecture", "modular-monolith", "SKILL.md"],
        ["skills", "architecture", "vertical-slice", "SKILL.md"],
        ["skills", "api", "caching-strategies", "SKILL.md"],
        ["skills", "api", "controller-patterns", "SKILL.md"],
        ["skills", "microservice", "command", "command-handler", "SKILL.md"]
    ];

    [Fact]
    public void Domain_event_guidance_does_not_depend_on_mediatr_contracts()
    {
        var ddd = CorpusRepairTestHelpers.ReadArtifact("skills", "architecture", "ddd-patterns", "SKILL.md");
        var notifications = CorpusRepairTestHelpers.ReadArtifact("skills", "cqrs", "notification-handlers", "SKILL.md");

        Assert.DoesNotContain("IDomainEvent : INotification", ddd);
        Assert.DoesNotContain("IDomainEvent : INotification", notifications);
        Assert.DoesNotContain("public interface IDomainEvent : INotification", ddd);
        Assert.DoesNotContain("public interface IDomainEvent : INotification", notifications);
    }

    [Fact]
    public void Tier_a_default_guidance_frames_mediatr_as_opt_in_or_abstracted()
    {
        foreach (var path in TierADefaultFiles)
        {
            var content = CorpusRepairTestHelpers.ReadArtifact(path);
            var hasMediatrDefault =
                content.Contains("Install MediatR", StringComparison.OrdinalIgnoreCase)
                || content.Contains("AddMediatR", StringComparison.Ordinal)
                || content.Contains("MediatR handlers", StringComparison.OrdinalIgnoreCase);
            var hasPolicy =
                content.Contains("project-owned sender port", StringComparison.OrdinalIgnoreCase)
                || content.Contains("MediatR is opt-in", StringComparison.OrdinalIgnoreCase)
                || content.Contains("mediator-abstraction", StringComparison.OrdinalIgnoreCase);

            Assert.False(
                hasMediatrDefault && !hasPolicy,
                string.Join("/", path) + " names MediatR as default without the license-safe policy.");
        }
    }

    [Fact]
    public void Agents_rule_and_knowledge_name_the_license_safe_default()
    {
        string[][] paths =
        [
            ["agents", "ef-specialist.md"],
            ["agents", "processor-architect.md"],
            ["rules", "domain", "architecture.md"],
            ["knowledge", "cqrs-patterns.md"],
            ["knowledge", "event-sourcing-flow.md"]
        ];

        foreach (var path in paths)
        {
            var content = CorpusRepairTestHelpers.ReadArtifact(path);
            Assert.Contains("project-owned sender port", content, StringComparison.OrdinalIgnoreCase);
        }
    }
}
