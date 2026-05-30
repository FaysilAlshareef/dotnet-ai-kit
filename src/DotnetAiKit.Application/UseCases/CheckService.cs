using DotnetAiKit.Application.Ports;

namespace DotnetAiKit.Application.UseCases;

public sealed record CheckEntry(string Name, string Status, string Details);

public sealed record CheckResult(int ExitCode, IReadOnlyList<CheckEntry> Checks)
{
    public bool Healthy => ExitCode == 0;
}

/// <summary>
/// Read-only validation of an initialized solution. Returns the enumerated exit-code contract
/// (contracts/exit-codes.md); lowest non-zero code wins on multiple failures (FR-014, SC-007).
/// Makes no network calls (FR-015).
/// </summary>
public sealed class CheckService(IFileSystem fileSystem)
{
    public const int Ok = 0;
    public const int PluginInstallMissing = 10;
    public const int ProjectSchemaInvalid = 12;
    public const int ManifestIntegrity = 14;
    public const int HostSymmetry = 16;

    public CheckResult Run(string solutionRoot)
    {
        var checks = new List<CheckEntry>();
        var exit = Ok;

        void Fail(string name, string details, int code)
        {
            checks.Add(new CheckEntry(name, "fail", details));
            if (exit == Ok || code < exit)
                exit = code;
        }

        void Pass(string name) => checks.Add(new CheckEntry(name, "pass", string.Empty));

        var footprint = Path.Combine(solutionRoot, ".dotnet-ai-kit");
        if (!fileSystem.DirectoryExists(footprint))
            Fail("plugin-install", ".dotnet-ai-kit/ footprint is missing — run init.", PluginInstallMissing);
        else
            Pass("plugin-install");

        var projectYml = Path.Combine(footprint, "project.yml");
        if (!fileSystem.FileExists(projectYml))
            Fail("project-schema", ".dotnet-ai-kit/project.yml is missing.", ProjectSchemaInvalid);
        else
            Pass("project-schema");

        var manifestJson = Path.Combine(footprint, "manifest.json");
        if (!fileSystem.FileExists(manifestJson))
            Fail("manifest-integrity", ".dotnet-ai-kit/manifest.json is missing.", ManifestIntegrity);
        else
            Pass("manifest-integrity");

        var claudeRules = Path.Combine(solutionRoot, ".claude", "rules");
        if (!fileSystem.DirectoryExists(claudeRules))
            Fail("host-symmetry", ".claude/rules/ is missing — rule delivery is broken.", HostSymmetry);
        else
            Pass("host-symmetry");

        return new CheckResult(exit, checks);
    }
}
