# BLOCK-WITH-CONCERNS

Direct round-2 fixes are verified: all 7 tests in
`tests/unit/test_codex_blockers_resolved.py` pass, and the full baseline is
green. I cannot sign off because adjacent command paths still preserve the
legacy Copilot copy architecture and Claude settings side effect.

## Blocking Findings

1. Plain `dotnet-ai upgrade` still treats Copilot as a legacy copy host.
   Copilot is render-only (`src/dotnet_ai_kit/agents.py:58-60`;
   `specs/019-plugin-native-arch/spec.md:18`, `:245`), but the normal upgrade
   loop sends non-`PLUGIN_NATIVE_HOSTS` through `copy_commands`/`copy_rules` at
   `src/dotnet_ai_kit/cli.py:1829-1838`. Copilot's legacy config still points
   `commands_dir` at `.github/agents/commands` at
   `src/dotnet_ai_kit/agents.py:36-42`. Repro: temp project with
   `ai_tools: [copilot]` and old `version.txt`; `upgrade --json` exits 0 and
   creates `.github/agents/commands/dai.*.agent.md`. It also creates
   `.claude/settings.json` via `src/dotnet_ai_kit/cli.py:1917-1921` and
   `src/dotnet_ai_kit/copier.py:1341-1345`.

2. `dotnet-ai configure --tools copilot` has the same sibling gap. FR-016 says
   configure writes files only for selected hosts
   (`specs/019-plugin-native-arch/spec.md:173`), and Copilot remains rendered
   repository-native only (`specs/019-plugin-native-arch/spec.md:245`).
   Configure unconditionally applies Claude permissions at
   `src/dotnet_ai_kit/cli.py:2321-2333`, then bulk-copies Copilot commands at
   `src/dotnet_ai_kit/cli.py:2353-2376` and rules/skills/agents at
   `src/dotnet_ai_kit/cli.py:2395-2416`. Repro:
   `configure --no-input --company Acme --tools copilot --permissions minimal --json`
   exits 0 and creates both `.github/agents/commands/` and
   `.claude/settings.json`.

## Checked Clean

- Blocker 1 init path is fixed: `src/dotnet_ai_kit/cli.py:1132-1155`;
  `tests/unit/test_codex_blockers_resolved.py:37-45`.
- Blocker 2 init render-only branch is fixed:
  `src/dotnet_ai_kit/cli.py:150-155`, `:969-995`;
  `tests/unit/test_codex_blockers_resolved.py:53-63`.
- Blocker 3 repo-wide render is no longer placeholder:
  `src/dotnet_ai_kit/hosts/copilot.py:353-467`;
  `agents-copilot-templates/copilot-instructions.md.j2:1-40`.
- Blocker 4 `_should_skip` encodes FR-015 vs FR-022 correctly:
  `src/dotnet_ai_kit/hosts/copilot.py:158-187`;
  `src/dotnet_ai_kit/cli.py:1586-1597`.
- Blocker 5 manifest and freshness are implemented:
  `src/dotnet_ai_kit/cli.py:528-543`, `:3069-3099`;
  `src/dotnet_ai_kit/manifest.py:45-63`.
- Blocker 6 linked-secondary Copilot render path is fixed:
  `src/dotnet_ai_kit/copier.py:1037-1061`.

## Gap Notes

- No sibling placeholder gap found in the Copilot templates:
  `agents-copilot-templates/instructions-path.md.j2:1-22` and
  `agents-copilot-templates/agent.md.j2:1-16`.
- Do not swap check ordering for exit 15. The contract says multiple failures
  use the lowest code, so manifest drift + Copilot stale should exit 14:
  `specs/019-plugin-native-arch/contracts/check-cli.contract.md:31-36`.
  The `(14, 15)` assertion is acceptable but can be tightened to 14.

## Verification Run

- `pytest -q tests/unit/test_codex_blockers_resolved.py` -> 7 passed.
- `pytest --tb=no -q` -> 727 passed, 25 skipped.
- `python scripts/measure_always_on.py` -> 2880 tokens, 68.0% reduction.
- `python scripts/doc_lint.py` -> clean.
