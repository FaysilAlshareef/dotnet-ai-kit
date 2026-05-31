using System.Collections.Immutable;
using System.Composition;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CodeActions;
using Microsoft.CodeAnalysis.CodeFixes;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

namespace DotnetAiKit.Analyzers;

/// <summary>Code-fix for DAK0004: add <c>private</c> to a public setter on an aggregate (FR-F3 / T060).</summary>
[ExportCodeFixProvider(LanguageNames.CSharp, Name = nameof(AggregateSetterCodeFix))]
[Shared]
public sealed class AggregateSetterCodeFix : CodeFixProvider
{
    public override ImmutableArray<string> FixableDiagnosticIds =>
        ImmutableArray.Create(AggregateEncapsulationAnalyzer.DiagnosticId);

    public override FixAllProvider GetFixAllProvider() => WellKnownFixAllProviders.BatchFixer;

    public override async Task RegisterCodeFixesAsync(CodeFixContext context)
    {
        var root = await context.Document.GetSyntaxRootAsync(context.CancellationToken).ConfigureAwait(false);
        if (root is null)
            return;

        var diagnostic = context.Diagnostics[0];
        var node = root.FindNode(diagnostic.Location.SourceSpan);
        var setter = node as AccessorDeclarationSyntax ?? node.FirstAncestorOrSelf<AccessorDeclarationSyntax>();
        if (setter is null || !setter.IsKind(SyntaxKind.SetAccessorDeclaration))
            return;

        context.RegisterCodeFix(
            CodeAction.Create(
                title: "Make setter private",
                createChangedDocument: _ =>
                {
                    var newSetter = setter.AddModifiers(SyntaxFactory.Token(SyntaxKind.PrivateKeyword));
                    return Task.FromResult(context.Document.WithSyntaxRoot(root.ReplaceNode(setter, newSetter)));
                },
                equivalenceKey: "make-setter-private"),
            diagnostic);
    }
}
