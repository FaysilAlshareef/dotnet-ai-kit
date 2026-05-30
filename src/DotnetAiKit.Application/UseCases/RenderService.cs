using DotnetAiKit.Application.Ports;
using DotnetAiKit.Core.Policies;

namespace DotnetAiKit.Application.UseCases;

public sealed record RenderResult(bool Ok, string? Body, IReadOnlyList<string> Errors, IReadOnlyList<string> UnresolvedTokens);

/// <summary>
/// Resolves a skill or rule and substitutes the detected project metadata into its body (FR-019,
/// token replacement only — FR-005). Reports any unresolved tokens.
/// </summary>
public sealed class RenderService(IArtifactRepository repository, IDetectionProvider detector)
{
    public RenderResult Render(string artifactsRoot, string kind, string name, string projectRoot)
    {
        var load = repository.Load(artifactsRoot);
        if (!load.Ok || load.Corpus is null)
            return new RenderResult(false, null, load.Errors, []);

        var body = kind.ToLowerInvariant() switch
        {
            "skill" => load.Corpus.Skills.FirstOrDefault(s => s.Name.Value == name)?.Body,
            "rule" => load.Corpus.Rules.FirstOrDefault(r => r.Name.Value == name)?.Body,
            _ => null,
        };

        if (body is null)
            return new RenderResult(false, null, [$"{kind} '{name}' not found."], []);

        var tokens = detector.Detect(projectRoot).ToTokenMap();
        var rendered = SubstitutionEngine.Render(body, tokens);
        return new RenderResult(true, rendered, [], SubstitutionEngine.FindUnresolved(rendered));
    }
}
