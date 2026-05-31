using DotnetAiKit.Application.UseCases;
using Xunit;

namespace DotnetAiKit.Application.Tests;

/// <summary>
/// Unit coverage for the PreToolUse hook decision logic (planning/24 T1 injection + T2 deny). The Stop
/// gate (T4) is covered by <c>VerificationGateTests</c>; here we pin the pure path/rule decisions.
/// </summary>
public class HookTests
{
    private static HookRule Universal(string body) => new([], body);

    private static HookRule Domain(string body, params string[] globs) => new(globs, body);

    [Theory]
    [InlineData("src/obj/Debug/App.dll")]
    [InlineData("obj/x.cs")]
    [InlineData("src/bin/Release/y.json")]
    [InlineData("Generated/Foo.g.cs")]
    [InlineData("Views/Bar.Designer.cs")]
    [InlineData("obj/App.AssemblyInfo.cs")]
    public void Denies_edits_to_generated_or_output_files(string path)
    {
        var decision = PreToolUseHookService.Decide(path, []);
        Assert.NotNull(decision.DenyReason);
        Assert.Null(decision.AdditionalContext);
    }

    [Fact]
    public void Injects_universal_rule_for_any_source_path()
    {
        var decision = PreToolUseHookService.Decide("src/Foo.cs", [Universal("ALWAYS-ON RULE")]);
        Assert.Null(decision.DenyReason);
        Assert.Equal("ALWAYS-ON RULE", decision.AdditionalContext);
    }

    [Fact]
    public void Injects_domain_rule_only_when_the_path_matches()
    {
        var rules = new[] { Domain("CS RULE", "**/*.cs") };

        Assert.Equal("CS RULE", PreToolUseHookService.Decide("src/A/B.cs", rules).AdditionalContext);
        Assert.Null(PreToolUseHookService.Decide("docs/readme.md", rules).AdditionalContext);
    }

    [Fact]
    public void Concatenates_universal_and_matching_domain_rules_in_order()
    {
        var rules = new[]
        {
            Universal("UNIVERSAL"),
            Domain("RAZOR", "**/*.razor"),
            Domain("CS", "**/*.cs"),
        };

        var ctx = PreToolUseHookService.Decide("src/Page.cs", rules).AdditionalContext;
        Assert.Equal("UNIVERSAL\n\nCS", ctx);
    }

    [Fact]
    public void No_decision_for_a_plain_path_with_no_rules()
    {
        var decision = PreToolUseHookService.Decide("src/Foo.cs", []);
        Assert.Null(decision.DenyReason);
        Assert.Null(decision.AdditionalContext);
    }

    [Fact]
    public void Empty_path_is_a_no_op()
    {
        var decision = PreToolUseHookService.Decide("", [Universal("X")]);
        Assert.Same(PreToolUseDecision.None, decision);
    }

    [Theory]
    [InlineData("src/Foo.cs", "**/*.cs", true)]
    [InlineData("Foo.cs", "*.cs", true)]
    [InlineData("src/api/E.cs", "src/**", true)]
    [InlineData("src/api/E.cs", "**/Endpoints/**/*.cs", false)]
    [InlineData("README.md", "**/*.cs", false)]
    [InlineData("a/b/c.razor", "**/*.razor", true)]
    public void Glob_matching_is_deterministic(string rel, string glob, bool expected) =>
        Assert.Equal(expected, PreToolUseHookService.Matches(rel, glob));

    // ---- HookToolDiagnostics (FR-022-10): bare `dotnet-ai` resolution ----

    [Fact]
    public void Diagnose_flags_a_python_scripts_shim_as_shadowed()
    {
        string[] path = ["C:/Users/x/AppData/Local/Programs/Python/Python312/Scripts", "C:/Users/x/.dotnet/tools"];
        var (resolution, foundIn) = HookToolDiagnostics.Diagnose(
            path, p => p.Replace('\\', '/').Contains("/Python312/Scripts/dotnet-ai"));
        Assert.Equal(HookToolResolution.ShadowedByShim, resolution);
        Assert.NotNull(HookToolDiagnostics.Warning(resolution, foundIn));
    }

    [Fact]
    public void Diagnose_accepts_a_dotnet_tools_launcher()
    {
        string[] path = ["/home/x/.dotnet/tools"];
        var (resolution, _) = HookToolDiagnostics.Diagnose(
            path, p => p.Replace('\\', '/').EndsWith("/.dotnet/tools/dotnet-ai", StringComparison.Ordinal));
        Assert.Equal(HookToolResolution.Ok, resolution);
    }

    [Fact]
    public void Diagnose_reports_not_installed_when_absent()
    {
        var (resolution, _) = HookToolDiagnostics.Diagnose(["/usr/bin"], _ => false);
        Assert.Equal(HookToolResolution.NotInstalled, resolution);
        Assert.NotNull(HookToolDiagnostics.Warning(resolution, null));
    }
}
