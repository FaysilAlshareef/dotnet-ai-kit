# Contract: Python v1 → .NET parity assessment (gates Python removal — FR-020)

Python (`src/dotnet_ai_kit/`) is removed **only** when every v1 CLI capability maps to a covered .NET capability AND the acceptance suite is green. This table is **filled in phase C9** (statuses below are the template; ✅ covered / ⚠️ partial / ❌ gap). Source of truth for v1 verbs: `src/dotnet_ai_kit/cli.py` (surveyed in C9).

| v1 capability | .NET equivalent | Status |
|---|---|---|
| `init` (per-solution footprint + `.claude/rules` with paths) | `InitService` / `init` verb | (C9) |
| `check` (6 check classes → 8 exit codes) | `CheckService` / `check` verb | (C9) |
| `render` (skill/rule + substitution) | `RenderService` / `render` verb | (C9) |
| `migrate` (legacy cleanup + alias) | `MigrateService` / `migrate` verb | (C9) |
| `generate` (projection + drift gate) | `GenerateService` / `generate` verb | (C9) |
| `configure` (config wizard / set) | `ConfigureService` / `configure` verb | (C9) |
| `detect` (architecture/.NET/paths) | `DetectService` / `detect` verb | (C9) |
| `upgrade` (plugin-native no-op / copilot) | `UpgradeService` / `upgrade` verb | (C9) |
| `extension-*` / `learn` (if present in v1) | — assess; map or document gap | (C9) |
| no-network invariant | Acceptance.Tests network-deny | (C9) |
| exit-code contract | Acceptance + Cli exit-code tests | (C9) |
| footprint ≤18 | Acceptance footprint test | (C9) |

## Decision rule
- **All ✅ + acceptance green** → remove `src/dotnet_ai_kit/` + Python `tests/` (separate commit, with CI cutover).
- **Any ⚠️/❌** → retain Python; document the gap here and in tasks.md; do not remove.
