using DotnetAiKit.Application.Ports;

namespace DotnetAiKit.Application.UseCases;

public sealed record GenerateResult(
    bool Ok, IReadOnlyList<string> Errors, IReadOnlyList<string> Drifts, int FilesWritten)
{
    public static GenerateResult Failed(IReadOnlyList<string> errors) => new(false, errors, [], 0);
}

/// <summary>
/// Build-time projection: load the authored corpus, project it to every host, and either write the
/// outputs under <c>build/</c> or (check mode) report drift against the committed outputs (SC-001).
/// Fails fast on load/graph errors; deterministic + idempotent (FR-009/011).
/// </summary>
public sealed class GenerateService(IArtifactRepository repository, IProjectionEngine engine, IFileSystem fileSystem)
{
    public GenerateResult Run(string artifactsRoot, string outputRoot, bool checkOnly)
    {
        var load = repository.Load(artifactsRoot);
        if (!load.Ok || load.Corpus is null)
            return GenerateResult.Failed(load.Errors);

        var files = engine.ProjectAll(load.Corpus);

        if (checkOnly)
        {
            var drifts = new List<string>();
            foreach (var file in files)
            {
                var path = Path.Combine(outputRoot, file.RelativePath);
                var current = fileSystem.FileExists(path) ? Normalize(fileSystem.ReadAllText(path)) : null;
                if (current != Normalize(file.Content))
                    drifts.Add(file.RelativePath);
            }

            return new GenerateResult(drifts.Count == 0, [], drifts, 0);
        }

        foreach (var file in files)
            fileSystem.WriteAllText(Path.Combine(outputRoot, file.RelativePath), file.Content);

        return new GenerateResult(true, [], [], files.Count);
    }

    private static string Normalize(string content) => content.Replace("\r\n", "\n");
}
