using Xunit;

namespace DotnetAiKit.Acceptance.Tests;

internal static class GeneratedOutputAssertions
{
    public static string BuildPath(params string[] segments) =>
        Path.Combine([CorpusRepairTestHelpers.RepoRoot(), "build", .. segments]);

    public static void FileExists(params string[] segments)
    {
        var path = BuildPath(segments);
        Assert.True(File.Exists(path), $"Expected generated file to exist: {path}");
    }

    public static void DirectoryExists(params string[] segments)
    {
        var path = BuildPath(segments);
        Assert.True(Directory.Exists(path), $"Expected generated directory to exist: {path}");
    }
}
