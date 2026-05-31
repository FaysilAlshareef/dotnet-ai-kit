using DotnetAiKit.Core.Artifacts;
using DotnetAiKit.Core.Manifest;
using DotnetAiKit.Core.Values;

namespace DotnetAiKit.Application.UseCases;

public sealed record CapabilityViolation(string Artifact, string Capability, HostName Host, string Reason);

/// <summary>
/// FR-012 / FR-I: validates that every artifact's declared <c>requires-capability</c> (metadata) exists
/// in the host-capability matrix and is not <c>Unsupported</c> for an enabled host without a fallback.
/// Pure; runs during generate/check. An artifact that declares no capability is trivially valid.
/// </summary>
public sealed class CapabilityValidationService
{
    public IReadOnlyList<CapabilityViolation> Validate(
        ArtifactCorpus corpus, IReadOnlyList<HostName> hosts)
    {
        var matrix = corpus.Manifest?.Capabilities ?? new HostCapabilityMatrix();
        var violations = new List<CapabilityViolation>();

        foreach (var skill in corpus.Skills)
        {
            var capability = skill.Frontmatter.MetadataValue("requires-capability");
            if (string.IsNullOrWhiteSpace(capability))
                continue;

            foreach (var host in hosts)
            {
                var maturity = matrix.Lookup(host, capability);
                if (maturity is null)
                    violations.Add(new CapabilityViolation(skill.Name.Value, capability, host, "capability not declared in the host-capability matrix"));
                else if (maturity == CapabilityMaturity.Unsupported)
                    violations.Add(new CapabilityViolation(skill.Name.Value, capability, host, "capability is Unsupported on this host (declare a fallback)"));
            }
        }

        return violations;
    }
}
