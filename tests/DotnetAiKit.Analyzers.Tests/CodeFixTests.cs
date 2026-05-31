using System.Collections.Immutable;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CodeActions;
using Microsoft.CodeAnalysis.CodeFixes;
using Microsoft.CodeAnalysis.Diagnostics;
using Xunit;

namespace DotnetAiKit.Analyzers.Tests;

public class CodeFixTests
{
    [Fact]
    public async Task DAK0004_codefix_makes_aggregate_setter_private()
    {
        const string source = "public class OrderAggregate { public int Total { get; set; } }";

        using var workspace = new AdhocWorkspace();
        var project = workspace
            .AddProject("T", LanguageNames.CSharp)
            .AddMetadataReference(MetadataReference.CreateFromFile(typeof(object).Assembly.Location));
        var document = project.AddDocument("T.cs", source);

        var compilation = await document.Project.GetCompilationAsync();
        var withAnalyzers = compilation!.WithAnalyzers(ImmutableArray.Create<DiagnosticAnalyzer>(new AggregateEncapsulationAnalyzer()));
        var diagnostic = (await withAnalyzers.GetAnalyzerDiagnosticsAsync()).Single(d => d.Id == AggregateEncapsulationAnalyzer.DiagnosticId);

        CodeAction? action = null;
        var context = new CodeFixContext(document, diagnostic, (a, _) => action = a, CancellationToken.None);
        await new AggregateSetterCodeFix().RegisterCodeFixesAsync(context);
        Assert.NotNull(action);

        var operations = await action!.GetOperationsAsync(CancellationToken.None);
        var applied = operations.OfType<ApplyChangesOperation>().Single();
        var fixedText = (await applied.ChangedSolution.GetDocument(document.Id)!.GetTextAsync()).ToString();

        Assert.Contains("private set", fixedText, StringComparison.Ordinal);
    }
}
