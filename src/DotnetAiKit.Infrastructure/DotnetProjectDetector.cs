using System.Text.RegularExpressions;
using DotnetAiKit.Application.Ports;
using DotnetAiKit.Core.Project;

namespace DotnetAiKit.Infrastructure;

/// <summary>Detects .NET version + architecture + path map from a target solution's .csproj files and folders.</summary>
public sealed partial class DotnetProjectDetector(IFileSystem fileSystem) : IDetectionProvider
{
    [GeneratedRegex(@"<TargetFramework>([^<]+)</TargetFramework>", RegexOptions.CultureInvariant)]
    private static partial Regex TargetFrameworkRegex();

    public ProjectMetadata Detect(string projectRoot)
    {
        var dotnetVersion = string.Empty;
        foreach (var csproj in fileSystem.EnumerateFiles(projectRoot, "*.csproj", recursive: true))
        {
            var match = TargetFrameworkRegex().Match(fileSystem.ReadAllText(csproj));
            if (match.Success)
            {
                dotnetVersion = match.Groups[1].Value.Trim();
                break;
            }
        }

        return new ProjectMetadata
        {
            Company = string.Empty,
            Domain = string.Empty,
            Architecture = DetectArchitecture(projectRoot),
            DotnetVersion = dotnetVersion,
            DetectedPaths = new DetectedPaths { Paths = DetectPaths(projectRoot) },
        };
    }

    private string DetectArchitecture(string projectRoot)
    {
        var dirNames = fileSystem.EnumerateDirectories(projectRoot)
            .Select(d => Path.GetFileName(d).ToLowerInvariant())
            .ToHashSet(StringComparer.Ordinal);

        if (dirNames.Contains("domain") && dirNames.Contains("application") && dirNames.Contains("infrastructure"))
            return "clean";
        if (dirNames.Contains("features"))
            return "vsa";
        return "generic";
    }

    private Dictionary<string, string> DetectPaths(string projectRoot)
    {
        var map = new Dictionary<string, string>(StringComparer.Ordinal);
        foreach (var dir in fileSystem.EnumerateDirectories(projectRoot))
        {
            var name = Path.GetFileName(dir).ToLowerInvariant();
            if (name is "domain" or "entities" or "aggregates" or "endpoints" or "application")
                map[name] = name;
        }

        return map;
    }
}
