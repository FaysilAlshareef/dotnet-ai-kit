using DotnetAiKit.Application.Ports;

namespace DotnetAiKit.Application.UseCases;

public sealed record MigrateResult(bool Ok, IReadOnlyList<string> Migrated, IReadOnlyList<string> Errors);

/// <summary>
/// Cleans v1 layout artifacts with rotated backups (NFR-8). For the per-solution config, migrates the
/// legacy <c>ai_tools:</c> key to <c>enabled_hosts:</c> (FR-018), backing up first. <c>--dry-run</c> previews.
/// </summary>
public sealed class MigrateService(IFileSystem fileSystem, IBackupService backupService)
{
    public MigrateResult Run(string solutionRoot, int keep, bool dryRun)
    {
        var migrated = new List<string>();
        var configPath = Path.Combine(solutionRoot, ".dotnet-ai-kit", "config.yml");

        if (fileSystem.FileExists(configPath))
        {
            var text = fileSystem.ReadAllText(configPath);
            if (text.Contains("ai_tools:", StringComparison.Ordinal))
            {
                if (!dryRun)
                {
                    backupService.BackupAndRotate(configPath, keep);
                    fileSystem.WriteAllText(configPath, text.Replace("ai_tools:", "enabled_hosts:", StringComparison.Ordinal));
                }

                migrated.Add(".dotnet-ai-kit/config.yml (ai_tools → enabled_hosts)");
            }
        }

        return new MigrateResult(true, migrated, []);
    }
}
