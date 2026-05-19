# Final Consolidated Review — Feature 019 Plugin-Native Architecture

**Date**: 2026-05-18
**Branch**: `019-plugin-native-arch`
**Status**: **Cross-AI debate concluded — Codex AGREED-WITH-NITS on review direction**
**Release status**: **BLOCKED** until P0/P1 fixes land per the corrected plan below

## What this document is

This is the canonical post-debate doc. It supersedes the earlier
review files in this folder:

- `claude/review.md` — first Claude review (CLI-narrow); verdict was
  `AGREED-WITH-NOTES`, **retracted** after Codex's empirical probes
  found the central FR-005/FR-006/FR-034 violation I missed.
- `claude/tool-surface-review.md` — broader scan; still valid for
  F1-F6 docs/asset findings.
- `claude/content-quality-and-oos-review.md` — content quality scan
  (F-A through F-L) + OOS analysis; severities adjusted per Codex
  round 3.
- `claude/consolidated-review.md` — first synthesis after Codex
  round 1; superseded by THIS document after Codex round 3.

Cross-AI debate trail:

- `codex/review.md` — Codex's initial BLOCKED review
- `round1-claude-to-codex.md` — Claude push-back briefing
- `round1-codex-reply.md` — Codex confirmed BLOCKERS + 6 push-backs
- `round2-claude-reply.md` — Claude conceded + clarifying push-backs
- `round3-codex-verify.md` — Codex AGREED-WITH-NITS + 8 plan corrections

## Cross-AI verdict

Both reviewers converged on:

- **Release stays BLOCKED for v1.0.0** until 8 implementation
  defects (B-1 through B-8) land plus the plan corrections below.
- **No more spec/architecture disagreement.** The remaining work is
  execution, not debate.

## Mandatory fixes (in execution order)

### Tier 1 — P0 BLOCKERS (release-gating)

#### F-B8 — Ruff: 48 errors + 55 format issues (1h, lowest risk first)

```
python -m ruff check --fix src/ tests/ scripts/
python -m ruff format src/ tests/ scripts/
```

**Codex correction**: my round-2 row missed `scripts/`. CI runs
`ruff check src/ tests/ scripts/` at `.github/workflows/ci.yml:55-59`,
so the fix command must include it or CI will still fail.

After auto-fix, manually resolve the ~8 non-fixable items (f-string
placeholders, line length, unused imports).

Verify: `python -m ruff check src/ tests/ scripts/` exits 0;
`python -m ruff format --check src/ tests/ scripts/` exits 0.

#### F-B6 — `configure` interactive picker shows all 4 hosts (30m)

`src/dotnet_ai_kit/cli.py:2286-2297`:

```python
# BEFORE
tools_result = questionary.checkbox(
    "AI tools to configure:",
    choices=[
        questionary.Choice("Claude Code", value="claude", ...),
    ],
).ask()

# AFTER
tools_result = questionary.checkbox(
    "AI tools to configure:",
    choices=[
        questionary.Choice("Claude Code", value="claude",
                           checked="claude" in current_tools),
        questionary.Choice("Codex CLI", value="codex",
                           checked="codex" in current_tools),
        questionary.Choice("Cursor", value="cursor",
                           checked="cursor" in current_tools),
        questionary.Choice("GitHub Copilot", value="copilot",
                           checked="copilot" in current_tools),
    ],
).ask()
```

Remove the "v1.0: Claude only" comment.

Test: add a unit asserting all 4 hosts appear in the choice list.

#### F-B1 — Skip `copy_profile()` AND `copy_hook()` for plugin-native hosts (3-4h with linked-secondary trap)

Five call sites + the **linked-secondary stale-profile trap**
(Codex round 3):

| Site | File:Line | Fix |
|---|---|---|
| init | `cli.py:1102-1116` | `for tool_name in ai_tools: if tool_name in PLUGIN_NATIVE_HOSTS: continue` before `copy_profile` |
| init hook | `cli.py:1120-1124` | Already gated by `_init_profile_path is not None`, which becomes `None` after the fix above — but add explicit `claude in ai_tools` belt-and-braces |
| upgrade | `cli.py:1874-1884` | Same skip pattern |
| upgrade hook | `cli.py:1893-1895` | Same belt-and-braces |
| configure | `cli.py:2459-2471` | Same skip pattern |
| configure hook | `cli.py:2475-2479` | Same belt-and-braces |
| linked-secondary profile | `copier.py:1063-1094` | Same skip pattern |
| **linked-secondary hook (Codex round 3 trap)** | `copier.py:1131-1137` | **Even if profile copy is gated, a STALE `.claude/rules/architecture-profile.md` from a prior run can still trigger hook embedding.** Add explicit check: `if not (target / ".claude/rules/architecture-profile.md").exists(): skip`. Alternative: check `tool_name in PLUGIN_NATIVE_HOSTS` even when reading the stale profile. |

**Tests to rewrite** (existing tests assert the bug):

- `tests/test_cli.py:1186` `test_upgrade_force_calls_profile`
  → assert NO `.claude/rules/architecture-profile.md` for claude
- `tests/test_cli.py:1399` `test_init_force_profile`
  → assert NO `.claude/rules/architecture-profile.md`
- `tests/test_cli.py:1629` (architecture-profile.md in output)
  → assert NOT present
- `tests/test_copier_hooks.py` (8 refs to architecture-profile.md)
  → assert negation for plugin-native; keep coverage for legacy
  migration paths if needed
- **`tests/test_multi_repo_deploy.py:486-491`** (Codex r3): currently
  asserts the linked secondary profile file EXISTS → flip to NOT
  EXISTS for plugin-native
- **New regression**: linked secondary with a pre-existing stale
  `.claude/rules/architecture-profile.md` → deploy must not call
  `copy_hook()` and must not embed the stale file into settings

#### F-B2 — Full `enabled_hosts` migration (4-6h, NOT just writer swap)

Codex round 3 expanded the blast radius beyond my round-2 plan.
The fix is not just `save_user_config` instead of `save_config`. The
following call sites still consume `config.ai_tools`:

| Site | File:Line | Action |
|---|---|---|
| `init` config build | `cli.py:896-910` | Build `UserConfig(enabled_hosts=..., plugin_version=...)`; call `save_user_config()` |
| `configure` config build | `cli.py:2310-...` | Same |
| Load via `load_config` | `cli.py:1253, 1726, 2189, 2838` | Migrate to `load_user_config()` OR add a compat adapter that reads `ai_tools` legacy alias and returns `enabled_hosts` |
| Consume `config.ai_tools` | `cli.py:1279, 1750, 2209, 2369` | Use `config.enabled_hosts` |
| Legacy keys in `models.py` | `models.py:422-433` | Add `enabled_hosts` to the legacy migration key list |
| `DotnetAiConfig.ai_tools` field | `models.py:437-486` | Either remove from `DotnetAiConfig` and replace usage with `UserConfig`, OR keep `DotnetAiConfig` as the in-memory representation with bidirectional conversion to/from `UserConfig` |
| `extra="ignore"` on DotnetAiConfig | `models.py:443` | Confirm `UserConfig` mirrors this where appropriate |

**Decision required**: do we have ONE config model (`UserConfig`) and
delete `DotnetAiConfig`, OR keep both with a conversion layer? Per
data-model.md:80 ("Pydantic reader accepts the legacy `ai_tools`
field name and maps it to `enabled_hosts` on read; writer always
emits `enabled_hosts`"), the cleanest fix is:

1. `UserConfig` is the canonical model with `enabled_hosts:`.
2. `UserConfig.from_legacy_dict()` classmethod accepts dicts with
   `ai_tools:` and rewrites to `enabled_hosts:`.
3. Delete `DotnetAiConfig` OR alias it to `UserConfig`.
4. All 4 `load_config()` call sites → `load_user_config()`.
5. All 4 `config.ai_tools` consumers → `config.enabled_hosts`.

**Test**: new unit `tests/contract/test_config_yml_emit.py` that
runs `dotnet-ai init` and validates the emitted `config.yml` against
`schemas/config-yml.schema.json` via `jsonschema.validate`.

#### F-B3 — `project.yml` writer + required-field derivation strategy (3-4h)

Codex round 3 caught what I missed: just removing the `detected:`
wrapper isn't enough because the schema requires fields that
`DetectedProject` doesn't have.

**Schema requires** (`schemas/project-yml.schema.json:7-8`):

```
company, domain, side, project_type, architecture_branch,
detected_paths, dotnet_version
```

**Today's `DetectedProject`** (`models.py:554-606`) has:

```
mode, project_type, architecture, namespace_format, packages,
confidence, ... but NO company, NO domain, NO side, NO dotnet_version
```

**Required-field derivation strategy** at `dotnet-ai init`:

| Field | Source |
|---|---|
| `company` | Read from `config.yml::company.name` (already required at init OR prompt if empty) |
| `domain` | Default to project_type-derived placeholder OR prompt; resolved properly by `dotnet-ai configure` |
| `side` | Inferred from project_type: command/processor/gateway → `server`; controlpanel → `client`; default `server` |
| `project_type` | From `--type` flag OR detection |
| `architecture_branch` | Derived: microservice (`command/query-sql/query-cosmos/processor/gateway/controlpanel/hybrid`) or generic (others) per data-model.md:69 |
| `detected_paths` | Detection output OR empty `{}` if detection skipped — validate against `non-empty values` constraint at data-model.md:69; if no detection ran, project.yml MUST NOT be emitted (defer to `configure`) |
| `dotnet_version` | Detection output from `.csproj`/`global.json`; default `"8.0"` if unknown |

**Decision**: if any required field cannot be derived, `init`
should:
- **Option A**: refuse to write `project.yml`; print "Run
  `dotnet-ai configure` to set company/domain before validation."
- **Option B**: write `project.yml` with placeholder values
  (`company: "<unset>"`, etc.) and have `check` flag the placeholders
  as schema violations.

Option A is cleaner (no invalid file on disk). Option B preserves
the existing init flow but trades cleanliness for less workflow
disruption.

**Test**: new unit `tests/contract/test_project_yml_emit.py` that
runs `dotnet-ai init . --ai claude --type command --company Acme`
and validates the emitted `project.yml` against
`schemas/project-yml.schema.json`.

#### F-B4 — `check` raw-schema-validate + parse (2h)

Codex round 3 refinement: raw JSON Schema validate FIRST, then parse
into the runtime model. Reasoning: `ProjectMetadata.model_config =
"ignore"` (`models.py:119`) silently drops extra fields, but the
schema rejects them. Without raw validation, this drift is invisible.

In `cli.py::check::project_yml_schema` (line ~2961-3048):

```python
import jsonschema, yaml

try:
    raw = yaml.safe_load(project_yml.read_text(encoding="utf-8"))
    schema = json.loads(
        (_get_package_dir() / "schemas" / "project-yml.schema.json")
        .read_text(encoding="utf-8")
    )
    jsonschema.validate(raw, schema)
except jsonschema.ValidationError as e:
    report_class("project_yml_schema", "fail",
                 details=str(e),
                 exit_class=FRClass.INVALID_PROJECT_SCHEMA)
    return
except yaml.YAMLError as e:
    report_class("project_yml_schema", "fail", details=str(e),
                 exit_class=FRClass.INVALID_PROJECT_YAML)
    return

# Raw schema OK → now parse into model for downstream checks
try:
    project = load_project(project_yml)
    # Use `project` for detected-paths correctness, etc.
except (pydantic.ValidationError, ValueError) as e:
    report_class("project_yml_model", "fail", details=str(e))
```

This gives **two-stage validation**:
1. Raw schema (catches schema drift, extra fields)
2. Model parse (semantic validation, used by downstream checks)

**Test**: new unit that hand-crafts an invalid `project.yml` (missing
`company`) and asserts `check` exits non-zero with the
"INVALID_PROJECT_SCHEMA" exit class.

#### F-B5 — Copilot freshness re-renders + compares (3h)

Current implementation at `cli.py:3093-3117` only compares stored
hash to current on-disk hash. **Misses metadata-staleness case.**

New algorithm:

```python
for entry in manifest.entries_with(host_owner="copilot"):
    target_path = project_root / entry.target
    if not target_path.exists():
        report_stale(target_path, reason="missing")
        continue

    # Re-render from CURRENT plugin source + CURRENT project metadata
    current_metadata = load_project(project_yml)
    rendered_now_bytes = render_copilot_file(
        source_path=entry.source,  # e.g., copilot-instructions.md template
        project_metadata=current_metadata,
    )

    on_disk_bytes = target_path.read_bytes()
    if sha256(rendered_now_bytes) != sha256(on_disk_bytes):
        report_stale(target_path,
                     reason="metadata-or-source-drift")
```

The existing hash-only check stays as a faster first-pass (catches
on-disk mutation); the re-render is the authoritative second pass
that catches the case where the user edited `project.yml::company`
without re-rendering.

**Test**: probe that renames company in `project.yml`, runs `check`,
asserts `copilot_freshness: fail` with appropriate exit class.

#### F-B7 — CI smoke gate: 3-OS matrix + 4 binaries + preflight (3-4h)

Codex round 3 corrections to my round-2 plan:

- **Add `workflow_dispatch`** so maintainers can trigger pre-merge
- **3-OS matrix** (Linux + macOS + Windows) per A-010
- **3 env vars**: `CLAUDE_CODE_SMOKE=1`, `CODEX_SMOKE=1`, `CURSOR_SMOKE=1`
- **4 binaries** (I missed csharp-ls):
  `claude`, `codex`, `cursor`, **`csharp-ls`** (needed by
  `test_smoke_claude_lsp.py:29-31`)
- **Preflight that fails on missing binaries** — otherwise the
  fixtures skip silently and the job goes green
- **Run the 4 specific test files**:
  - `tests/integration/test_smoke_claude.py`
  - `tests/integration/test_smoke_claude_lsp.py`
  - `tests/integration/test_smoke_codex.py`
  - `tests/integration/test_smoke_cursor.py`

`.github/workflows/ci.yml` smoke job rewrite:

```yaml
smoke:
  name: Smoke (release gate)
  if: |
    github.event_name == 'schedule'
    || github.event_name == 'workflow_dispatch'
    || contains(github.event.pull_request.labels.*.name, 'smoke')
  strategy:
    matrix:
      os: [ubuntu-latest, macos-latest, windows-latest]
    fail-fast: false
  runs-on: ${{ matrix.os }}
  needs: static-unit
  env:
    CLAUDE_CODE_SMOKE: "1"
    CODEX_SMOKE: "1"
    CURSOR_SMOKE: "1"
  steps:
    - uses: actions/checkout@v6
    - uses: actions/setup-python@v6
      with:
        python-version: "3.12"
    - name: Install dependencies
      run: |
        pip install pytest
        pip install -e .
    - name: Provision host CLIs
      run: |
        # Install claude, codex, cursor, csharp-ls — OS-specific
        # ...
    - name: Preflight — fail if any binary is missing
      shell: bash
      run: |
        set -e
        for bin in claude codex cursor csharp-ls; do
          if ! command -v $bin > /dev/null; then
            echo "::error::Required binary missing: $bin"
            exit 1
          fi
        done
    - name: Run feature-019 smoke fixtures
      run: |
        python -m pytest \
          tests/integration/test_smoke_claude.py \
          tests/integration/test_smoke_claude_lsp.py \
          tests/integration/test_smoke_codex.py \
          tests/integration/test_smoke_cursor.py \
          -q
```

Pre-tag: maintainer triggers `workflow_dispatch` from main; confirms
all 3 OS lanes are green before tagging v1.0.0.

### Tier 2 — P1 (release-impacting)

#### F-F (P1) — Migrate 13 agents-source/ files to `host_overrides` (2-3h)

Codex round 3 nits on my plan:

- **Don't require placeholder** `host_overrides.cursor` /
  `host_overrides.copilot` blocks unless the values are real. Empty
  blocks create fake host semantics. Skip them.
- **Contract test** should assert "**no host-allow-list fields at
  source top level outside `host_overrides`**" not "every source has
  `host_overrides`". The former catches the actual bug without
  over-constraining future minimal agents.
- **Migration scope** = 13 markdown sources excluding
  `agents-source/dotnet-ai-architect.md` (which already follows
  the contract). Skip `.gitkeep`.

For each of the 13 source files, migrate:

```yaml
# BEFORE — agents-source/dotnet-architect.md
---
name: dotnet-architect
description: Leads overall .NET solution architecture and design patterns
role: advisory
expertise: [...]
complexity: high
max_iterations: 20
---

# AFTER
---
name: dotnet-architect
description: Leads overall .NET solution architecture and design patterns
host_overrides:
  claude:
    role: advisory
    expertise: [...]
    complexity: high
    max_iterations: 20
---
```

Regenerate `agents-claude/<name>.md` for each via
`generate_claude_agent()` and verify the output now carries the full
metadata.

**Contract test** (new `tests/contract/test_agent_source_shape.py`):

```python
FORBIDDEN_TOP_LEVEL = (
    "role", "expertise", "complexity", "max_iterations",  # claude
    "model", "readonly",                                   # cursor
    "target", "tools", "disable-model-invocation",
    "user-invocable", "mcp-servers",                       # copilot
)

for src in (REPO / "agents-source").glob("*.md"):
    fm = parse_frontmatter(src)
    for key in FORBIDDEN_TOP_LEVEL:
        assert key not in fm, (
            f"{src.relative_to(REPO)}: `{key}` at top level. "
            f"Host-allow-list fields must be nested under "
            f"`host_overrides.<host>:`. See agent-source.contract.md."
        )
```

#### F-J (P1) — Rewrite stale slash-command bodies (1h)

`commands/init.md`: 9 stale references at lines 34, 44, 60, 76, 77,
106, 107, 127, 128. Rewrite the "Plugin mode" paragraph and the
output samples to describe the plugin-native flow:

```markdown
### Step 5: Verify

Confirm the following files/directories exist:
- `.dotnet-ai-kit/config.yml`
- `.dotnet-ai-kit/version.txt`
- `.dotnet-ai-kit/manifest.json` (generated-file inventory, FR-032)
- `.dotnet-ai-kit/project.yml` (only if detection succeeded)
- `.claude/settings.json` (only if Claude selected; permissions only)

For plugin-supporting hosts (Claude/Codex/Cursor): commands, rules,
skills, and agents are served from the host's plugin install, NOT
copied per-solution. For GitHub Copilot: renders are written to
`.github/instructions/`, `.github/agents/`, and
`.github/copilot-instructions.md`.
```

Output format updates (lines 106-107, 127-128):

```
dotnet-ai-kit v1.0.0
Initializing for Claude Code...
  Created: .dotnet-ai-kit/config.yml
  Created: .dotnet-ai-kit/manifest.json
  Created: .claude/settings.json (permissions: standard)
  (No commands/rules/skills/agents copied — served by plugin)
```

`commands/configure.md:126`: replace

```
This updates `.claude/settings.json` ... and re-copies commands ...
```

with:

```
This updates `.claude/settings.json` with the selected permission
level and updates the recorded `command_style` in
`.dotnet-ai-kit/config.yml`. For plugin-native hosts, commands are
served from the plugin install path; the style preference is read
at runtime.
```

#### OOS-005 release notes neutralization NOW (30m)

Codex round 3 (PB-3): pushed my MEDIUM to HIGH confidence. Spec text
at `spec.md:248` and `cursor-fixture-decision.contract.md:27-31`
make this binding.

`docs/release-notes-v1.0.md:106-117` — rewrite from:

```markdown
Until that runs, this release assumes the PASS branch (full Cursor
sub-agent generation shipped).
```

to:

```markdown
Cursor sub-agent generation is pending the A-005 spike fixture
outcome. The single spike fixture at `agents/dotnet-ai-architect.md`
is shipped as the A-005 verification artifact only. Full per-
specialist generation lands only after the smoke fixture passes in
CI. See `cursor-fixture-decision.contract.md` for the pass/fail
branches.
```

**Update tests**:

- `tests/unit/test_release_notes_consistency.py:11-12`: replace the
  "release notes assume PASS branch but flag pending" assertion with
  "pending state requires neutral 'pending A-005 outcome' language".
- `tests/unit/test_release_notes_consistency.py:60-63`: remove
  "default-assume-pass" permissiveness. Pending outcome MUST NOT
  contain "shipped" or "assumes PASS".
- `tests/unit/test_fr029_cursor_fail_path.py:28-77`: extend with a
  PENDING fixture (`cursor_fixture_pending/`) in addition to the
  existing pass/fail fixtures. Assert pending state allows the spike
  manifest with the single fixture but requires neutral release-note
  language.

### Tier 3 — P2 (technical accuracy)

#### C-Q1 — gRPC drops cancellation (10m)

`skills/microservice/grpc/service-definition/SKILL.md:96-110`:

```csharp
// BEFORE
var output = await mediator.Send(command);

// AFTER
var output = await mediator.Send(command, context.CancellationToken);
```

Apply to both `CreateOrder` and `UpdateOrder` examples.

#### C-Q2 — Minimal API validator drops cancellation (5m)

`skills/api/minimal-api/SKILL.md:141`:

```csharp
// BEFORE
var result = await validator.ValidateAsync(request);

// AFTER
var result = await validator.ValidateAsync(
    request, context.HttpContext.RequestAborted);
```

#### C-Q3 — gRPC money types (20m)

`skills/microservice/grpc/service-definition/SKILL.md:51, 77-84,
165`: replace `double total`/`double unit_price` with one of:

- **Recommended for new services**: integer minor-units (e.g.,
  `int64 total_cents`)
- **Alternative**: `string decimal_total` with explicit serialization
- **Or**: documented `DecimalValue` message pattern

Update the anti-pattern table at line 165 to flip the recommendation:

```
| Using `double` for money | Floating-point loss | Use int64 minor-units OR string decimal |
```

#### C-Q4 — Controllers Problem(result.Error) (15m, REFINED from compile-error to semantic)

Codex round 3 verified `Result<T>::Error` is `string?` in the
template Result<T> (`templates/generic-*/src/.../Result.cs:7`). So
`Problem(result.Error)` **compiles** but produces an incomplete
ProblemDetails.

`skills/api/controllers/SKILL.md:47-49` (and `:74` if similar):

```csharp
// BEFORE
: Problem(result.Error);

// AFTER
: Problem(detail: result.Error,
          statusCode: StatusCodes.Status400BadRequest);
```

Or introduce a `ToProblem()` extension. The CQRS skill's
`Result<T>` (where `Error` is an `Error` object — see
`skills/cqrs/request-response/SKILL.md:172`) needs a separate mapper.

#### C-Q5 — Modern C# primary constructor mental model (5m)

`skills/core/modern-csharp/SKILL.md:213`:

```
| Primary constructors storing to `private readonly` | Redundant -- captured params are already fields |
```

→

```
| Primary constructors stored to `private readonly` fields | Compiler generates backing storage only when an instance member captures the parameter; explicit `private readonly` adds a second storage slot |
```

#### F-G — Newtonsoft.Json rationale (20m)

Add a "Why Newtonsoft.Json" section to
`skills/microservice/command/event-store/SKILL.md` (upstream skill).
Cross-reference from `outbox`, `event-routing`, and
`knowledge/outbox-pattern.md`.

Suggested text:

```markdown
## Why Newtonsoft.Json (not System.Text.Json)

Events in this template use Newtonsoft.Json for the `Data` column
because polymorphic deserialization with type discriminators is
required for event-sourced replay. System.Text.Json supports this
since .NET 7 via `JsonPolymorphicAttribute`, but Newtonsoft.Json
remains the default in this template stack because:

1. The legacy event catalogue uses `TypeNameHandling.Auto` for
   schema-evolving events (`knowledge/event-versioning.md`).
2. Custom converters for value objects integrate with the existing
   `GenericEventConfiguration<TEntity, TData>` infrastructure.

If migrating new services to System.Text.Json, replace the converter
chain in `EventConfiguration.cs` and run the full event-replay
regression suite.
```

#### Compile-check scaffold for C-Q1/2/3/4 (Codex round 3 — 3h)

Add `tests/content/test_csharp_skill_snippets_compile.py`:

- Writes a temporary `net8.0` SDK project (`Microsoft.NET.Sdk.Web`).
- Adds `FrameworkReference Include="Microsoft.AspNetCore.App"`.
- Stubs MediatR, FluentValidation, Grpc.Core types locally (avoid
  NuGet/network).
- Includes the FIXED versions of:
  - Controller sample (post-C-Q4)
  - Minimal API filter (post-C-Q2)
  - gRPC service method (post-C-Q1)
- Skip if `dotnet` is missing; otherwise `dotnet build --nologo`
  must pass.

**Not a v1.0 release blocker** but should be the gate for closing
the C-Q content findings. Visual review alone is too loose now that
we know `Problem(result.Error)` was ambiguous.

### Tier 4 — Polish (P3)

| ID | Action | File(s) | Time |
|---|---|---|---|
| F-A | Add `when_to_use:` to 9 `skills/core/*` | 9 files | 30m |
| F-B | Document `metadata.agent` optional convention in `data-model.md` | data-model.md | 10m |
| F-C | Remove `paths:` from `rules/conventions/async-concurrency.md` (universal rules don't need it) | 1 file | 2m |
| F-D | Add `## Related Skills` to 5 rules (existing-projects, tool-calls, localization, multi-repo, naming) | 5 files | 30m |
| F-E | Fill or remove 3 empty section headers (`plan-templates.md:70,73`, `review.md:144`) | 2 files | 10m |
| F-H | Link `knowledge/grpc-patterns.md` from gRPC skills | 4 files | 10m |
| F-I | Promote lowercase `must` → `MUST` at `rules/domain/configuration.md:18,21` | 1 file | 5m |
| F-L | Confirm `plan-artifacts/SKILL.md` is intentionally lean (per Codex r1 it's a pointer skill) | doc note | 5m |

### Tier 5 — Tool surface (from earlier tool-surface-review)

| ID | Action | Time |
|---|---|---|
| F1 | Add `## [1.0.0] — 2026-05-18 — Plugin-Native Architecture` to `CHANGELOG.md` (AFTER all P0/P1 fixes land) | 30m |
| F4 | Update `AGENTS.md` Project Structure counts (15→16 rules, 5→7 hooks, 13→12 templates) | 10m |
| F5 | Update `CONTRIBUTING.md` Project Structure counts + `.mcp.json` description (not csharp-ls) | 10m |
| F6 | Drop the `rules` declaration from `.cursor-plugin/plugin.json` (it's `./rules/cursor/` and the folder is empty) OR populate the folder if OOS-005 ships | 15m |

### OOS items per user request

| OOS | Verdict | Action | Time |
|---|---|---|---|
| **OOS-005** | **CONDITIONAL INCLUDE** if Cursor smoke passes | Run `pytest tests/integration/test_smoke_cursor.py` with `CURSOR_SMOKE=1`. On PASS: generate 12 Cursor agents via `generate_cursor_agent()`, update `cursor-subagent-outcome.json` to `"passed"`. On FAIL: follow well-documented fail-path. | 2-3h |
| **OOS-003** | **NARROW INCLUDE** (source-tree wrappers) | Add `bin/dotnet-ai` (POSIX) + `bin/dotnet-ai.cmd` (Windows) thin wrappers that `python -m dotnet_ai_kit.cli "$@"`. NOT a standalone executable. Document `[project.scripts]` is the install-time path. | 1h |
| **OOS-004** | **CANNOT SHIP** (forward-compat scaffolding only) | Per `developers.openai.com/codex/plugins/build` retrieved 2026-05-18: plugin manifest accepts skills/mcpServers/apps/hooks only, NO `agents` field. Codex documents subagents generally at `~/.codex/agents/` but not as a plugin primitive. Shipping `agents` in `.codex-plugin/plugin.json` would violate FR-002/FR-035. Reserve `host_overrides.codex:` blocks in agents-source AFTER F-F migration. File v1.1 tracking issue. | 30m |

## Total effort

| Tier | Effort |
|---|---|
| Tier 1 P0 BLOCKERS (B-1 → B-8) | 17-22h |
| Tier 1 test rewrites (existing tests assert the bug) | 4-6h |
| Tier 2 P1 (F-F migration, F-J commands, OOS-005 neutralization) | 3.5-4.5h |
| Tier 3 P2 technical (C-Q1-Q5, F-G, compile-check scaffold) | 4-5h |
| Tier 4 P3 polish (F-A through F-L) | 1.5h |
| Tier 5 tool surface (CHANGELOG, AGENTS.md, CONTRIBUTING.md, rules/cursor) | 1h |
| OOS items (-005 conditional, -003 wrappers, -004 scaffolding) | 3.5-4.5h |
| **TOTAL** | **~35-44 hours** |

Roughly **a focused week of maintainer work**. The Python
implementation gap is the bulk; everything else is polish.

## Execution sequence (lowest blast radius first)

1. **F-B8** (ruff cleanup including `scripts/`) — unblocks CI
2. **F-B6** (configure picker) — smallest semantic change
3. **F-B1** (skip copy_profile + copy_hook + linked-secondary trap) — core behavioral fix
4. **F-B2 + F-B3** (config + project schema migration with full call-path) — parallel, biggest blast radius
5. **F-B4** (raw-plus-model check validation) — depends on F-B3
6. **F-B5** (Copilot freshness re-render) — independent
7. **F-B7** (CI smoke gate 3-OS + 4 binaries + preflight) — validates the others
8. **F-F** migration (13 agents-source files)
9. **F-J** commands rewrite
10. **OOS-005** neutralize release notes
11. Tier 3 (C-Q fixes + compile-check scaffold)
12. **OOS-005 conditional inclusion** (run Cursor smoke; on PASS, generate 12 agents)
13. **OOS-003** bin/ wrappers
14. **OOS-004** forward-compat scaffolding
15. Tier 4 polish (F-A through F-L)
16. Tier 5 tool surface (CHANGELOG, etc.)
17. Tag v1.0.0 after CI green via `workflow_dispatch`

## What still goes to v1.1

| Item | Reason |
|---|---|
| OOS-006 multi-repo monitor | Very large scope (3-5 weeks); user excluded from this batch |
| OOS-004 native Codex plugin agents | Codex docs at developers.openai.com/codex/plugins don't expose an `agents` primitive; FR-035 admission gate blocks shipping |
| OOS-005 if Cursor smoke fails | Per cursor-fixture-decision.contract.md fail-path |
| OOS-003 standalone executable (shiv/PyInstaller) | Out of scope; v1.0 ships source-tree wrappers only |
| Full corpus C# compile-check across 124 skills | Tier 3 scaffold covers C-Q fixes only |

## Cross-AI debate audit trail

| Round | File | Outcome |
|---|---|---|
| 1 | `codex/review.md` | Codex: BLOCKED with 7 findings |
| 1 | `claude/review.md` | Claude: AGREED-WITH-NOTES (RETRACTED) |
| 1 | `claude/tool-surface-review.md` | Claude: BLOCK-WITH-MINOR-FIXES (6 doc findings) |
| 1 | `claude/content-quality-and-oos-review.md` | Claude: 12 content findings + OOS analysis |
| 2 | `round1-claude-to-codex.md` | Claude: 6 push-backs + content-quality demand |
| 2 | `round1-codex-reply.md` | Codex: rejected 1 push-back, accepted 3, 5 new C# findings |
| 3 | `round2-claude-reply.md` | Claude: 4 concessions + 3 clarifying push-backs |
| 3 | `round3-codex-verify.md` | Codex: AGREED-WITH-NITS + 8 plan corrections |
| Final | `final-consolidated-review.md` (this file) | Both: BLOCKED until P0/P1 fixes + 8 corrections incorporated |

## Sources

- [Codex CLI Plugins reference (OpenAI)](https://developers.openai.com/codex/plugins) — retrieved 2026-05-18
- [Codex CLI Plugins build guide](https://developers.openai.com/codex/plugins/build) — retrieved 2026-05-18
- [Codex CLI Subagents](https://developers.openai.com/codex/subagents) — retrieved 2026-05-18
- [Cursor Plugins Reference](https://cursor.com/docs/plugins/building) — retrieved 2026-05-18
- [Cursor 2.4 Subagents announcement](https://memu.pro/blog/cursor-2-4-subagents-skills-memory) — retrieved 2026-05-18
- [Cursor 2.5 changelog](https://cursor.com/changelog/2-5) — retrieved 2026-05-18
- [PyPA Entry points specification](https://packaging.python.org/specifications/entry-points/) — retrieved 2026-05-18
- [shiv project (zipapp bundling)](https://github.com/linkedin/shiv) — retrieved 2026-05-18

## Reproducibility

Every claim in this document is reproducible via the scanners and
probes already in the repo:

```bash
# Content quality
python scripts/quality_scan.py
python scripts/quality_scan2.py
python scripts/quality_scan3.py
python scripts/quality_scan4.py

# Lint
python -m ruff check src/ tests/ scripts/
python -m ruff format --check src/ tests/ scripts/

# Doc lint
python scripts/doc_lint.py

# CLI probe
dotnet-ai init <tmp> --ai claude --type generic --json
ls <tmp>/.claude/rules/                          # should be empty after F-B1
cat <tmp>/.dotnet-ai-kit/config.yml | grep enabled_hosts    # required after F-B2
cat <tmp>/.dotnet-ai-kit/project.yml | grep ^company        # required after F-B3

# Schema validation
python -c "
import yaml, json, jsonschema
proj = yaml.safe_load(open('<tmp>/.dotnet-ai-kit/project.yml').read())
schema = json.load(open('schemas/project-yml.schema.json'))
jsonschema.validate(proj, schema)
print('OK')
"
```

## End of debate

Both reviewers agree on:
- The 7 implementation BLOCKERS
- The 12 content findings (with reclassified severities)
- The 8 plan corrections
- The 3 OOS verdicts (-005 conditional, -003 narrow, -004 cannot)
- The execution sequence

The next move is **implementation**, not more cross-AI review.
Maintainer should execute the 17-step sequence above, then trigger
the CI smoke gate via `workflow_dispatch` before tagging v1.0.0.
