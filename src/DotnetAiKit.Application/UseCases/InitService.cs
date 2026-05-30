using DotnetAiKit.Application.Ports;

namespace DotnetAiKit.Application.UseCases;

public sealed record InitResult(bool Ok, IReadOnlyList<string> Errors, HostWriteResult? Write)
{
    public static InitResult Failed(IReadOnlyList<string> errors) => new(false, errors, null);
}

/// <summary>
/// Initializes the per-solution footprint for a host: detect project metadata, load the corpus,
/// and write the small bounded set — including <c>.claude/rules/*.md</c> with <c>paths:</c>, the v1
/// rule-delivery fix (FR-017/FR-019, SC-002/SC-011).
/// </summary>
public sealed class InitService(
    IDetectionProvider detector, IArtifactRepository repository, IHostAdapter hostAdapter)
{
    public InitResult Run(string solutionRoot, string artifactsRoot, bool dryRun)
    {
        var load = repository.Load(artifactsRoot);
        if (!load.Ok || load.Corpus is null)
            return InitResult.Failed(load.Errors);

        var metadata = detector.Detect(solutionRoot);
        var write = hostAdapter.WritePerSolution(solutionRoot, load.Corpus, metadata, dryRun);
        return new InitResult(true, [], write);
    }
}
