using DotnetAiKit.Core.Artifacts;
using DotnetAiKit.Core.Frontmatter;
using DotnetAiKit.Core.Project;
using DotnetAiKit.Core.Values;

namespace DotnetAiKit.Application.Ports;

// ---- Filesystem / process / git -------------------------------------------------

/// <summary>The only file-I/O seam. Writes are atomic temp-replace, utf-8, fixed LF newline.</summary>
public interface IFileSystem
{
    bool FileExists(string path);
    bool DirectoryExists(string path);
    string ReadAllText(string path);
    void WriteAllText(string path, string content);
    void CreateDirectory(string path);
    void DeleteFile(string path);
    IReadOnlyList<string> EnumerateFiles(string path, string searchPattern, bool recursive);
    IReadOnlyList<string> EnumerateDirectories(string path);
}

public sealed record ProcessResult(int ExitCode, string StdOut, string StdErr)
{
    public bool Success => ExitCode == 0;
}

/// <summary>Runs external processes with argument lists — never a shell string (cross-platform safety).</summary>
public interface IProcessRunner
{
    Task<ProcessResult> RunAsync(
        string fileName, IReadOnlyList<string> arguments, string? workingDirectory = null,
        CancellationToken cancellationToken = default);
}

public interface IGitClient
{
    bool IsRepository(string path);
    string? CurrentBranch(string path);
}

public interface ITokenizer
{
    int CountTokens(string text);
}

// ---- Serialization / repository -------------------------------------------------

/// <summary>A SKILL.md/agent file split into its YAML frontmatter block and body.</summary>
public sealed record FrontmatterDocument(string Frontmatter, string Body);

/// <summary>Parses/emits artifact frontmatter (YAML) + body, round-trip-safe.</summary>
public interface IArtifactSerializer
{
    FrontmatterDocument Split(string fileText);
    ArtifactFrontmatter ParseFrontmatter(string fileText);
    string ComposeFrontmatter(ArtifactFrontmatter frontmatter);
}

public sealed record CorpusLoadResult(ArtifactCorpus? Corpus, IReadOnlyList<string> Errors)
{
    public bool Ok => Errors.Count == 0;
}

/// <summary>Loads the authored <c>artifacts/</c> tree → Core models + builds the <c>ArtifactGraph</c>.</summary>
public interface IArtifactRepository
{
    CorpusLoadResult Load(string artifactsRoot);
}

// ---- Detection ------------------------------------------------------------------

public interface IDetectionProvider
{
    ProjectMetadata Detect(string projectRoot);
}

// ---- Projection (build-time) ----------------------------------------------------

/// <summary>A single generated output file (host-relative path + content).</summary>
public sealed record ProjectedFile(string RelativePath, string Content);

/// <summary>Projects the corpus into one host's native shape (skills/agents/rules + manifest).</summary>
public interface IHostProjector
{
    HostName Host { get; }
    IEnumerable<ProjectedFile> Project(ArtifactCorpus corpus);
}

/// <summary>Drives every registered host projector over the corpus.</summary>
public interface IProjectionEngine
{
    IReadOnlyList<ProjectedFile> ProjectAll(ArtifactCorpus corpus);
}

// ---- Per-solution writing (runtime init) ----------------------------------------

/// <summary>Outcome of writing a host's per-solution files (supports user-file + script-trust policy).</summary>
public sealed record HostWriteResult
{
    public IReadOnlyList<string> Written { get; init; } = [];
    public IReadOnlyList<string> Preserved { get; init; } = [];
    public IReadOnlyList<string> ForceRendered { get; init; } = [];
    public IReadOnlyList<string> PendingConsent { get; init; } = [];
}

public interface IHostAdapter
{
    HostName Host { get; }

    HostWriteResult WritePerSolution(
        string solutionRoot, ArtifactCorpus corpus, ProjectMetadata metadata, bool dryRun);
}

public interface IBackupService
{
    void BackupAndRotate(string path, int keep);
}

// ---- Console --------------------------------------------------------------------

public interface IConsoleReporter
{
    void Info(string message);
    void Success(string message);
    void Warn(string message);
    void Error(string message);
    void Table(string title, IReadOnlyList<(string Key, string Value)> rows);
}
