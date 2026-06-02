using Xunit;

namespace DotnetAiKit.Acceptance.Tests;

public sealed class V2ResidueRepairTests
{
    [Fact]
    public void Touched_guidance_does_not_reference_removed_v1_python_tooling()
    {
        string[][] paths =
        [
            ["skills", "commands", "init", "SKILL.md"],
            ["skills", "commands", "configure", "SKILL.md"],
            ["skills", "commands", "constitution", "SKILL.md"],
            ["skills", "workflow", "git-worktree-isolation", "SKILL.md"],
            ["rules", "domain", "testing.md"],
            ["skills", "workflow", "verification-gate", "SKILL.md"],
            ["skills", "testing", "performance-testing", "SKILL.md"],
            ["knowledge", "testing-patterns.md"]
        ];

        foreach (var path in paths)
        {
            var content = CorpusRepairTestHelpers.ReadArtifact(path);
            Assert.DoesNotContain("pip install dotnet-ai-kit", content, StringComparison.OrdinalIgnoreCase);
            Assert.DoesNotContain("mcp_check.", content, StringComparison.OrdinalIgnoreCase);
            Assert.DoesNotContain("pytest", content, StringComparison.OrdinalIgnoreCase);
            Assert.DoesNotContain("ruff", content, StringComparison.OrdinalIgnoreCase);
            Assert.DoesNotContain("RuntimeMoniker.Net90", content, StringComparison.Ordinal);
        }
    }

    [Fact]
    public void Init_guidance_uses_the_v2_dotnet_tool_install_path()
    {
        var init = CorpusRepairTestHelpers.ReadArtifact("skills", "commands", "init", "SKILL.md");

        Assert.Contains("dotnet tool install --global DotnetAiKit.Tool", init);
        Assert.DoesNotContain("Python", init, StringComparison.OrdinalIgnoreCase);
    }
}
