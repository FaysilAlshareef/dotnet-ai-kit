using DotnetAiKit.Application.Ports;

namespace DotnetAiKit.Application.UseCases;

public sealed record ConfigureResult(bool Ok, string Message, IReadOnlyList<string> Errors);

/// <summary>Sets a key in the per-solution <c>.dotnet-ai-kit/config.yml</c> (FR-013); <c>--dry-run</c> previews.</summary>
public sealed class ConfigureService(IFileSystem fileSystem)
{
    public ConfigureResult Set(string solutionRoot, string key, string value, bool dryRun)
    {
        if (string.IsNullOrWhiteSpace(key))
            return new ConfigureResult(false, string.Empty, ["key must not be empty"]);

        var configPath = Path.Combine(solutionRoot, ".dotnet-ai-kit", "config.yml");
        var existing = fileSystem.FileExists(configPath) ? fileSystem.ReadAllText(configPath) : string.Empty;

        var lines = existing.Replace("\r\n", "\n").TrimEnd('\n')
            .Split('\n', StringSplitOptions.None)
            .Where(l => l.Length > 0)
            .ToList();

        var prefix = key + ":";
        var index = lines.FindIndex(l => l.TrimStart().StartsWith(prefix, StringComparison.Ordinal));
        var newLine = $"{key}: {value}";
        if (index >= 0)
            lines[index] = newLine;
        else
            lines.Add(newLine);

        if (!dryRun)
            fileSystem.WriteAllText(configPath, string.Join("\n", lines) + "\n");

        return new ConfigureResult(true, $"{key} = {value}", []);
    }
}
