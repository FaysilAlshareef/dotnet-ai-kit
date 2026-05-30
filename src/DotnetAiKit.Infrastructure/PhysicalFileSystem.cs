using System.Text;
using DotnetAiKit.Application.Ports;

namespace DotnetAiKit.Infrastructure;

/// <summary>
/// Real filesystem adapter. Writes are atomic (temp file + replace), UTF-8 without BOM, and
/// newline-normalized to LF so generated content is byte-identical across platforms (SC-012).
/// </summary>
public sealed class PhysicalFileSystem : IFileSystem
{
    private static readonly UTF8Encoding Utf8NoBom = new(encoderShouldEmitUTF8Identifier: false);

    public bool FileExists(string path) => File.Exists(path);

    public bool DirectoryExists(string path) => Directory.Exists(path);

    public string ReadAllText(string path) => File.ReadAllText(path);

    public void WriteAllText(string path, string content)
    {
        var dir = Path.GetDirectoryName(path);
        if (!string.IsNullOrEmpty(dir))
            Directory.CreateDirectory(dir);

        var normalized = NormalizeNewlines(content);
        var temp = path + ".tmp-" + Guid.NewGuid().ToString("N");
        File.WriteAllText(temp, normalized, Utf8NoBom);
        File.Move(temp, path, overwrite: true);
    }

    public void CreateDirectory(string path) => Directory.CreateDirectory(path);

    public void DeleteFile(string path)
    {
        if (File.Exists(path))
            File.Delete(path);
    }

    public IReadOnlyList<string> EnumerateFiles(string path, string searchPattern, bool recursive)
    {
        if (!Directory.Exists(path))
            return [];
        var option = recursive ? SearchOption.AllDirectories : SearchOption.TopDirectoryOnly;
        var files = Directory.EnumerateFiles(path, searchPattern, option).ToList();
        files.Sort(StringComparer.Ordinal); // deterministic ordering (FR-011)
        return files;
    }

    public IReadOnlyList<string> EnumerateDirectories(string path)
    {
        if (!Directory.Exists(path))
            return [];
        var dirs = Directory.EnumerateDirectories(path).ToList();
        dirs.Sort(StringComparer.Ordinal);
        return dirs;
    }

    private static string NormalizeNewlines(string content) =>
        content.Replace("\r\n", "\n").Replace('\r', '\n');
}
