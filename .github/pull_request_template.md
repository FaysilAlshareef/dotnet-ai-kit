## Summary

<!-- Brief description of what this PR does (1-3 sentences) -->

## Changes

<!-- List key changes. Use checkboxes for multi-part PRs -->

- [ ] ...

## Type

<!-- Check one -->

- [ ] Bug fix
- [ ] New feature
- [ ] Enhancement
- [ ] Refactoring
- [ ] Documentation
- [ ] Tests

## Testing

<!-- How was this tested? -->

- [ ] `dotnet build dotnet-ai-kit.slnx -warnaserror` clean (0/0)
- [ ] `dotnet test dotnet-ai-kit.slnx` passes
- [ ] `dotnet format dotnet-ai-kit.slnx --verify-no-changes` clean
- [ ] `dotnet run --project src/DotnetAiKit.Cli -- generate --check` drift-clean
- [ ] Cross-platform verified (Windows / macOS / Linux)

## Breaking Changes

<!-- Does this change break existing behavior? If yes, describe the migration path -->

None

## Checklist

- [ ] Code follows project conventions (clean/hexagonal layers; Core stays pure)
- [ ] Token budgets respected (rules ≤ 100 lines, agents ≤ 120, skills ≤ 500)
- [ ] Skill descriptions meet the standard (verb-first + "Use when…" + "Do NOT use… (use <sibling>)")
- [ ] Tests added for new functionality (acceptance coverage for policies/projectors)
- [ ] Documentation updated if needed
