using System.Collections.Immutable;
using System.Linq;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.Diagnostics;

namespace DotnetAiKit.Analyzers;

/// <summary>DAK0004: flags public property setters on aggregate types (type name ends with "Aggregate").
/// Aggregate state must be mutated only through methods that raise events (add-aggregate rule, FR-022).</summary>
[DiagnosticAnalyzer(LanguageNames.CSharp)]
public sealed class AggregateEncapsulationAnalyzer : DiagnosticAnalyzer
{
    public const string DiagnosticId = "DAK0004";

    private static readonly DiagnosticDescriptor Rule = new(
        id: DiagnosticId,
        title: "No public setters on aggregates",
        messageFormat: "Property '{0}' on aggregate '{1}' has a public setter; mutate aggregate state only through methods that raise events",
        category: "Design",
        defaultSeverity: DiagnosticSeverity.Warning,
        isEnabledByDefault: true,
        description: "Event-sourced aggregates encapsulate state; public setters break the invariant. Paired with the add-aggregate skill.");

    public override ImmutableArray<DiagnosticDescriptor> SupportedDiagnostics => ImmutableArray.Create(Rule);

    public override void Initialize(AnalysisContext context)
    {
        context.EnableConcurrentExecution();
        context.ConfigureGeneratedCodeAnalysis(GeneratedCodeAnalysisFlags.None);
        context.RegisterSyntaxNodeAction(Analyze, SyntaxKind.PropertyDeclaration);
    }

    private static void Analyze(SyntaxNodeAnalysisContext context)
    {
        var property = (PropertyDeclarationSyntax)context.Node;
        if (property.Parent is not TypeDeclarationSyntax type)
            return;
        if (!type.Identifier.Text.EndsWith("Aggregate", System.StringComparison.Ordinal))
            return;

        var setter = property.AccessorList?.Accessors
            .FirstOrDefault(a => a.IsKind(SyntaxKind.SetAccessorDeclaration));
        if (setter is null)
            return;

        // A setter with no explicit accessibility modifier inherits the property's — public here triggers.
        var setterIsRestricted = setter.Modifiers.Any(m =>
            m.IsKind(SyntaxKind.PrivateKeyword) || m.IsKind(SyntaxKind.ProtectedKeyword) || m.IsKind(SyntaxKind.InternalKeyword));
        var propertyIsPublic = property.Modifiers.Any(m => m.IsKind(SyntaxKind.PublicKeyword));
        if (propertyIsPublic && !setterIsRestricted)
            context.ReportDiagnostic(Diagnostic.Create(
                Rule, setter.GetLocation(), property.Identifier.Text, type.Identifier.Text));
    }
}
