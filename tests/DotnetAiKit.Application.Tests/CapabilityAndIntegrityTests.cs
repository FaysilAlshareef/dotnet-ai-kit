using DotnetAiKit.Application.UseCases;
using DotnetAiKit.Core.Artifacts;
using DotnetAiKit.Core.Frontmatter;
using DotnetAiKit.Core.Manifest;
using DotnetAiKit.Core.Values;
using DotnetAiKit.Infrastructure;
using Xunit;

namespace DotnetAiKit.Application.Tests;

public class CapabilityAndIntegrityTests
{
    private static Skill SkillRequiring(string name, string? capability)
    {
        var meta = capability is null
            ? new Dictionary<string, string>()
            : new Dictionary<string, string> { ["requires-capability"] = capability };
        var desc = Description.From("Does a thing. Use when X. Do NOT use for Y (use z).");
        return new Skill
        {
            Name = ArtifactName.From(name),
            Description = desc,
            Frontmatter = new ArtifactFrontmatter { Name = ArtifactName.From(name), Description = desc, Metadata = meta },
        };
    }

    private static ArtifactCorpus CorpusWith(params Skill[] skills) => new()
    {
        Skills = skills,
        Manifest = new PluginManifest
        {
            Name = "k",
            Version = new SemVer(2, 0, 0),
            Capabilities = new HostCapabilityMatrix
            {
                Entries =
                [
                    new(HostName.Claude, "stop-hook", CapabilityMaturity.Ga),
                    new(HostName.Codex, "stop-hook", CapabilityMaturity.Unsupported),
                ],
            },
        },
    };

    [Fact]
    public void Capability_unsupported_on_a_host_is_a_violation()
    {
        var violations = new CapabilityValidationService()
            .Validate(CorpusWith(SkillRequiring("needs-gate", "stop-hook")), [HostName.Claude, HostName.Codex]);
        Assert.Contains(violations, v => v.Host == HostName.Codex && v.Capability == "stop-hook");
        Assert.DoesNotContain(violations, v => v.Host == HostName.Claude);
    }

    [Fact]
    public void Capability_not_in_matrix_is_a_violation()
    {
        var violations = new CapabilityValidationService()
            .Validate(CorpusWith(SkillRequiring("needs-ghost", "ghost-cap")), [HostName.Claude]);
        Assert.Contains(violations, v => v.Capability == "ghost-cap");
    }

    [Fact]
    public void Skill_without_a_declared_capability_is_clean()
    {
        var violations = new CapabilityValidationService()
            .Validate(CorpusWith(SkillRequiring("plain", null)), HostNames.All);
        Assert.Empty(violations);
    }

    [Fact]
    public void Manifest_sha256_is_stable_and_verifies()
    {
        var svc = new ManifestIntegrityService();
        var hash = svc.ComputeSha256("name: k\nversion: 2.0.0\n");
        Assert.Equal(hash, svc.ComputeSha256("name: k\r\nversion: 2.0.0\r\n")); // newline-normalized
        Assert.True(svc.Verify("name: k\nversion: 2.0.0\n", hash));
        Assert.False(svc.Verify("tampered", hash));
    }

    [Fact]
    public void Footprint_manifest_hash_verifies_stable_fields()
    {
        var svc = new ManifestIntegrityService();
        var hash = svc.ComputeFootprintSha256("claude", 21);
        var manifest = "{\n  \"host\": \"claude\",\n  \"rules\": 21,\n  \"sha256\": \"" + hash + "\"\n}\n";

        Assert.True(svc.TryVerifyFootprintManifest(manifest, out var details));
        Assert.Equal(string.Empty, details);

        var tampered = manifest.Replace("\"rules\": 21", "\"rules\": 22", StringComparison.Ordinal);
        Assert.False(svc.TryVerifyFootprintManifest(tampered, out details));
        Assert.Contains("manifest hash mismatch", details);
    }
}
