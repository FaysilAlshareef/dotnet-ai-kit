using DotnetAiKit.Application.UseCases;
using DotnetAiKit.Infrastructure;
using Xunit;

namespace DotnetAiKit.Application.Tests;

public sealed class VerbServicesTests : IDisposable
{
    private readonly string _root = Path.Combine(Path.GetTempPath(), "dak-verbs-" + Guid.NewGuid().ToString("N"));
    private readonly PhysicalFileSystem _fs = new();

    public void Dispose()
    {
        if (Directory.Exists(_root))
            Directory.Delete(_root, recursive: true);
    }

    [Fact]
    public void Migrate_rewrites_legacy_ai_tools_alias_and_backs_up()
    {
        var configPath = Path.Combine(_root, ".dotnet-ai-kit", "config.yml");
        _fs.WriteAllText(configPath, "ai_tools:\n  - claude\npermission_profile: standard\n");

        var result = new MigrateService(_fs, new BackupRotationService(_fs)).Run(_root, keep: 3, dryRun: false);

        Assert.True(result.Ok);
        Assert.Single(result.Migrated);
        Assert.Contains("enabled_hosts:", _fs.ReadAllText(configPath), StringComparison.Ordinal);
        Assert.DoesNotContain("ai_tools:", _fs.ReadAllText(configPath), StringComparison.Ordinal);
        Assert.True(_fs.FileExists(configPath + ".bak.1"), "a rotated backup was not created");
    }

    [Fact]
    public void Migrate_is_noop_when_no_legacy_key()
    {
        var configPath = Path.Combine(_root, ".dotnet-ai-kit", "config.yml");
        _fs.WriteAllText(configPath, "enabled_hosts:\n  - claude\n");

        var result = new MigrateService(_fs, new BackupRotationService(_fs)).Run(_root, keep: 3, dryRun: false);

        Assert.Empty(result.Migrated);
    }

    [Fact]
    public void Configure_sets_a_key_creating_or_replacing()
    {
        var configPath = Path.Combine(_root, ".dotnet-ai-kit", "config.yml");
        _fs.WriteAllText(configPath, "permission_profile: standard\n");

        var service = new ConfigureService(_fs);
        service.Set(_root, "permission_profile", "full", dryRun: false);
        service.Set(_root, "retention", "5", dryRun: false);

        var content = _fs.ReadAllText(configPath);
        Assert.Contains("permission_profile: full", content, StringComparison.Ordinal);
        Assert.Contains("retention: 5", content, StringComparison.Ordinal);
        Assert.DoesNotContain("standard", content, StringComparison.Ordinal);
    }

    [Fact]
    public void Configure_dry_run_writes_nothing()
    {
        var configPath = Path.Combine(_root, ".dotnet-ai-kit", "config.yml");
        var result = new ConfigureService(_fs).Set(_root, "k", "v", dryRun: true);

        Assert.True(result.Ok);
        Assert.False(_fs.FileExists(configPath));
    }

    [Fact]
    public void Upgrade_is_noop_for_plugin_native_and_copilot_aware()
    {
        Assert.Contains("No-op", new UpgradeService().Run(copilotOnly: false).Message, StringComparison.Ordinal);
        Assert.Contains("Copilot", new UpgradeService().Run(copilotOnly: true).Message, StringComparison.Ordinal);
    }
}
