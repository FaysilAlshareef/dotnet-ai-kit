namespace DotnetAiKit.Application.UseCases;

/// <summary>How the bare <c>dotnet-ai</c> command resolves on PATH — the hooks invoke it, so a stale v1
/// Python shim shadowing the v2 .NET tool means the hooks load + validate but error on fire (FR-022-10).</summary>
public enum HookToolResolution
{
    /// <summary>A <c>dotnet-ai</c> resolves and looks like the v2 .NET global tool.</summary>
    Ok,

    /// <summary>The first <c>dotnet-ai</c> on PATH is a stale v1 shim (e.g. a Python Scripts launcher).</summary>
    ShadowedByShim,

    /// <summary>No <c>dotnet-ai</c> on PATH — the v2 tool is not installed.</summary>
    NotInstalled,
}

/// <summary>
/// Pure diagnostic for hook-backend resolution (FR-022-10). Given the PATH directories and a file-exists
/// probe, finds the first <c>dotnet-ai</c> launcher and classifies it. No I/O — the CLI supplies PATH +
/// the probe, so this stays deterministic and unit-testable across platforms.
/// </summary>
public static class HookToolDiagnostics
{
    private static readonly string[] LauncherNames = ["dotnet-ai", "dotnet-ai.exe", "dotnet-ai.cmd", "dotnet-ai.bat"];

    public static (HookToolResolution Resolution, string? FoundIn) Diagnose(
        IReadOnlyList<string> pathDirectories, Func<string, bool> fileExists)
    {
        foreach (var dir in pathDirectories)
        {
            if (string.IsNullOrWhiteSpace(dir))
                continue;
            foreach (var name in LauncherNames)
            {
                var candidate = Path.Combine(dir, name);
                if (!fileExists(candidate))
                    continue;

                var normalized = candidate.Replace('\\', '/').ToLowerInvariant();
                // A v1 pip/uv console-script launcher lives under a Python install's Scripts/bin dir.
                if (normalized.Contains("/python") || normalized.Contains("/site-packages/")
                    || normalized.Contains("/scripts/dotnet-ai") && normalized.Contains("python"))
                    return (HookToolResolution.ShadowedByShim, candidate);

                return (HookToolResolution.Ok, candidate);
            }
        }

        return (HookToolResolution.NotInstalled, null);
    }

    /// <summary>A human-readable warning + remediation for a non-Ok resolution; null when Ok.</summary>
    public static string? Warning(HookToolResolution resolution, string? foundIn) => resolution switch
    {
        HookToolResolution.ShadowedByShim =>
            $"'dotnet-ai' on PATH resolves to a stale v1 shim ({foundIn}); the Claude hooks will error on fire. "
            + "Install/repath the v2 tool: dotnet tool install --global DotnetAiKit.Tool, and remove the v1 shim.",
        HookToolResolution.NotInstalled =>
            "'dotnet-ai' is not on PATH; the Claude enforcement hooks cannot run. "
            + "Install the v2 tool: dotnet tool install --global DotnetAiKit.Tool.",
        _ => null,
    };
}
