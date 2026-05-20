# Review-Phase: Codex Full Codebase Review

**Date**: 2026-05-18  
**Branch**: `019-plugin-native-arch`  
**Reviewer**: Codex  
**Scope**: Full codebase scan after feature 019 implementation, including spec/task alignment, runtime CLI probes, tests, packaging, lint, docs, and CI gate wiring.

## Verdict

**BLOCKED.**

The feature has a large amount of useful implementation and many tests pass, but it is not release-ready against the feature-19 contract. Several high-priority requirements are represented by schemas/tests/docs but are not wired into the actual CLI behavior. The most important failures are:

1. Plugin-native hosts still get per-solution rule/profile files and a frozen architecture prompt.
2. `config.yml` and `project.yml` are still written in legacy shapes that fail the published feature-19 schemas.
3. `dotnet-ai check` validates those legacy shapes instead of the published schemas.
4. Copilot freshness only checks hash drift against the manifest, so metadata/source staleness passes as healthy.
5. `configure` still offers only Claude in the interactive host picker.
6. The required host smoke gates are skipped locally and not actually invoked by the CI smoke job.
7. Ruff lint/format gates fail.

## Findings

### P0-1: Plugin-native init/upgrade/configure still writes per-solution rule/profile artifacts and freezes architecture constraints

**Requirement violated**: FR-005, FR-006, FR-014, FR-034, SC-001/SC-014 intent.

`init`, `upgrade`, and `configure` still call `copy_profile()` for plugin-native hosts:

- `src/dotnet_ai_kit/cli.py:1094`, `src/dotnet_ai_kit/cli.py:1104`, `src/dotnet_ai_kit/cli.py:1122`
- `src/dotnet_ai_kit/cli.py:1866`, `src/dotnet_ai_kit/cli.py:1876`, `src/dotnet_ai_kit/cli.py:1895`
- `src/dotnet_ai_kit/cli.py:2446`, `src/dotnet_ai_kit/cli.py:2461`, `src/dotnet_ai_kit/cli.py:2478`
- linked secondaries: `src/dotnet_ai_kit/copier.py:1087`, `src/dotnet_ai_kit/copier.py:1109`, `src/dotnet_ai_kit/copier.py:1135`

`copy_profile()` writes a rule file into the repository:

- `src/dotnet_ai_kit/copier.py:545`
- `src/dotnet_ai_kit/copier.py:587`
- `src/dotnet_ai_kit/copier.py:590`

`copy_hook()` then reads that profile body and embeds the full constraints into `.claude/settings.json` as a prompt:

- `src/dotnet_ai_kit/copier.py:597`
- `src/dotnet_ai_kit/copier.py:621`
- `src/dotnet_ai_kit/copier.py:632`

Direct probe:

```text
dotnet-ai init <probe> --ai claude --type generic --json

Files written:
.claude/rules/architecture-profile.md
.claude/settings.json
.dotnet-ai-kit/.gitignore
.dotnet-ai-kit/config.yml
.dotnet-ai-kit/manifest.json
.dotnet-ai-kit/project.yml
.dotnet-ai-kit/version.txt
```

This contradicts `spec.md:153-154`, which says plugin-host init writes only the project metadata, user config, and host settings merge file, and must not copy commands, rules, skills, or agents. It also contradicts FR-034 because the settings prompt freezes the init-time profile body instead of relying only on runtime project metadata.

### P0-2: The CLI writes legacy `config.yml`, not the feature-19 `UserConfig` contract

**Requirement violated**: T003/T004/T005, FR-016, FR-017, config schema contract.

The published schema requires `enabled_hosts` and `plugin_version`, and explicitly says writing `ai_tools` is forbidden in v1:

- `schemas/config-yml.schema.json:7`
- `schemas/config-yml.schema.json:9`

But `init` still writes `DotnetAiConfig(ai_tools=...)`:

- `src/dotnet_ai_kit/cli.py:905`
- `src/dotnet_ai_kit/cli.py:907`
- `src/dotnet_ai_kit/cli.py:910`

Direct probe output:

```yaml
version: '1.0'
company:
  name: ''
...
ai_tools:
- codex
command_style: both
linked_from: null
```

Validating that file against `schemas/config-yml.schema.json` fails:

```text
ValidationError: 'enabled_hosts' is a required property
```

The `UserConfig` model and `save_user_config()` exist, but the primary CLI write paths still use the legacy config model.

### P0-3: The CLI writes and validates legacy `project.yml`, not the feature-19 `ProjectMetadata` contract

**Requirement violated**: FR-009, FR-010, FR-017, FR-034, project schema contract.

The published project schema requires top-level `company`, `domain`, `side`, `project_type`, `architecture_branch`, `detected_paths`, and `dotnet_version`:

- `schemas/project-yml.schema.json:7`

But `save_project()` writes a legacy nested `detected:` object from `DetectedProject`:

- `src/dotnet_ai_kit/config.py:127`
- `src/dotnet_ai_kit/config.py:132`
- `src/dotnet_ai_kit/config.py:144`

Direct probe output:

```yaml
detected:
  mode: generic
  project_type: generic
  dotnet_version: ''
  detected_paths: null
  ...
```

Validating this emitted file against `schemas/project-yml.schema.json` fails:

```text
ValidationError: 'company' is a required property
```

`dotnet-ai check` still calls `load_project()` and reports this same schema-invalid file as `project_yml_schema: pass`:

- `src/dotnet_ai_kit/cli.py:2962`
- `src/dotnet_ai_kit/cli.py:3045`
- `src/dotnet_ai_kit/cli.py:3046`

So the validation command does not enforce the schema it publishes.

### P1-1: Copilot freshness misses metadata and plugin-source staleness

**Requirement violated**: US2 acceptance scenario 3, FR-017, SC-006, CHK016.

The check implementation only compares current rendered file hashes to the manifest hash:

- `src/dotnet_ai_kit/cli.py:3093`
- `src/dotnet_ai_kit/cli.py:3110`
- `src/dotnet_ai_kit/cli.py:3116`
- `src/dotnet_ai_kit/cli.py:3117`

It never re-renders from the current plugin source/current project metadata into memory for comparison, and the manifest does not record the source/template metadata needed to know whether a render is stale.

Direct probe:

1. Render Copilot instructions with `company: Acme`.
2. Change `.dotnet-ai-kit/project.yml` to `company: Globex`.
3. Do not run `upgrade --copilot`.
4. Run `dotnet-ai check <probe> --host copilot --json`.

Observed:

```json
{
  "exit_code": 0,
  "checks": [
    { "name": "copilot_freshness", "status": "pass" }
  ]
}
```

But `.github/copilot-instructions.md` still contained:

```text
- **company**: Acme
```

This is exactly the stale-render case feature 19 says `check` must catch.

### P1-2: `configure` interactive host selection still only lists Claude

**Requirement violated**: FR-016, CHK037.

The interactive configure flow has a comment saying "v1.0: Claude only" and creates one checkbox choice:

- `src/dotnet_ai_kit/cli.py:2286`
- `src/dotnet_ai_kit/cli.py:2288`
- `src/dotnet_ai_kit/cli.py:2292`
- `src/dotnet_ai_kit/cli.py:2293`

The test coverage only checks `_prompt_for_hosts()` used by `init`, not the actual `configure` interactive flow. This means FR-016 is not satisfied.

### P1-3: Required smoke fixtures are not actually enforced by CI

**Requirement violated**: FR-029, SC-008, CHK001-CHK004, CHK011/CHK012 process gate.

The feature-19 smoke tests are in `tests/integration/test_smoke_{claude,codex,cursor,claude_lsp}.py` and are gated by host-specific environment variables:

- `tests/integration/test_smoke_claude.py:21`
- `tests/integration/test_smoke_codex.py:21`
- `tests/integration/test_smoke_cursor.py:26`

Local pytest result showed all four feature-19 integration smoke tests skipped.

CI's smoke job only sets `CLAUDE_CODE_SMOKE=1` and runs `tests/smoke`, not the feature-19 integration smoke files:

- `.github/workflows/ci.yml:72`
- `.github/workflows/ci.yml:87`
- `.github/workflows/ci.yml:88`

The Cursor spike source of truth is still pending:

- `specs/019-plugin-native-arch/discussion/tasks-phase/cursor-subagent-outcome.json:2`

Release notes explicitly assume the pass branch while still pending:

- `docs/release-notes-v1.0.md:106`
- `docs/release-notes-v1.0.md:107`
- `docs/release-notes-v1.0.md:112`
- `docs/release-notes-v1.0.md:117`

This is a release gate, not just a process note. The spec says the release must not quietly ship Cursor support if the fixture has not passed.

### P1-4: Verification checklist remains unchecked

`specs/019-plugin-native-arch/checklists/verification.md` still has all CHK001-CHK063 boxes unchecked. This conflicts with the tasks file's final checkpoint language saying all CHK items are checked off. Even if some are tested elsewhere, the formal review checklist is not in a release-ready state.

### P2-1: Ruff gates fail

Commands run:

```text
.venv\Scripts\ruff.exe check src/ tests/
.venv\Scripts\ruff.exe format --check src/ tests/
```

Results:

- `ruff check`: 48 errors
- `ruff format --check`: 55 files would be reformatted

Representative failures:

- `src/dotnet_ai_kit/agent_generators.py:24` import ordering
- `src/dotnet_ai_kit/cli.py:990` and `src/dotnet_ai_kit/cli.py:991` f-strings without placeholders
- `src/dotnet_ai_kit/manifest.py:298` line too long
- `src/dotnet_ai_kit/render.py:15` unused import

Because CI runs both ruff checks in `.github/workflows/ci.yml`, the branch would fail the static-unit job.

## Verification Performed

### Passing checks

```text
uv run pytest
704 passed, 50 skipped in 68.15s
```

```text
uv run --with build pytest tests/test_packaging.py
13 passed in 11.89s
```

```text
python scripts/doc_lint.py
[OK] Doc-lint passed (24 files scanned).
```

```text
python scripts/check.py --static-only
[OK] Static config check passed (plugin manifests + multi-host config).
```

### Failed or incomplete checks

```text
ruff check src/ tests/
48 errors
```

```text
ruff format --check src/ tests/
55 files would be reformatted
```

Skipped in local full pytest:

- macOS/Windows packaging variants
- Claude/Codex/Cursor/LSP integration smoke tests
- several host CLI smoke tests
- Windows bash-hook tests

Packaging was separately re-run with `build` installed and passed on this Windows environment.

## Recommended Fix Order

1. Remove `copy_profile()` and frozen `copy_hook()` writes from plugin-native init/upgrade/configure/linked-secondary paths. Rely on plugin hooks plus runtime `.dotnet-ai-kit/project.yml` resolution.
2. Convert the primary config writer to `UserConfig` (`enabled_hosts`, `retention`, `permission_profile`, `plugin_version`) or revise the schema/spec if the legacy `DotnetAiConfig` shape is intentionally retained.
3. Convert project metadata read/write/check to `ProjectMetadata` and validate against `schemas/project-yml.schema.json`.
4. Fix Copilot freshness to compare rendered output from current plugin source + current metadata, or record enough render provenance to detect template/metadata drift.
5. Update `configure` interactive host picker to list all four supported hosts.
6. Wire CI smoke job to run `tests/integration/test_smoke_claude.py`, `test_smoke_codex.py`, `test_smoke_cursor.py`, and `test_smoke_claude_lsp.py` with the needed env vars, or mark unsupported hosts out of scope before release.
7. Resolve ruff check and formatting failures.
8. Update `verification.md` checkboxes only after the corresponding automated or manual gate has actually passed.

## Final Note

The implementation is close in surface area but not in release semantics. The strongest evidence is that `pytest` passes while direct CLI probes produce schema-invalid state and stale Copilot output that `dotnet-ai check` reports as healthy. Feature 19 should not merge until those runtime paths are corrected.
