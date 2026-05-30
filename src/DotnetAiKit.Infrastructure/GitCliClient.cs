using DotnetAiKit.Application.Ports;

namespace DotnetAiKit.Infrastructure;

/// <summary>
/// Git information read from the <c>.git</c> directory (no subprocess, no network) — sufficient for
/// repo detection and current-branch resolution. Walks up to find the repository root.
/// </summary>
public sealed class GitCliClient : IGitClient
{
    public bool IsRepository(string path) => FindGitDir(path) is not null;

    public string? CurrentBranch(string path)
    {
        var gitDir = FindGitDir(path);
        if (gitDir is null)
            return null;

        var headFile = Path.Combine(gitDir, "HEAD");
        if (!File.Exists(headFile))
            return null;

        var head = File.ReadAllText(headFile).Trim();
        // "ref: refs/heads/<branch>" for a normal checkout; a bare SHA for detached HEAD.
        const string prefix = "ref: refs/heads/";
        return head.StartsWith(prefix, StringComparison.Ordinal) ? head[prefix.Length..] : null;
    }

    private static string? FindGitDir(string startPath)
    {
        var current = new DirectoryInfo(Path.GetFullPath(startPath));
        while (current is not null)
        {
            var candidate = Path.Combine(current.FullName, ".git");
            if (Directory.Exists(candidate))
                return candidate;
            current = current.Parent;
        }

        return null;
    }
}
