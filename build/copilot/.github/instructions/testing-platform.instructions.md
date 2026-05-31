---
applyTo: "**/*Tests*/**/*.cs,**/*.Tests.csproj"
---
# Testing Platform (domain)

Standardize how tests run (the platform), distinct from how tests are written (see `testing`).

## MUST
- Use Microsoft.Testing.Platform (MTP) for new test projects where supported; configure consistently across the solution.
- Keep runner configuration in the test project / Directory.Build.props, not ad hoc.
- Ensure `dotnet test` and CI use the same runner config.

## SHOULD
- Prefer MTP-native frameworks (xUnit v3 / TUnit) when adopting MTP; flag pre-1.0 maturity.
