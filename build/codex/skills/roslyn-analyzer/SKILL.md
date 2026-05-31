---
name: roslyn-analyzer
description: "Authors a Roslyn DiagnosticAnalyzer plus a matching CodeFixProvider that enforces a project convention at compile time. Use when you need a custom compiler diagnostic (squiggle + auto-fix) that built-in rules cannot express, e.g. \"every aggregate must be sealed\". Do NOT use for configuring severity of existing rules in .editorconfig (use code-analysis) or for packaging the analyzer into a NuGet (use analyzer-packaging)."
---
# Roslyn DiagnosticAnalyzer + CodeFixProvider

## Core Principles

- Target `netstandard2.0` for the analyzer project so every host SDK can load it.
- A `DiagnosticAnalyzer` is **read-only**: never mutate the compilation, never do I/O, never block.
- Register actions on the *smallest* node/symbol kind needed; prefer `RegisterSymbolAction` over `RegisterSyntaxNodeAction` when working at the declaration level.
- Call `EnableConcurrentExecution()` and `ConfigureGeneratedCodeAnalysis(GeneratedCodeAnalysisFlags.None)` in `Initialize`.
- Each rule gets a stable `DiagnosticId` (e.g. `PROJ001`) that NEVER changes once shipped.
- The `CodeFixProvider` is the *only* place edits happen, via an immutable `SyntaxNode`/`Solution` transform.

## Analyzer + Fix Example

```csharp
[DiagnosticAnalyzer(LanguageNames.CSharp)]
public sealed class AggregateMustBeSealedAnalyzer : DiagnosticAnalyzer
{
    public const string DiagnosticId = "PROJ001";

    private static readonly DiagnosticDescriptor Rule = new(
        DiagnosticId,
        title: "Aggregate roots must be sealed",
        messageFormat: "Aggregate '{0}' should be declared sealed",
        category: "Design",
        DiagnosticSeverity.Warning,
        isEnabledByDefault: true,
        description: "Aggregate roots are not designed for inheritance.");

    public override ImmutableArray<DiagnosticDescriptor> SupportedDiagnostics
        => ImmutableArray.Create(Rule);

    public override void Initialize(AnalysisContext context)
    {
        context.EnableConcurrentExecution();
        context.ConfigureGeneratedCodeAnalysis(GeneratedCodeAnalysisFlags.None);
        context.RegisterSymbolAction(AnalyzeType, SymbolKind.NamedType);
    }

    private static void AnalyzeType(SymbolAnalysisContext context)
    {
        var type = (INamedTypeSymbol)context.Symbol;
        if (type.TypeKind != TypeKind.Class || type.IsSealed || type.IsAbstract)
            return;
        if (!type.AllInterfaces.Any(i => i.Name == "IAggregateRoot"))
            return;

        context.ReportDiagnostic(
            Diagnostic.Create(Rule, type.Locations[0], type.Name));
    }
}

[ExportCodeFixProvider(LanguageNames.CSharp), Shared]
public sealed class AggregateMustBeSealedFixer : CodeFixProvider
{
    public override ImmutableArray<string> FixableDiagnosticIds
        => ImmutableArray.Create(AggregateMustBeSealedAnalyzer.DiagnosticId);

    public override FixAllProvider GetFixAllProvider() => WellKnownFixAllProviders.BatchFixer;

    public override async Task RegisterCodeFixesAsync(CodeFixContext context)
    {
        var root = await context.Document.GetSyntaxRootAsync(context.CancellationToken);
        var node = root?.FindToken(context.Span.Start).Parent?
            .AncestorsAndSelf().OfType<ClassDeclarationSyntax>().First();
        if (node is null) return;

        context.RegisterCodeFix(
            CodeAction.Create(
                "Make class sealed",
                ct => MakeSealedAsync(context.Document, node, ct),
                equivalenceKey: nameof(AggregateMustBeSealedFixer)),
            context.Diagnostics);
    }

    private static async Task<Document> MakeSealedAsync(
        Document doc, ClassDeclarationSyntax decl, CancellationToken ct)
    {
        var sealedKeyword = SyntaxFactory.Token(SyntaxKind.SealedKeyword)
            .WithTrailingTrivia(SyntaxFactory.Space);
        var newDecl = decl.AddModifiers(sealedKeyword);
        var root = await doc.GetSyntaxRootAsync(ct);
        return doc.WithSyntaxRoot(root!.ReplaceNode(decl, newDecl));
    }
}
```

## Gotchas

- Do not store per-compilation state in instance fields — analyzers are reused across compilations. Use `RegisterCompilationStartAction` for scoped state.
- Resolve symbols by `Compilation.GetTypeByMetadataName(...)` inside a start action, not by string name matching, when you control the marker type.
- A `CodeFixProvider` must return a *new* `Document`/`Solution`; never edit text in place.
- Always provide `equivalenceKey` so Fix-All can batch identical fixes.

## References

- https://learn.microsoft.com/en-us/dotnet/csharp/roslyn-sdk/tutorials/how-to-write-csharp-analyzer-code-fix
