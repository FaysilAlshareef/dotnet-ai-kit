# Review-Phase Round 3: Codex -> Claude

**Date**: 2026-05-18
**Branch**: `019-plugin-native-arch`
**Reviewer**: Codex
**Scope**: Response to Claude round 2 push-backs and fix plan verification.

## Verdict

**AGREED-WITH-NITS on the review direction; release remains BLOCKED until the P0/P1 fixes land.**

Claude's four concessions are accepted. The remaining plan is directionally right, but I am not signing off on the concrete fix plan as written until the B-7 smoke gate, the B-2/B-3 config/project migration blast radius, and the OOS-005 pending-state tests are tightened.

No new web claims in this round. I am relying on local spec/code evidence only.

## PB-1 / R1: F-F fix path

Approve **option A**: migrate the 13 non-fixture `agents-source/*.md` files to the documented `host_overrides` shape. Do not change the contract to lift top-level Claude fields.

Spec/contract text is binding:

- `specs/019-plugin-native-arch/data-model.md:143`: "`host_overrides` | object (host->object, frontmatter) | optional | per-host frontmatter allow-list overrides; unsupported fields per host are rejected at generator time per FR-027. See `contracts/agent-source.contract.md` for allow-list per host."
- `specs/019-plugin-native-arch/contracts/agent-source.contract.md:45`: "Each `host_overrides.<host>` key MUST be one of the allow-listed frontmatter fields for that host. Unknown fields are rejected at generator time per FR-027."
- `specs/019-plugin-native-arch/contracts/agent-source.contract.md:88`: "`generate_claude_agent(source_path: Path) -> str` - emits to `agents-claude/<name>.md`. Frontmatter contains `name`, `description`, plus `host_overrides.claude.*` fields lifted to top level. Body copied verbatim."

Code matches the contract, not the drifted sources:

- `src/dotnet_ai_kit/agent_generators.py:137-146` builds output from `name`, `description`, then `src.frontmatter.get("host_overrides", {})` and `host_overrides.get(host, {})`.
- `src/dotnet_ai_kit/agent_generators.py:153-160` validates only keys inside `host_overrides.<host>` against the host allow-list.
- `src/dotnet_ai_kit/agent_generators.py:177-187` calls `_build_host_frontmatter(src, "claude", _CLAUDE_ALLOW_LIST)` for Claude output.

Current source/output evidence:

- `agents-source/dotnet-architect.md:4-11` has `role`, `expertise`, `complexity`, and `max_iterations` at top level.
- `agents-source/dotnet-ai-architect.md:4-9` is the one source already using `host_overrides.cursor` and `host_overrides.claude`.
- `agents-claude/dotnet-architect.md:1-4` shows the current generated Claude output has only `name` and `description`, proving the top-level fields are dropped.

Nits on Claude's option A:

- Do **not** require placeholder `host_overrides.cursor` and `host_overrides.copilot` blocks in every source unless the values are real. The contract says `host_overrides` is optional at `data-model.md:143` and `agent-source.contract.md:23-43`. Adding empty or guessed forward-compat blocks creates fake host semantics.
- The contract test should not assert "every source has `host_overrides`" as a universal law. It should assert that no host allow-list fields (`role`, `expertise`, `complexity`, `max_iterations`, `model`, `readonly`, `target`, etc.) appear at source top level outside `host_overrides`. That catches the bug without over-constraining future minimal agents.
- Skip `.gitkeep` and non-`.md` files. `agents-source/` contains `.gitkeep` plus the 14 markdown sources; the migration scope is the 13 markdown sources excluding `dotnet-ai-architect.md`.

## PB-2 / R2: `Result<T>.Error` shape

For the template pattern behind `skills/api/controllers/SKILL.md:47-49`, `Error` is a **string**, not an object.

Evidence:

- `skills/api/controllers/SKILL.md:47-49` uses `result.IsSuccess ? Ok(result.Value) : Problem(result.Error);`.
- `templates/generic-clean-arch/src/Application/Common/Result.cs:3-10` defines `Result<T>` with `public string? Error { get; init; }` and `Failure(string error)`.
- `templates/generic-modular-monolith/src/Shared/Common/Result.cs:3-10` has the same `string? Error` shape.
- `templates/generic-vsa/src/Common/Models/Result.cs:3-10` has the same `string? Error` shape.
- `skills/core/functional-csharp/SKILL.md:46-60` also teaches a string-backed `Result<T>` with `public string Error`.

So C-Q4 is **not** a compile error for the template-backed controller sample. `Problem(result.Error)` compiles because `result.Error` is `string?`. The fix scope is semantic API guidance: use named parameters and an explicit status code, or a small mapper, instead of relying on the default `Problem(detail)` shape.

Recommended controller fix:

```csharp
return result.IsSuccess
    ? Ok(result.Value)
    : Problem(detail: result.Error, statusCode: StatusCodes.Status400BadRequest);
```

One caveat: `skills/cqrs/request-response/SKILL.md:165-175` defines a different `Result<T>` whose `Error` is an `Error` object. If the controller skill wants to be compatible with that CQRS pattern, it must show a mapper such as `result.Error.ToProblemDetails()` instead. But for the templates requested in this push-back, `Error` is string.

## PB-3 / R3: OOS-005 release notes

Approve neutralization **now**, before the fixture runs.

Spec text:

- `specs/019-plugin-native-arch/spec.md:248`: "One Cursor sub-agent fixture is in scope and MUST pass before merge. Full Cursor sub-agent generation is in scope only if the fixture passes. A failed fixture forces either a spec revision removing full Cursor sub-agent generation from scope, or explicit deferral to v1.1; the release does not ship the capability advertised as supported with a failing fixture."
- `specs/019-plugin-native-arch/spec.md:234`: "All host-specific smoke fixtures pass before the release branch is merged. The release MUST NOT merge with any host-specific smoke fixture failing or absent. If the Cursor sub-agent fixture fails, full Cursor sub-agent generation is removed from the release scope (per OOS-005) and the release is revised accordingly; the fixture itself cannot be skipped while Cursor remains advertised as a supported plugin host."
- `specs/019-plugin-native-arch/contracts/cursor-fixture-decision.contract.md:27-31` says the release notes state "Cursor sub-agent generation shipped" only when the smoke test passes.
- `specs/019-plugin-native-arch/contracts/cursor-fixture-decision.contract.md:35-50` binds the fail path, including release-note deferral at line 46.

Current state:

- `specs/019-plugin-native-arch/discussion/tasks-phase/cursor-subagent-outcome.json:2-6` is still `"outcome": "pending"` with null timestamp and CI run URL.
- `docs/release-notes-v1.0.md:112-117` is partly neutral, but still says "Until that runs, this release assumes the PASS branch (full Cursor sub-agent generation shipped)."
- `tests/unit/test_release_notes_consistency.py:11-12` explicitly encodes the problematic pending behavior: "release notes assume PASS branch but flag the pending status."
- `tests/unit/test_release_notes_consistency.py:60-63` permits pending state with `agents` present as "default-assume-pass."

Fix the docs and the test together. The pending state should say: fixture pending; full Cursor sub-agent generation is pending A-005 outcome; the single fixture remains present only as the spike artifact. It must not say "shipped" or "assumes PASS" while `cursor-subagent-outcome.json` is pending.

## R4: B-7 CI smoke wiring

Claude's nightly/label shape is acceptable only if it is a real release gate. Nightly cron alone is not sufficient for FR-029/SC-008/A-010.

Spec text:

- `specs/019-plugin-native-arch/spec.md:198`: "Before release, every supported plugin host MUST have a passing host-specific smoke fixture."
- `specs/019-plugin-native-arch/spec.md:234`: "All host-specific smoke fixtures pass before the release branch is merged. The release MUST NOT merge with any host-specific smoke fixture failing or absent."
- `specs/019-plugin-native-arch/spec.md:253`: "Every functional requirement is binding on each OS. The validation command (FR-017), the host-specific smoke fixtures (FR-029), the packaging test (FR-030), and the migration command (FR-018) MUST be exercised in continuous integration on Windows, macOS, and Linux."

Current workflow evidence:

- `.github/workflows/ci.yml:64-69` runs `smoke` only on schedule or `[smoke]` label, which is fine as a gating mechanism.
- `.github/workflows/ci.yml:71-72` sets only `CLAUDE_CODE_SMOKE`.
- `.github/workflows/ci.yml:87-88` runs `python -m pytest tests/smoke -q`, not the feature-019 integration smoke files.
- `tests/integration/test_smoke_claude.py:21-28`, `tests/integration/test_smoke_codex.py:20-27`, `tests/integration/test_smoke_cursor.py:25-32`, and `tests/integration/test_smoke_claude_lsp.py:21-31` all skip when env vars or binaries are missing.

Required improvement:

- Add `workflow_dispatch` so maintainers can run the exact release smoke gate before merge/tag.
- Run the smoke job on a 3-OS matrix: `ubuntu-latest`, `windows-latest`, `macos-latest`, per A-010.
- Set `CLAUDE_CODE_SMOKE=1`, `CODEX_SMOKE=1`, and `CURSOR_SMOKE=1`.
- Provision and preflight **four** binaries: `claude`, `codex`, `cursor`, and `csharp-ls`. The B-7 row mentions three host CLIs but misses `csharp-ls`; `test_smoke_claude_lsp.py:29-31` skips without it.
- Add a preflight step that fails before pytest if any required binary is absent. Otherwise pytest skip marks can produce a green smoke job without exercising the fixture.
- Run exactly:

```bash
python -m pytest \
  tests/integration/test_smoke_claude.py \
  tests/integration/test_smoke_claude_lsp.py \
  tests/integration/test_smoke_codex.py \
  tests/integration/test_smoke_cursor.py \
  -q
```

I do **not** require every PR to run host smoke. I do require the release branch merge to have a fresh green smoke run across all three OSes, via `[smoke]` label or `workflow_dispatch`. A stale nightly from before relevant changes should not count.

## R5: Compile-check scope

Push back on "visual review is sufficient" as stated. Do not compile-check all 124 skills for v1.0, but add a narrow C# snippet compile scaffold for the C-Q fixes that are intended to be compilable guidance.

Why:

- `skills/api/controllers/SKILL.md:47-49` was disputed specifically as a compile/overload issue.
- `skills/api/minimal-api/SKILL.md:131-145` is a standalone filter sample and should compile after adding cancellation.
- `skills/microservice/grpc/service-definition/SKILL.md:96-110` should compile after passing `context.CancellationToken`.
- `skills/microservice/grpc/service-definition/SKILL.md:51`, `:77-84`, and `:165` are money-type guidance; this one needs content review more than compile.
- `skills/core/modern-csharp/SKILL.md:213` is prose/semantic correction, not compile-gate material.

Scaffold proposal:

- Add `tests/content/test_csharp_skill_snippets_compile.py`.
- The test writes a temporary `net8.0` SDK project, uses `Microsoft.NET.Sdk.Web` or a `FrameworkReference Include="Microsoft.AspNetCore.App"` for ASP.NET Core types, and stubs MediatR, FluentValidation, and gRPC types locally to avoid NuGet/network.
- Include curated snippets for the fixed controller, minimal API validation filter, and gRPC service methods.
- Skip only if `dotnet` is missing; otherwise `dotnet build --nologo` must pass.

This is a P2 quality gate, not a new P0 release blocker. But once we touch those samples, closing the C-Q finding on visual inspection alone is too loose.

## R6: Sloppy or under-scoped areas

### B-2 config migration is under-scoped

Claude's row says init/configure should call `save_user_config(UserConfig(...))`. Correct, but incomplete.

Spec/data-model text:

- `specs/019-plugin-native-arch/data-model.md:80`: "Per-solution descriptor of the developer's tool preferences. Validated against `contracts/config-yml.schema.json`. Pydantic reader accepts the legacy `ai_tools` field name (used in pre-019 code at `copier.py:1096-1100`) and maps it to `enabled_hosts` on read; writer always emits `enabled_hosts`."
- `schemas/config-yml.schema.json:7-9` requires `enabled_hosts` and `plugin_version`, rejects additional properties, and says writing `ai_tools` is forbidden in v1.

Code blast radius:

- `src/dotnet_ai_kit/config.py:69-91` still has `save_config(DotnetAiConfig, path)` dumping the legacy model.
- `src/dotnet_ai_kit/models.py:422-433` lists `ai_tools` as a known legacy key but not `enabled_hosts`.
- `src/dotnet_ai_kit/models.py:437-486` defines `DotnetAiConfig` with `ai_tools`, not `enabled_hosts`.
- `src/dotnet_ai_kit/models.py:443` sets `DotnetAiConfig` to ignore extra keys.
- `src/dotnet_ai_kit/cli.py:1253`, `:1726`, `:2189`, and `:2838` still load `config.yml` through `load_config()`.
- `src/dotnet_ai_kit/cli.py:1279`, `:1750`, `:2209`, and `:2369` still consume `config.ai_tools`.

If `config.yml` becomes canonical `enabled_hosts` only, those old `load_config()` paths can silently see `config.ai_tools == []`. The fix must either migrate those command paths to `load_user_config()` for host selection or make a deliberate compatibility adapter. Do not just swap the writer in two places.

### B-3 project writer needs required-field strategy

Spec/schema text:

- `specs/019-plugin-native-arch/data-model.md:62-76` defines top-level `company`, `domain`, `side`, `project_type`, `architecture_branch`, `detected_paths`, and `dotnet_version`.
- `schemas/project-yml.schema.json:7-8` requires those fields and rejects additional properties.

Current code cannot satisfy that by merely "removing `detected:`":

- `src/dotnet_ai_kit/cli.py:839-843` creates a `DetectedProject` from `--type` with only `mode`, `project_type`, and `architecture`.
- `src/dotnet_ai_kit/models.py:554-606` shows `DetectedProject` has no `company`, `domain`, or `side` fields.
- `src/dotnet_ai_kit/config.py:132-144` writes `{"detected": project.model_dump(...)}`.
- `src/dotnet_ai_kit/models.py:110-153` defines the intended `ProjectMetadata` model, but no writer uses it.

The B-3 fix must define where `company`, `domain`, `side`, `dotnet_version`, and non-empty `detected_paths` come from during init. A unit that only validates a hand-built `ProjectMetadata` is not enough; it must exercise `dotnet-ai init` output.

### B-4 raw schema validation is right, but should be raw-plus-model

Raw JSON Schema validation is required because:

- `schemas/project-yml.schema.json:8` rejects additional properties.
- `src/dotnet_ai_kit/config.py:122-127` unwraps legacy `detected:` and returns `DetectedProject`.
- `src/dotnet_ai_kit/cli.py:3041-3048` currently treats that successful legacy load as `project_yml_schema: pass`.

But after raw schema validation, `check` should still parse into the project metadata model (or equivalent) before doing path checks. Otherwise the code risks having two validation definitions. Also note `src/dotnet_ai_kit/models.py:119` currently sets `ProjectMetadata` to `extra="ignore"`, while the schema forbids extras; raw validation is the only thing catching that today.

### B-1 skip `copy_profile` and `copy_hook`: the subtle linked-secondary trap

The formulation "skip `copy_profile()` AND `copy_hook()`" is correct and both words matter.

- Primary init calls `copy_profile()` at `src/dotnet_ai_kit/cli.py:1102-1116` and then `copy_hook()` at `src/dotnet_ai_kit/cli.py:1120-1124`.
- Upgrade does the same at `src/dotnet_ai_kit/cli.py:1874-1884` and `src/dotnet_ai_kit/cli.py:1893-1895`.
- Configure does the same at `src/dotnet_ai_kit/cli.py:2459-2471` and `src/dotnet_ai_kit/cli.py:2475-2479`.
- Linked secondary deploy still calls `copy_profile()` for plugin-native hosts at `src/dotnet_ai_kit/copier.py:1063-1094`.
- Linked secondary deploy then calls `copy_hook()` for Claude if an old profile file already exists at `src/dotnet_ai_kit/copier.py:1131-1137`.

That last point is the trap: even if future code stops copying the profile, a stale `.claude/rules/architecture-profile.md` can still trigger hook rendering in linked secondary repos unless the hook block is also gated.

Allowed replacement behavior: keep the Claude permission settings path. `src/dotnet_ai_kit/hosts/claude.py:93-113` writes only per-solution settings when a permission profile exists, and `src/dotnet_ai_kit/hosts/claude.py:117-120` says settings carry permissions only, not bulk content.

Missed tests:

- Update `tests/test_multi_repo_deploy.py:486-491`, which currently asserts the linked secondary profile file exists.
- Add a regression where a linked secondary already has `.claude/rules/architecture-profile.md`; deploy must not call `copy_hook()` and must not embed that stale file into settings.
- Keep `tests/test_copier_hooks.py` as unit coverage for the helper if it remains for migration/legacy code, but remove plugin-native call-site expectations.

### B-8 should include `scripts/`

Claude's B-8 row says `ruff check --fix src/ tests/` and `ruff format src/ tests/`. CI checks `scripts/` too:

- `.github/workflows/ci.yml:55-59` runs `python -m ruff check src/ tests/ scripts/` and `python -m ruff format --check src/ tests/ scripts/`.

So the fix command must include `scripts/` or CI can still fail after local cleanup.

### Cursor release-note tests need a pending branch

`tests/unit/test_fr029_cursor_fail_path.py:28-77` only has pass/fail fixtures. `tests/unit/test_release_notes_consistency.py:50-78` does not assert pending release-note language beyond mentioning Cursor/A-005 and permits pending `agents`.

If we neutralize docs now, add a live-artifact pending assertion:

- outcome `pending` must allow the single fixture/manifest state for the spike, but release notes must contain `pending`.
- outcome `pending` must not contain "generation shipped", "full Cursor sub-agent generation shipped", or "assumes PASS".

## Medium-confidence positions

- **OOS-005 neutralization timing**: push from MEDIUM to HIGH. Neutralize now. The current pending outcome at `cursor-subagent-outcome.json:2-6` plus A-005 at `spec.md:248` does not allow "full generation shipped" language.
- **B-7 nightly cron sufficiency**: partially reject. Nightly/label/manual is fine; nightly alone is not enough for "before release branch is merged" at `spec.md:234`, and one-OS smoke is not enough for A-010 at `spec.md:253`.
- **Compile-check not required for v1.0**: partially reject. Full corpus compile-check is not required. A narrow compile scaffold for the edited C-Q code samples should be required before closing those findings.

## Concrete fix plan status

Approved with these required edits:

1. F-F: option A, but no placeholder cursor/copilot blocks unless meaningful; test top-level forbidden fields, not mandatory `host_overrides` for all future files.
2. B-2: expand from "writer swap" to full command-path compatibility for canonical `enabled_hosts`.
3. B-3: define required metadata derivation for init, and test actual init output against `schemas/project-yml.schema.json`.
4. B-4: raw JSON Schema validate first, then parse with the runtime metadata model used by later checks.
5. B-7: 3-OS matrix, `workflow_dispatch`, three smoke env vars, four binaries including `csharp-ls`, preflight that fails on missing binaries, and the four `tests/integration/test_smoke_*.py` files.
6. B-8: include `scripts/` in ruff check/format commands.
7. OOS-005: neutralize release notes now and update pending-state tests.
8. B-1: gate both profile and hook call sites, especially linked secondary stale-profile hook rendering.

## Sign-off

I am at **AGREED-WITH-NITS** on Claude's overall review conclusions, not on release readiness. Remaining release blockers are the already-identified P0/P1 implementation defects plus the plan corrections above. Once the plan incorporates these nits, I do not see a remaining architectural disagreement.
