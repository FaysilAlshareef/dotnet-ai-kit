using System.Collections.Immutable;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.Diagnostics;
using Xunit;

namespace DotnetAiKit.Analyzers.Tests;

public class AnalyzerTests
{
    private static async Task<IReadOnlyList<Diagnostic>> Analyze(DiagnosticAnalyzer analyzer, string source)
    {
        var tree = CSharpSyntaxTree.ParseText(source);
        var compilation = CSharpCompilation.Create(
            "AnalyzerTestAssembly",
            [tree],
            [MetadataReference.CreateFromFile(typeof(object).Assembly.Location)],
            new CSharpCompilationOptions(OutputKind.DynamicallyLinkedLibrary));

        var withAnalyzers = compilation.WithAnalyzers(ImmutableArray.Create(analyzer));
        var diagnostics = await withAnalyzers.GetAnalyzerDiagnosticsAsync();
        return diagnostics;
    }

    [Fact]
    public async Task AsyncVoid_method_is_flagged()
    {
        var diagnostics = await Analyze(new AsyncVoidAnalyzer(), "public class C { public async void Handle() { } }");
        Assert.Contains(diagnostics, d => d.Id == AsyncVoidAnalyzer.DiagnosticId);
    }

    [Fact]
    public async Task AsyncTask_method_is_clean()
    {
        var diagnostics = await Analyze(new AsyncVoidAnalyzer(),
            "public class C { public async System.Threading.Tasks.Task Handle() { } }");
        Assert.DoesNotContain(diagnostics, d => d.Id == AsyncVoidAnalyzer.DiagnosticId);
    }

    [Fact]
    public async Task Public_setter_on_aggregate_is_flagged()
    {
        var diagnostics = await Analyze(new AggregateEncapsulationAnalyzer(),
            "public class OrderAggregate { public int Total { get; set; } }");
        Assert.Contains(diagnostics, d => d.Id == AggregateEncapsulationAnalyzer.DiagnosticId);
    }

    [Fact]
    public async Task Private_setter_on_aggregate_is_clean()
    {
        var diagnostics = await Analyze(new AggregateEncapsulationAnalyzer(),
            "public class OrderAggregate { public int Total { get; private set; } }");
        Assert.DoesNotContain(diagnostics, d => d.Id == AggregateEncapsulationAnalyzer.DiagnosticId);
    }

    [Fact]
    public async Task Public_setter_on_non_aggregate_is_clean()
    {
        var diagnostics = await Analyze(new AggregateEncapsulationAnalyzer(),
            "public class OrderDto { public int Total { get; set; } }");
        Assert.DoesNotContain(diagnostics, d => d.Id == AggregateEncapsulationAnalyzer.DiagnosticId);
    }
}
