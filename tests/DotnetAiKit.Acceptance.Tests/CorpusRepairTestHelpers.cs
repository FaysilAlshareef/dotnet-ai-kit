using DotnetAiKit.Core.Artifacts;
using DotnetAiKit.Infrastructure;

namespace DotnetAiKit.Acceptance.Tests;

internal static class CorpusRepairTestHelpers
{
    public static string RepoRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir is not null)
        {
            if (File.Exists(Path.Combine(dir.FullName, "dotnet-ai-kit.slnx")))
                return dir.FullName;
            dir = dir.Parent;
        }

        throw new InvalidOperationException("repo root not found");
    }

    public static string ArtifactPath(params string[] segments) =>
        Path.Combine([RepoRoot(), "artifacts", .. segments]);

    public static string ReadArtifact(params string[] segments) =>
        File.ReadAllText(ArtifactPath(segments));

    public static ArtifactCorpus LoadCorpus()
    {
        var result = new FileSystemArtifactRepository(new PhysicalFileSystem(), new YamlFrontmatterParser())
            .Load(Path.Combine(RepoRoot(), "artifacts"));
        if (!result.Ok || result.Corpus is null)
            throw new InvalidOperationException("corpus load errors: " + string.Join("; ", result.Errors));

        return result.Corpus;
    }
}
