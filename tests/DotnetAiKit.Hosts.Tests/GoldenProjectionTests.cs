using DotnetAiKit.Hosts.Claude;
using DotnetAiKit.Hosts.Codex;
using DotnetAiKit.Hosts.Copilot;
using DotnetAiKit.Hosts.Cursor;
using VerifyXunit;
using Xunit;

namespace DotnetAiKit.Hosts.Tests;

/// <summary>
/// NFR-6 / FR-022-08/09: golden-output (Verify) over the full projection of a fixed sample corpus —
/// every artifact-type × host + the plugin manifests, marketplace.json, hooks.json, AGENTS.md, and
/// copilot-instructions.md. Pins the emitted SHAPE, so a projector format change fails this test
/// independently of the `generate --check` drift gate (which only compares against committed build/).
/// </summary>
public class GoldenProjectionTests
{
    [Fact]
    public Task Full_projection_shape_is_byte_stable()
    {
        var engine = new ProjectionEngine(new HostRegistry(
        [
            new ClaudeProjector(), new CodexProjector(), new CursorProjector(), new CopilotProjector(),
        ]));

        var snapshot = string.Join(
            "\n",
            engine.ProjectAll(MultiHostProjectorTests.Sample())
                .OrderBy(f => f.RelativePath, StringComparer.Ordinal)
                .Select(f => $"=== {f.RelativePath} ===\n{f.Content}"));

        return Verifier.Verify(snapshot, extension: "txt");
    }
}
