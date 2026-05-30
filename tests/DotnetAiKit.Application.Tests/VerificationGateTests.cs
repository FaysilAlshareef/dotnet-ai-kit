using DotnetAiKit.Application.Ports;
using DotnetAiKit.Application.UseCases;
using Xunit;

namespace DotnetAiKit.Application.Tests;

public class VerificationGateTests
{
    private sealed class FakeProcessRunner(params ProcessResult[] results) : IProcessRunner
    {
        private readonly Queue<ProcessResult> _results = new(results);

        public Task<ProcessResult> RunAsync(
            string fileName, IReadOnlyList<string> arguments, string? workingDirectory = null,
            CancellationToken cancellationToken = default) =>
            Task.FromResult(_results.Count > 0 ? _results.Dequeue() : new ProcessResult(0, "", ""));
    }

    [Fact]
    public async Task Blocks_completion_when_build_fails()
    {
        var gate = new VerificationGateService(new FakeProcessRunner(new ProcessResult(1, "", "build error")));
        var result = await gate.EvaluateAsync(".");
        Assert.False(result.Allowed);
    }

    [Fact]
    public async Task Blocks_completion_when_tests_fail()
    {
        var gate = new VerificationGateService(new FakeProcessRunner(
            new ProcessResult(0, "build ok", ""),
            new ProcessResult(1, "", "test failed")));
        var result = await gate.EvaluateAsync(".");
        Assert.False(result.Allowed);
    }

    [Fact]
    public async Task Allows_completion_when_build_and_tests_are_green()
    {
        var gate = new VerificationGateService(new FakeProcessRunner(
            new ProcessResult(0, "build ok", ""),
            new ProcessResult(0, "tests passed", "")));
        var result = await gate.EvaluateAsync(".");
        Assert.True(result.Allowed);
    }
}
