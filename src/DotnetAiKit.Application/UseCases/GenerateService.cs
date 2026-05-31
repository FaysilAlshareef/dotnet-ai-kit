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
/// Orphaned outputs (files no longer produced) are deleted in write mode and reported in check mode,
/// so <c>build/</c> exactly matches the corpus. Fails fast on load/graph errors; deterministic (FR-009/011).
/// </summary>
public sealed class GenerateService(IArtifactRepository repository, IProjectionEngine engine, IFileSystem fileSystem)
{
    public GenerateResult Run(string artifactsRoot, string outputRoot, bool checkOnly)
    {
        var load = repository.Load(artifactsRoot);
        if (!load.Ok || load.Corpus is null)
            return GenerateResult.Failed(load.Errors);

        // FR-012: fail generation if any artifact declares a capability the matrix can't honor.
        var capabilityViolations = new CapabilityValidationService()
            .Validate(load.Corpus, Core.Values.HostNames.All);
        if (capabilityViolations.Count > 0)
            return GenerateResult.Failed(
                capabilityViolations.Select(v => $"{v.Artifact}: capability '{v.Capability}' on {v.Host} — {v.Reason}").ToList());

        var files = engine.ProjectAll(load.Corpus);
        var expected = files.Select(f => NormalizePath(f.RelativePath)).ToHashSet(StringComparer.OrdinalIgnoreCase);

        if (checkOnly)
        {
            var drifts = new List<string>();
            foreach (var file in files)
            {
                var path = Path.Combine(outputRoot, file.RelativePath);
                var current = fileSystem.FileExists(path) ? NormalizeContent(fileSystem.ReadAllText(path)) : null;
                if (current != NormalizeContent(file.Content))
                    drifts.Add(file.RelativePath);
            }

            foreach (var orphan in Orphans(outputRoot, expected))
                drifts.Add($"{orphan} (orphan)");

            return new GenerateResult(drifts.Count == 0, [], drifts, 0);
        }

        foreach (var file in files)
            fileSystem.WriteAllText(Path.Combine(outputRoot, file.RelativePath), file.Content);

        foreach (var orphan in Orphans(outputRoot, expected))
            fileSystem.DeleteFile(Path.Combine(outputRoot, orphan));

        return new GenerateResult(true, [], [], files.Count);
    }

    private IEnumerable<string> Orphans(string outputRoot, HashSet<string> expected)
    {
        if (!fileSystem.DirectoryExists(outputRoot))
            return [];
        return fileSystem.EnumerateFiles(outputRoot, "*", recursive: true)
            .Select(f => NormalizePath(Path.GetRelativePath(outputRoot, f)))
            .Where(rel => !expected.Contains(rel))
            .ToList();
    }

    private static string NormalizeContent(string content) => content.Replace("\r\n", "\n");

    private static string NormalizePath(string path) => path.Replace('\\', '/');
}
