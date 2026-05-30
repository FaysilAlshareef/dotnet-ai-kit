using System.Collections.Immutable;
using System.Linq;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.Diagnostics;

namespace DotnetAiKit.Analyzers;

/// <summary>DAK0001: flags <c>async void</c> methods (they swallow exceptions and cannot be awaited).
/// Mirrors the security / async-concurrency convention rules (deterministic enforcement, FR-022).</summary>
[DiagnosticAnalyzer(LanguageNames.CSharp)]
public sealed class AsyncVoidAnalyzer : DiagnosticAnalyzer
{
    public const string DiagnosticId = "DAK0001";

    private static readonly DiagnosticDescriptor Rule = new(
        id: DiagnosticId,
        title: "Avoid async void",
        messageFormat: "Method '{0}' is 'async void'; return 'async Task' so failures are observable and awaitable",
        category: "Reliability",
        defaultSeverity: DiagnosticSeverity.Warning,
        isEnabledByDefault: true,
        description: "async void methods swallow exceptions and cannot be awaited. Paired with the security and async-concurrency rules.");

    public override ImmutableArray<DiagnosticDescriptor> SupportedDiagnostics => ImmutableArray.Create(Rule);

    public override void Initialize(AnalysisContext context)
    {
        context.EnableConcurrentExecution();
        context.ConfigureGeneratedCodeAnalysis(GeneratedCodeAnalysisFlags.None);
        context.RegisterSyntaxNodeAction(Analyze, SyntaxKind.MethodDeclaration);
    }

    private static void Analyze(SyntaxNodeAnalysisContext context)
    {
        var method = (MethodDeclarationSyntax)context.Node;
        var isAsync = method.Modifiers.Any(m => m.IsKind(SyntaxKind.AsyncKeyword));
        var isVoid = method.ReturnType is PredefinedTypeSyntax pre && pre.Keyword.IsKind(SyntaxKind.VoidKeyword);
        if (isAsync && isVoid)
            context.ReportDiagnostic(Diagnostic.Create(Rule, method.Identifier.GetLocation(), method.Identifier.Text));
    }
}
