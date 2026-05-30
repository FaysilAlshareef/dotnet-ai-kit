using DotnetAiKit.Application.Ports;

namespace DotnetAiKit.Application.UseCases;

public sealed record GateResult(bool Allowed, int BuildExitCode, int TestExitCode, string Summary);

/// <summary>
/// The completion-gate decision logic backing the Claude Stop/SubagentStop hook (FR-023, SC-004):
/// run build, then tests; block completion ("done") unless both are green. Pure of any host concern —
/// the hook script invokes this and translates the result to a block/allow decision.
/// </summary>
public sealed class VerificationGateService(IProcessRunner processRunner)
{
    public async Task<GateResult> EvaluateAsync(string solutionRoot, CancellationToken cancellationToken = default)
    {
        var build = await processRunner.RunAsync("dotnet", ["build", "--nologo"], solutionRoot, cancellationToken);
        if (!build.Success)
            return new GateResult(false, build.ExitCode, -1, "build failed — completion blocked");

        var test = await processRunner.RunAsync("dotnet", ["test", "--nologo"], solutionRoot, cancellationToken);
        return test.Success
            ? new GateResult(true, build.ExitCode, test.ExitCode, "build + tests green — completion allowed")
            : new GateResult(false, build.ExitCode, test.ExitCode, "tests failed — completion blocked");
    }
}
