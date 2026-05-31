using DotnetAiKit.Application.Ports;
using DotnetAiKit.Core.Artifacts;
using DotnetAiKit.Infrastructure;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Xunit;

namespace DotnetAiKit.Acceptance.Tests;

/// <summary>
/// FR-022-01/02/03 + SC-022-1: the required resource set is present per skill-kind and bundled C#
/// examples are syntactically valid. "Compilable" is read as Roslyn-parse-valid (no error-severity
/// syntax diagnostics) — examples reference ASP.NET/EF types not in the solution, so a full semantic
/// compile is out of scope (see spec §FR-022-02).
/// </summary>
public class SkillResourceTests
{
    private static ArtifactCorpus LoadCorpus()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir is not null && !File.Exists(Path.Combine(dir.FullName, "dotnet-ai-kit.slnx")))
            dir = dir.Parent;
        Assert.NotNull(dir);
        var result = new FileSystemArtifactRepository(new PhysicalFileSystem(), new YamlFrontmatterParser())
            .Load(Path.Combine(dir!.FullName, "artifacts"));
        Assert.True(result.Ok, string.Join("; ", result.Errors));
        return result.Corpus!;
    }

    private static Skill Skill(ArtifactCorpus corpus, string name) =>
        corpus.Skills.Single(s => s.Name.Value == name);

    [Theory]
    [InlineData("constitution")]
    [InlineData("checklist")]
    [InlineData("fix")]
    [InlineData("release")]
    public void New_command_skill_bundles_workflow_scripts(string name) =>
        Assert.NotEmpty(Skill(LoadCorpus(), name).Resources.Scripts);

    [Theory]
    [InlineData("add-aggregate")]
    [InlineData("add-entity")]
    [InlineData("add-event")]
    [InlineData("add-endpoint")]
    [InlineData("add-page")]
    [InlineData("add-crud")]
    [InlineData("add-tests")]
    public void Add_command_skill_bundles_an_example(string name) =>
        Assert.NotEmpty(Skill(LoadCorpus(), name).Resources.Examples);

    [Fact]
    public void Bundled_csharp_examples_are_syntactically_valid()
    {
        var corpus = LoadCorpus();
        var failures = new List<string>();
        foreach (var skill in corpus.Skills)
            foreach (var resource in skill.Resources.All()
                         .Where(r => r.RelativePath.EndsWith(".cs", StringComparison.Ordinal)))
            {
                var errors = CSharpSyntaxTree.ParseText(resource.Content)
                    .GetDiagnostics()
                    .Where(d => d.Severity == DiagnosticSeverity.Error)
                    .Select(d => d.GetMessage())
                    .ToList();
                if (errors.Count > 0)
                    failures.Add($"{skill.Name}/{resource.RelativePath}: {string.Join("; ", errors)}");
            }

        Assert.True(failures.Count == 0, "C# examples with syntax errors:\n" + string.Join("\n", failures));
    }

    [Fact]
    public void Executable_scripts_are_flagged_for_the_trust_model()
    {
        // FR-022-05: bundled scripts are recognized as executable (never auto-run without consent).
        var corpus = LoadCorpus();
        foreach (var skill in corpus.Skills)
            foreach (var script in skill.Resources.Scripts.Where(s =>
                         s.RelativePath.EndsWith(".py", StringComparison.Ordinal)))
                Assert.True(script.IsExecutable, $"{skill.Name}/{script.RelativePath} should be executable");
    }
}
