---
name: code-analysis
description: >
  Use when configuring Roslyn analyzers, StyleCop, or EditorConfig for static analysis.
metadata:
  category: quality
  agent: reviewer
  when-to-use: "When configuring static code analysis, Roslyn analyzers, or EditorConfig rules"
---

# Code Analysis — Roslyn Analyzers & EditorConfig

## Core Principles

- Roslyn analyzers catch issues at compile time
- `.editorconfig` enforces consistent code style across the team
- `Directory.Build.props` enables analyzers for all projects
- `TreatWarningsAsErrors` in CI prevents degradation
- StyleCop.Analyzers for naming and formatting rules
- `EnforceCodeStyleInBuild` enables style warnings during build

## Key Patterns

### EditorConfig

```ini
# .editorconfig (solution root)
root = true

[*]
indent_style = space
indent_size = 4
end_of_line = crlf
charset = utf-8-bom
trim_trailing_whitespace = true
insert_final_newline = true

[*.cs]
# Namespace
csharp_style_namespace_declarations = file_scoped:warning

# Using directives
dotnet_sort_system_directives_first = true
csharp_using_directive_placement = outside_namespace:warning

# var preferences
csharp_style_var_for_built_in_types = true:suggestion
csharp_style_var_when_type_is_apparent = true:suggestion
csharp_style_var_elsewhere = true:suggestion

# Expression-bodied members
csharp_style_expression_bodied_methods = when_on_single_line:suggestion
csharp_style_expression_bodied_properties = true:suggestion

# Null checking
dotnet_style_prefer_is_null_check_over_reference_equality_method = true:warning

# Naming conventions
dotnet_naming_rule.private_fields.symbols = private_fields
dotnet_naming_rule.private_fields.style = _camelCase
dotnet_naming_rule.private_fields.severity = warning

dotnet_naming_symbols.private_fields.applicable_kinds = field
dotnet_naming_symbols.private_fields.applicable_accessibilities = private

dotnet_naming_style._camelCase.required_prefix = _
dotnet_naming_style._camelCase.capitalization = camel_case

# Analyzer severity
dotnet_diagnostic.CA1062.severity = warning  # Validate arguments
dotnet_diagnostic.CA1822.severity = suggestion  # Mark static
dotnet_diagnostic.CA2007.severity = none  # ConfigureAwait
```

### Directory.Build.props Analyzer Configuration

```xml
<Project>
  <PropertyGroup>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>
    <AnalysisLevel>latest-recommended</AnalysisLevel>
    <EnableNETAnalyzers>true</EnableNETAnalyzers>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="StyleCop.Analyzers" Version="1.2.0-beta.556">
      <PrivateAssets>all</PrivateAssets>
      <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
    </PackageReference>
    <PackageReference Include="Meziantou.Analyzer" Version="2.0.182">
      <PrivateAssets>all</PrivateAssets>
    </PackageReference>
  </ItemGroup>
</Project>
```

### StyleCop Configuration

```json
// stylecop.json (solution root)
{
  "$schema": "https://raw.githubusercontent.com/DotNetAnalyzers/StyleCopAnalyzers/master/StyleCop.Analyzers/StyleCop.Analyzers/Settings/stylecop.schema.json",
  "settings": {
    "documentationRules": {
      "companyName": "{Company}",
      "xmlHeader": false,
      "documentInterfaces": false,
      "documentPrivateElements": false
    },
    "orderingRules": {
      "usingDirectivesPlacement": "outsideNamespace"
    }
  }
}
```

### Suppressing False Positives

```csharp
// Targeted suppression (prefer over global)
[SuppressMessage("Style", "IDE0057",
    Justification = "Range operator less readable here")]
public string GetPrefix(string value) => value.Substring(0, 3);

// Global suppression file
// GlobalSuppressions.cs
[assembly: SuppressMessage("Design", "CA1062",
    Scope = "namespaceanddescendants",
    Target = "~N:{Company}.{Domain}.Tests")]
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Disabling all warnings | Fix warnings or suppress with justification |
| No .editorconfig | Create one at solution root |
| Analyzers only in CI | Enable in IDE and build |
| Global suppressions without justification | Always include Justification |

## Detect Existing Patterns

```bash
# Find .editorconfig
find . -name ".editorconfig" -type f

# Find analyzer packages
grep -r "StyleCop\|Meziantou\|Roslynator" --include="*.csproj" .
grep -r "StyleCop\|Meziantou\|Roslynator" --include="*.props" .

# Find TreatWarningsAsErrors
grep -r "TreatWarningsAsErrors" --include="*.props" --include="*.csproj" .
```

## Adding to Existing Project

1. **Check for existing `.editorconfig`** — extend, don't replace
2. **Match existing analyzer configuration** in `Directory.Build.props`
3. **Don't enable `TreatWarningsAsErrors`** without fixing existing warnings
4. **Add analyzers gradually** — start with recommended level
5. **Run `dotnet format`** to auto-fix formatting issues
