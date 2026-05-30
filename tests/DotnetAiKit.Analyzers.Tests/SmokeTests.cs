using Xunit;

namespace DotnetAiKit.Analyzers.Tests;

// P0 scaffold smoke test. Real analyzer diagnostic tests land in P7.
public class SmokeTests
{
    [Fact]
    public void Scaffold_test_host_runs() => Assert.True(true);
}
