using Xunit;

namespace DotnetAiKit.Core.Tests;

// P0 scaffold smoke test — guarantees the test host runs green. Real Core tests land in P1.
public class SmokeTests
{
    [Fact]
    public void Scaffold_test_host_runs() => Assert.True(true);
}
