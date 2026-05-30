using Xunit;

namespace DotnetAiKit.Acceptance.Tests;

// P0 scaffold smoke test. Real cross-language invariant tests (no-network, exit codes, footprint) land in P5.
public class SmokeTests
{
    [Fact]
    public void Scaffold_test_host_runs() => Assert.True(true);
}
