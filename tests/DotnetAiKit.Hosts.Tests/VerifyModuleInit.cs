using System.Runtime.CompilerServices;

namespace DotnetAiKit.Hosts.Tests;

/// <summary>
/// Makes the Verify golden hermetic: never launch a diff GUI on a snapshot mismatch. CI already sets
/// CI=true (which disables DiffEngine), but this guards a bare developer machine where a failing golden
/// would otherwise block waiting for a diff tool.
/// </summary>
internal static class VerifyModuleInit
{
    [ModuleInitializer]
    public static void Init() => DiffEngine.DiffRunner.Disabled = true;
}
