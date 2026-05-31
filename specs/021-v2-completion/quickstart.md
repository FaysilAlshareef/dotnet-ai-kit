# Quickstart: v2 Completion verification

Exercises the completion end-to-end (after C1–C7).

## 1. Build + test
```bash
dotnet build dotnet-ai-kit.slnx -warnaserror
dotnet test dotnet-ai-kit.slnx          # incl. the corpus-integrity test over the full corpus
```

## 2. Corpus loads + projects (no drift)
```bash
dotnet run --project src/DotnetAiKit.Cli -- generate --out build/
dotnet run --project src/DotnetAiKit.Cli -- generate --check --out build/   # exit 0, no drift, all 4 hosts
git diff --exit-code build/
```

## 3. Corpus integrity (the high-coverage gate)
The `CorpusIntegrityTests` assert — for every artifact — load + name==dir + graph-consistent + 4-host projection, and report the migrated DescriptionStandard-compliance count.

## 4. Restructure is clean
```bash
ls skills commands rules agents profiles knowledge 2>/dev/null || echo "v1 dirs removed (single source = artifacts/)"
dotnet run --project src/DotnetAiKit.Cli -- check .   # still valid
```

## 5. Plugin setup
Inspect `build/.claude-plugin/plugin.json` (real corpus counts, no auto-discovered keys) + `build/marketplace.json` (project-scoped, pinned). Exactly one authoritative generated manifest per host.

## 6. Docs + CI
README/CLAUDE.md/docs describe the v2 .NET tool. `.github/workflows/*` build/test/format/drift-gate the .NET solution; no Python dependency.

## 7. Parity (gates Python removal)
`contracts/parity-assessment.md` maps every v1 verb → .NET; Python removed only if all covered.

## What this proves
SC-001 (corpus + drift), SC-002 (integrity test), SC-003 (warnings/format/vuln + tests), SC-004 (restructure), SC-005 (one manifest), SC-006 (deferred features), SC-007 (docs), SC-008 (CI), SC-009 (parity), SC-010 (baseline new skills).
