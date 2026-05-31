---
name: analyzer-packaging
description: "Packages a Roslyn analyzer/source-generator into a NuGet under analyzers/dotnet/cs, ships .editorconfig severity defaults, and maintains the analyzer release-tracking files. Use when distributing an analyzer to consumers so it loads via PackageReference with sensible default severities. Do NOT use for writing the analyzer logic itself (use roslyn-analyzer / incremental-source-generator) or for tuning rule severity in a consuming repo (use code-analysis)."
metadata:
  category: "quality"
  agent: "reviewer"
---
# Packaging Roslyn Analyzers as NuGet

## Core Principles

- Analyzer DLLs must land at `analyzers/dotnet/cs/` inside the package, NOT `lib/` — otherwise they ship as a runtime dependency instead of a build-time analyzer.
- Set `<IncludeBuildOutput>false</IncludeBuildOutput>` and `DevelopmentDependency` so the analyzer is never a transitive runtime reference.
- Reference `Microsoft.CodeAnalysis.CSharp` with `PrivateAssets="all"` and pin the *lowest* Roslyn version your consumers' SDK supports.
- Ship default severities via a packaged `.editorconfig`/`.props`, but let consumers override — never hard-code `error`.
- Maintain `AnalyzerReleases.Shipped.md` / `AnalyzerReleases.Unshipped.md`; `RS2008` fails the build if a new `DiagnosticId` is missing from release tracking.

## Packaging Setup

```xml
<!-- Analyzer.csproj -->
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>netstandard2.0</TargetFramework>
    <IncludeBuildOutput>false</IncludeBuildOutput>
    <DevelopmentDependency>true</DevelopmentDependency>
    <SuppressDependenciesWhenPacking>true</SuppressDependenciesWhenPacking>
    <EnforceExtendedAnalyzerRules>true</EnforceExtendedAnalyzerRules>
    <PackageId>MyApp.Analyzers</PackageId>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.CodeAnalysis.CSharp" Version="4.8.0"
                      PrivateAssets="all" />
  </ItemGroup>

  <!-- Place the analyzer DLL in the analyzers path consumers load from. -->
  <ItemGroup>
    <None Include="$(OutputPath)\$(AssemblyName).dll"
          Pack="true" PackagePath="analyzers/dotnet/cs"
          Visible="false" />
    <!-- Ship default severities; consumers can override. -->
    <None Include="build\MyApp.Analyzers.props"
          Pack="true" PackagePath="build" Visible="false" />
  </ItemGroup>

  <ItemGroup>
    <AdditionalFiles Include="AnalyzerReleases.Shipped.md" />
    <AdditionalFiles Include="AnalyzerReleases.Unshipped.md" />
  </ItemGroup>
</Project>
```

```ini
# Default severities shipped with the package (.editorconfig the consumer imports)
dotnet_diagnostic.PROJ001.severity = warning
dotnet_diagnostic.PROJ002.severity = suggestion
```

```markdown
<!-- AnalyzerReleases.Unshipped.md -->
### New Rules
Rule ID | Category | Severity | Notes
--------|----------|----------|------
PROJ001 | Design   | Warning  | Aggregate roots must be sealed
```

## Gotchas

- Forgetting `EnforceExtendedAnalyzerRules` lets reference-type pinning slip through (RS1035 etc.).
- A source generator package needs the *same* `analyzers/dotnet/cs` layout — generators are analyzers.
- When you move a rule from Unshipped to Shipped, copy the row to `AnalyzerReleases.Shipped.md` under the package version heading and delete it from Unshipped.
- Test the *packed* `.nupkg` against a sample consumer project; an analyzer that loads in source but not from NuGet usually means a wrong `PackagePath`.

## References

- https://github.com/dotnet/roslyn-analyzers/blob/main/docs/Analyzer%20Configuration.md
- https://learn.microsoft.com/en-us/visualstudio/extensibility/roslyn-version-support
