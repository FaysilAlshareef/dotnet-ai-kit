using DotnetAiKit.Application.Ports;

namespace DotnetAiKit.Infrastructure;

/// <summary>
/// Atomic, rotated backups of a text file: <c>path.bak.1</c> (newest) … <c>path.bak.N</c>, keeping at
/// most <paramref name="keep"/> generations (ports the v1 upgrade.py backup/rotate design — NFR-7/NFR-8).
/// </summary>
public sealed class BackupRotationService(IFileSystem fileSystem) : IBackupService
{
    public void BackupAndRotate(string path, int keep)
    {
        if (keep < 1 || !fileSystem.FileExists(path))
            return;

        // Drop the oldest, then shift each backup up one slot.
        var oldest = $"{path}.bak.{keep}";
        if (fileSystem.FileExists(oldest))
            fileSystem.DeleteFile(oldest);

        for (var i = keep - 1; i >= 1; i--)
        {
            var from = $"{path}.bak.{i}";
            if (fileSystem.FileExists(from))
            {
                fileSystem.WriteAllText($"{path}.bak.{i + 1}", fileSystem.ReadAllText(from));
                fileSystem.DeleteFile(from);
            }
        }

        fileSystem.WriteAllText($"{path}.bak.1", fileSystem.ReadAllText(path));
    }
}
