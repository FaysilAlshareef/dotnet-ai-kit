using Xunit;

namespace DotnetAiKit.Cli.Tests;

// P0 scaffold smoke test. Real verb end-to-end tests land in P5.
public class SmokeTests
{
    [Fact]
    public void Scaffold_test_host_runs() => Assert.True(true);
}
