using System.Text.Json;
using DotnetAiKit.Hosts.Cursor;
using Xunit;

namespace DotnetAiKit.Acceptance.Tests;

public sealed class CursorPluginDeliveryTests
{
    [Fact]
    public void Cursor_manifest_lives_under_cursor_plugin_root_and_references_existing_agents()
    {
        var files = new CursorProjector()
            .Project(CorpusRepairTestHelpers.LoadCorpus())
            .ToDictionary(f => f.RelativePath, StringComparer.Ordinal);

        Assert.Contains("cursor/.cursor-plugin/plugin.json", files.Keys);
        Assert.DoesNotContain(".cursor-plugin/plugin.json", files.Keys);

        using var doc = JsonDocument.Parse(files["cursor/.cursor-plugin/plugin.json"].Content);
        var agentRefs = ManifestJsonAssertions.ReadStringArray(doc.RootElement, "agents");
        Assert.NotEmpty(agentRefs);

        foreach (var agentRef in agentRefs)
        {
            Assert.StartsWith("./agents/", agentRef, StringComparison.Ordinal);
            var resolved = "cursor/.cursor-plugin/" + agentRef[2..];
            Assert.True(files.ContainsKey(resolved), $"Cursor manifest references missing file: {agentRef}");
        }
    }
}
