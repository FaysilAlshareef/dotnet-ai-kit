# Quickstart: dotnet-ai-kit v2 (author → generate → init → check)

This walkthrough exercises the convergence anchor (US1 + US2) end-to-end.

## Prerequisites
- .NET 10 SDK (`dotnet --version` → 10.0.300)
- Git

## 1. Build the solution
```bash
dotnet build dotnet-ai-kit.slnx
dotnet test           # Core/Application/Hosts/Cli/Analyzers/Acceptance suites green
```

## 2. Author an artifact once
Add a skill under the single source of truth:
```
artifacts/skills/api/minimal-api-patterns/SKILL.md
```
Frontmatter uses portable core fields + optional `x-claude` block; body ≤500 lines; description follows the standard (action-first + "Use when…" + "Do NOT use… use X").

## 3. Generate every host's outputs
```bash
dotnet run --project src/DotnetAiKit.Cli -- generate --out build/
git diff --exit-code build/        # MUST be clean → no drift (SC-001)
```
Delete a generated file and regenerate — it returns byte-identically:
```bash
rm build/claude/skills/minimal-api-patterns/SKILL.md
dotnet run --project src/DotnetAiKit.Cli -- generate --out build/
git status --short build/           # restored, no diff
```

## 4. Initialize a target solution (the rule-delivery fix)
```bash
cd /path/to/some/dotnet/solution
dotnet-ai init --host claude
ls .claude/rules/                   # domain rules present, each with `paths:` frontmatter (SC-002)
cat .dotnet-ai-kit/project.yml      # detected metadata; footprint within bound (SC-011)
```

## 5. Validate
```bash
dotnet-ai check                     # read-only; exit 0 when healthy (see contracts/exit-codes.md)
dotnet-ai check --json              # machine-readable report; < 10 s (SC-010)
```

## 6. Render a single artifact with project metadata
```bash
dotnet-ai render skill minimal-api-patterns   # tokens like ${Company} substituted; < 2 s
```

## What this proves
- **SC-001** drift gate (step 3), **SC-002** rule delivery (step 4), **SC-003** build/tests green (step 1), **SC-007** acceptance contract (`check` exit codes, no-network), **SC-010/011** performance + footprint.

## No-network guarantee
`init`, `check`, `render`, `migrate`, `generate` make zero network calls — enforced by a process-level network-deny acceptance test (FR-015).
