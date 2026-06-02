using DotnetAiKit.Application.Ports;
using DotnetAiKit.Application.UseCases;
using DotnetAiKit.Hosts;
using DotnetAiKit.Hosts.Claude;
using DotnetAiKit.Infrastructure;
using Xunit;

namespace DotnetAiKit.Acceptance.Tests;

/// <summary>SC-007: the cross-cutting contract — enumerated check exit codes + the no-network invariant.</summary>
public class CheckContractTests
{
    private static string RepoRoot()
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

    private static string TempDir() => Path.Combine(Path.GetTempPath(), "dak-chk-" + Guid.NewGuid().ToString("N"));

    [Fact]
    public void Healthy_initialized_project_returns_zero()
    {
        var temp = TempDir();
        try
        {
            var fs = new PhysicalFileSystem();
            new InitService(new DotnetProjectDetector(fs), new FileSystemArtifactRepository(fs, new YamlFrontmatterParser()), new ClaudeHostAdapter(fs, new BackupRotationService(fs), new ManifestIntegrityService()))
                .Run(temp, Path.Combine(RepoRoot(), "artifacts"), dryRun: false);

            var result = new CheckService(fs, new ManifestIntegrityService()).Run(temp);
            Assert.Equal(CheckService.Ok, result.ExitCode);
        }
        finally { if (Directory.Exists(temp)) Directory.Delete(temp, true); }
    }

    [Fact]
    public void Uninitialized_directory_returns_plugin_install_missing()
    {
        var temp = TempDir();
        Directory.CreateDirectory(temp);
        try
        {
            var result = new CheckService(new PhysicalFileSystem(), new ManifestIntegrityService()).Run(temp);
            Assert.Equal(CheckService.PluginInstallMissing, result.ExitCode);
        }
        finally { Directory.Delete(temp, true); }
    }

    [Fact]
    public void Lowest_code_wins_across_multiple_failures()
    {
        // Footprint dir present (10 passes) but project.yml (12), manifest.json (14), and
        // .claude/rules (16) all missing → lowest non-zero code (12) wins.
        var temp = TempDir();
        Directory.CreateDirectory(Path.Combine(temp, ".dotnet-ai-kit"));
        try
        {
            var result = new CheckService(new PhysicalFileSystem(), new ManifestIntegrityService()).Run(temp);
            Assert.Equal(CheckService.ProjectSchemaInvalid, result.ExitCode);
        }
        finally { Directory.Delete(temp, true); }
    }

    [Fact]
    public void Missing_manifest_fails_manifest_integrity_with_clear_details()
    {
        var temp = TempDir();
        try
        {
            var fs = new PhysicalFileSystem();
            new InitService(new DotnetProjectDetector(fs), new FileSystemArtifactRepository(fs, new YamlFrontmatterParser()), new ClaudeHostAdapter(fs, new BackupRotationService(fs), new ManifestIntegrityService()))
                .Run(temp, Path.Combine(RepoRoot(), "artifacts"), dryRun: false);
            File.Delete(Path.Combine(temp, ".dotnet-ai-kit", "manifest.json"));

            var result = new CheckService(fs, new ManifestIntegrityService()).Run(temp);

            Assert.Equal(CheckService.ManifestIntegrity, result.ExitCode);
            Assert.Contains(result.Checks, c =>
                c.Name == "manifest-integrity"
                && c.Status == "fail"
                && c.Details.Contains("manifest.json is missing", StringComparison.Ordinal));
        }
        finally { if (Directory.Exists(temp)) Directory.Delete(temp, true); }
    }

    [Fact]
    public void Tampered_manifest_fails_manifest_integrity_with_hash_mismatch()
    {
        var temp = TempDir();
        try
        {
            var fs = new PhysicalFileSystem();
            new InitService(new DotnetProjectDetector(fs), new FileSystemArtifactRepository(fs, new YamlFrontmatterParser()), new ClaudeHostAdapter(fs, new BackupRotationService(fs), new ManifestIntegrityService()))
                .Run(temp, Path.Combine(RepoRoot(), "artifacts"), dryRun: false);
            var manifestPath = Path.Combine(temp, ".dotnet-ai-kit", "manifest.json");
            var manifest = File.ReadAllText(manifestPath)
                .Replace("\"rules\": 21", "\"rules\": 999", StringComparison.Ordinal);
            File.WriteAllText(manifestPath, manifest);

            var result = new CheckService(fs, new ManifestIntegrityService()).Run(temp);

            Assert.Equal(CheckService.ManifestIntegrity, result.ExitCode);
            Assert.Contains(result.Checks, c =>
                c.Name == "manifest-integrity"
                && c.Status == "fail"
                && c.Details.Contains("manifest hash mismatch", StringComparison.Ordinal));
        }
        finally { if (Directory.Exists(temp)) Directory.Delete(temp, true); }
    }

    [Fact]
    public void Local_operations_complete_without_network()
    {
        // FR-015 / SC-007: init, generate and check use only the filesystem port + local process —
        // no HttpClient anywhere on these paths. They complete fully offline.
        // (A process-level socket-deny harness is a follow-on hardening of this behavioral guarantee.)
        var temp = TempDir();
        var buildOut = Path.Combine(temp, "out");
        try
        {
            var fs = new PhysicalFileSystem();
            var artifacts = Path.Combine(RepoRoot(), "artifacts");
            var repo = new FileSystemArtifactRepository(fs, new YamlFrontmatterParser());

            new GenerateService(repo, new ProjectionEngine(new HostRegistry(new IHostProjector[] { new ClaudeProjector() })), fs)
                .Run(artifacts, buildOut, checkOnly: false);
            new InitService(new DotnetProjectDetector(fs), repo, new ClaudeHostAdapter(fs, new BackupRotationService(fs), new ManifestIntegrityService()))
                .Run(temp, artifacts, dryRun: false);
            var check = new CheckService(fs, new ManifestIntegrityService()).Run(temp);

            Assert.True(Directory.Exists(Path.Combine(buildOut, "claude")));
            Assert.Equal(CheckService.Ok, check.ExitCode);
        }
        finally { if (Directory.Exists(temp)) Directory.Delete(temp, true); }
    }
}
