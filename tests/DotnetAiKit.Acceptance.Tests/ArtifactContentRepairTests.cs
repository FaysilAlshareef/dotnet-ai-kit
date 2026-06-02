using System.Text.RegularExpressions;
using Xunit;

namespace DotnetAiKit.Acceptance.Tests;

public sealed class ArtifactContentRepairTests
{
    [Fact]
    public void Broken_shipped_samples_are_repaired()
    {
        var minimalApi = CorpusRepairTestHelpers.ReadArtifact("skills", "api", "minimal-api-validation", "SKILL.md");
        Assert.DoesNotMatch(new Regex(@"\[Required,\s*ValidatableType\]", RegexOptions.CultureInvariant), minimalApi);
        Assert.Contains("[Experimental(\"ASP0029\")]", minimalApi);

        var configuration = CorpusRepairTestHelpers.ReadArtifact("skills", "core", "configuration", "SKILL.md");
        Assert.DoesNotContain("public sealed class MonitorService(IOptionsMonitor<DatabaseOptions> options)", configuration);

        var authJwt = CorpusRepairTestHelpers.ReadArtifact("skills", "security", "auth-jwt", "SKILL.md");
        Assert.Contains("MapInboundClaims = false", authJwt);
        Assert.DoesNotContain("User.FindFirstValue(JwtRegisteredClaimNames.Sub)!", authJwt);

        var blazorComponent = CorpusRepairTestHelpers.ReadArtifact("skills", "microservice", "controlpanel", "blazor-component", "SKILL.md");
        Assert.Contains("@inject IDialogService DialogService", blazorComponent);
        Assert.Contains("OpenEditDialog", blazorComponent);

        var gatewayFacade = CorpusRepairTestHelpers.ReadArtifact("skills", "microservice", "controlpanel", "gateway-facade", "SKILL.md");
        Assert.DoesNotContain("DeleteAsync<bool>", gatewayFacade);

        var transactionalBatch = CorpusRepairTestHelpers.ReadArtifact("skills", "microservice", "cosmos", "transactional-batch", "SKILL.md");
        Assert.Contains("ReplaceItemAsync", transactionalBatch);
        Assert.Contains("DeleteItemAsync", transactionalBatch);

        var grpcServiceDefinition = CorpusRepairTestHelpers.ReadArtifact("skills", "microservice", "grpc", "service-definition", "SKILL.md");
        Assert.DoesNotContain("(decimal)r.Total", grpcServiceDefinition);
        Assert.DoesNotContain("(decimal)i.UnitPrice", grpcServiceDefinition);
        Assert.Contains("/ 100m", grpcServiceDefinition);

        var testingPatterns = CorpusRepairTestHelpers.ReadArtifact("knowledge", "testing-patterns.md");
        Assert.DoesNotContain("OutboxMessage.EventId", testingPatterns);
        Assert.DoesNotContain("RuntimeMoniker.Net90", testingPatterns);
    }

    [Fact]
    public void Localized_serious_correctness_and_security_defects_are_repaired()
    {
        var multiTenancy = CorpusRepairTestHelpers.ReadArtifact("skills", "architecture", "multi-tenancy", "SKILL.md");
        Assert.Contains("IModelCacheKeyFactory", multiTenancy);
        Assert.Contains("public override int SaveChanges", multiTenancy);

        var emailNotifications = CorpusRepairTestHelpers.ReadArtifact("skills", "infra", "email-notifications", "SKILL.md");
        Assert.Contains("HtmlEncode", emailNotifications);

        var daprWorkflow = CorpusRepairTestHelpers.ReadArtifact("skills", "messaging", "dapr-workflow", "SKILL.md");
        Assert.Contains("TaskCanceledException", daprWorkflow);

        var circuitBreaker = CorpusRepairTestHelpers.ReadArtifact("skills", "resilience", "circuit-breaker", "SKILL.md");
        Assert.Contains("CircuitBreakerStateProvider", circuitBreaker);

        var changelogGen = CorpusRepairTestHelpers.ReadArtifact("skills", "docs", "changelog-gen", "SKILL.md");
        Assert.Contains("--pretty=format:%s", changelogGen);

        var hostedService = CorpusRepairTestHelpers.ReadArtifact("skills", "microservice", "processor", "hosted-service", "SKILL.md");
        Assert.Contains("await _processor.StartProcessingAsync", hostedService);
        Assert.Contains("await _processor.CloseAsync", hostedService);

        var listenerPattern = CorpusRepairTestHelpers.ReadArtifact("skills", "microservice", "query", "listener-pattern", "SKILL.md");
        Assert.Contains("await _processor.StartProcessingAsync", listenerPattern);
        Assert.Contains("Task.FromResult(true)", listenerPattern);

        var cosmosEntity = CorpusRepairTestHelpers.ReadArtifact("skills", "microservice", "cosmos", "cosmos-entity", "SKILL.md");
        Assert.DoesNotContain("CreatedAt.ToString(\"yyyy-MM\")", cosmosEntity);

        var integrationTesting = CorpusRepairTestHelpers.ReadArtifact("skills", "testing", "integration-testing", "SKILL.md");
        Assert.DoesNotContain("UseInMemoryDatabase(\"TestDb_", integrationTesting);
        Assert.DoesNotContain(": WebApplicationFactory<Program>, IClassFixture<SqlServerFixture>", integrationTesting);

        var testFixtures = CorpusRepairTestHelpers.ReadArtifact("skills", "testing", "test-fixtures", "SKILL.md");
        Assert.Contains("CancellationToken cancellationToken = default", testFixtures);

        var outbox = CorpusRepairTestHelpers.ReadArtifact("skills", "microservice", "command", "outbox", "SKILL.md");
        Assert.DoesNotContain("GeOutboxMessageAsync", outbox);
        Assert.Contains("CancellationToken cancellationToken", outbox);

        var mudblazor = CorpusRepairTestHelpers.ReadArtifact("skills", "microservice", "controlpanel", "mudblazor-patterns", "SKILL.md");
        Assert.Contains("SwitchAsync", mudblazor);

        var eventSourcing = CorpusRepairTestHelpers.ReadArtifact("knowledge", "event-sourcing-flow.md");
        Assert.DoesNotContain("Task.Run(PublishNonPublishedMessages)", eventSourcing);
        Assert.DoesNotContain("lockedScopes", eventSourcing);

        var outboxPattern = CorpusRepairTestHelpers.ReadArtifact("knowledge", "outbox-pattern.md");
        Assert.DoesNotContain("Task.Run(PublishNonPublishedMessages)", outboxPattern);
        Assert.DoesNotContain("lockedScopes", outboxPattern);
    }

    [Fact]
    public void Touched_testing_guidance_uses_net10_runtime_moniker()
    {
        var testingPatterns = CorpusRepairTestHelpers.ReadArtifact("knowledge", "testing-patterns.md");
        var performanceTesting = CorpusRepairTestHelpers.ReadArtifact("skills", "testing", "performance-testing", "SKILL.md");

        Assert.DoesNotContain("RuntimeMoniker.Net90", testingPatterns);
        Assert.DoesNotContain("RuntimeMoniker.Net90", performanceTesting);
        Assert.Contains("RuntimeMoniker.Net10_0", testingPatterns + performanceTesting);
    }
}
