# Consolidated Review — Feature 019 Plugin-Native Architecture

**Date**: 2026-05-18
**Branch**: `019-plugin-native-arch`
**Reviewer**: Claude (Opus 4.7, 1M context)
**Scope**: Aggregate every finding across the four prior review docs
(Claude `review.md`, `tool-surface-review.md`,
`content-quality-and-oos-review.md`; Codex `codex/review.md`) + web
research on OOS-003 / OOS-004 / OOS-005 implementation strategies +
empirical verification of Codex's BLOCKED findings.
**Verdict**: **BLOCKED for v1.0.0 tag** — 7 release-gating defects must
be fixed; OOS-005 should ship; OOS-003 needs clarified scope; OOS-004
cannot ship without Codex docs catching up.

## Correction to my earlier reviews

My `review.md` reached `AGREED-WITH-NOTES` based on a green pytest
run and a static grep for `PLUGIN_NATIVE_HOSTS` gates. **That verdict
was wrong.** Codex's `codex/review.md` ran direct CLI probes and
found that `init`/`upgrade`/`configure` still write per-solution
rule artifacts and a frozen architecture prompt — exactly the
FR-005/FR-006/FR-034 violation the feature exists to fix. I missed
this because:

1. I gated `copy_commands`/`copy_rules`/`copy_skills`/`copy_agents`
   but never grepped for the parallel `copy_profile()` /
   `copy_hook()` calls.
2. I trusted the pytest suite, which inherits pre-019 tests that
   **assert** the bug ("upgrade --force should call copy_profile",
   `tests/test_cli.py:1186`).
3. I did not run `dotnet-ai init` and inspect the actual file tree.

I reproduced Codex's probes empirically (below). Their findings hold.
This consolidated review supersedes my earlier verdicts.

## Empirical reproduction of Codex's BLOCKERS

All 7 findings verified by running probes against the working tree at
HEAD of `019-plugin-native-arch`:

### B-1: `init` writes per-solution rule + frozen profile prompt [P0 — BLOCKER]

**Probe**:

```
$ dotnet-ai init <tmp> --ai claude --type generic --json
```

**Files written**:

```
.claude/rules/architecture-profile.md       ← 3879 bytes, frozen at init
.claude/settings.json                       ← contains "hooks" with prompt embedding
.dotnet-ai-kit/.gitignore
.dotnet-ai-kit/config.yml
.dotnet-ai-kit/manifest.json
.dotnet-ai-kit/project.yml
.dotnet-ai-kit/version.txt
```

`.claude/settings.json` contains a `PreToolUse` hook with `"type":
"prompt"` and a `prompt:` field that embeds the full architecture
profile body verbatim:

```json
"hooks": {
  "PreToolUse": [{
    "_source": "dotnet-ai-kit-arch",
    "matcher": "Edit|Write",
    "hooks": [{
      "type": "prompt",
      "prompt": "You are an architecture enforcement validator. Check if the code being written violat[...]"
    }]
  }]
}
```

**Root cause**:

| Site | What it does |
|---|---|
| `src/dotnet_ai_kit/cli.py:1102` | `for tool_name in ai_tools:` — no `PLUGIN_NATIVE_HOSTS` skip |
| `src/dotnet_ai_kit/cli.py:1104` | `profile_path = copy_profile(target, tool_name, ...)` — runs for "claude" |
| `src/dotnet_ai_kit/cli.py:1122` | `copy_hook(target, _init_profile_path, ...)` — embeds profile in settings |
| `src/dotnet_ai_kit/cli.py:1874-1882` | Same pattern in `upgrade` |
| `src/dotnet_ai_kit/cli.py:2459-2467` | Same pattern in `configure` |
| `src/dotnet_ai_kit/copier.py:1087, 1109` | Same pattern in linked-secondary writer |

**Why this violates the spec**:
- **FR-005** (spec.md:153): plugin-host init writes ONLY project
  metadata, user config, and host settings merge file.
- **FR-006** (spec.md:154): MUST NOT copy commands, rules, skills, or
  agents.
- **FR-034** (spec.md:206): architecture-profile selection MUST be
  resolved from current project metadata at hook/tool-use time, not
  **frozen into init-time renders**.

**Test coverage gap that hid this**:

Existing tests **assert the bug**:

```
tests/test_cli.py:1186  - "upgrade --force should call copy_profile and copy_hook"
tests/test_cli.py:1399  - "init --type command should deploy architecture-profile.md"
tests/test_cli.py:1629  - assert "architecture-profile.md" in result.output
tests/test_copier_hooks.py — 8 refs to ".claude/rules/architecture-profile.md" path
```

These were written pre-019 and never updated. The 729-tests-pass
metric is misleading.

### B-2: `init` writes legacy `config.yml` (no `enabled_hosts:`) [P0 — BLOCKER]

**Probe**:

```python
$ python -c "
import yaml, json, jsonschema
cfg = yaml.safe_load(open('.dotnet-ai-kit/config.yml').read())
print('keys:', list(cfg.keys()))
schema = json.load(open('schemas/config-yml.schema.json'))
jsonschema.validate(cfg, schema)
"
keys: ['version', 'company', 'naming', 'repos', 'permissions_level',
       'managed_permissions', 'ai_tools', 'command_style', 'linked_from']
ValidationError: 'enabled_hosts' is a required property
```

The emitted YAML has `ai_tools:` (legacy `DotnetAiConfig` shape). The
published schema at `schemas/config-yml.schema.json:7-9` requires
`enabled_hosts` and `plugin_version` and forbids `ai_tools`. A
parallel `UserConfig` pydantic model + `save_user_config()` exists,
but `init`/`configure` still call `DotnetAiConfig(ai_tools=...)` at
`cli.py:905, 907, 910`.

**Violates**: T003/T004/T005 (data-model contract), FR-016, FR-017
(check validates against published schemas).

### B-3: `init` writes legacy `project.yml` (no top-level `company`) [P0 — BLOCKER]

**Probe**:

```python
$ python -c "
import yaml, json, jsonschema
proj = yaml.safe_load(open('.dotnet-ai-kit/project.yml').read())
print('keys:', list(proj.keys()))
schema = json.load(open('schemas/project-yml.schema.json'))
jsonschema.validate(proj, schema)
"
keys: ['detected']
ValidationError: 'company' is a required property
```

The emitted YAML nests the project data under `detected:`. The schema
requires top-level `company`, `domain`, `side`, `project_type`,
`architecture_branch`, `detected_paths`, `dotnet_version`.

**Root cause**: `src/dotnet_ai_kit/config.py:127, 132, 144` —
`save_project()` writes the legacy `DetectedProject` shape.

**Violates**: FR-009, FR-010, FR-017, FR-034, project schema contract.

### B-4: `check` validates legacy shape, reports schema-invalid as `pass` [P0 — BLOCKER]

**Probe** (same tmp dir as B-3):

```
$ dotnet-ai check . --host copilot --json
{
  "exit_code": 0,
  "checks": [
    { "name": "project_yml_schema", "status": "pass", ... }
  ]
}
```

Even though `jsonschema.validate(proj, project_yml_schema)` raises
`ValidationError: 'company' is a required property`, `dotnet-ai check`
reports `project_yml_schema: pass`. The validation routine in
`cli.py:2962, 3045-3046` calls `load_project()` (which reads the
legacy shape) instead of validating raw YAML against the published
schema.

**Violates**: FR-017 (the validation command's published contract),
FR-031 (unique exit class per failure — there's no failure to report).

### B-5: Copilot freshness misses metadata staleness [P1 — BLOCKER]

**Probe**:

```
1. dotnet-ai init <tmp> --ai copilot --type generic
2. Edit .dotnet-ai-kit/config.yml: company.name "" → "Globex"
3. Do NOT run upgrade --copilot
4. dotnet-ai check . --host copilot --json
   → "copilot_freshness": "pass"
```

But `.github/copilot-instructions.md` still contains the pre-rename
metadata. The check at `cli.py:3093, 3110, 3116-3117` only compares
on-disk hash to the manifest hash — it doesn't re-render from current
metadata and compare.

**Violates**: US2 acceptance scenario 3, FR-017, SC-006, CHK016.

### B-6: `configure` interactive shows only Claude [P1 — BLOCKER]

**Verified at `cli.py:2286-2297`**:

```python
# AI tools multi-select (T041) — v1.0: Claude only
current_tools = config.ai_tools or []
tools_result = questionary.checkbox(
    "AI tools to configure:",
    choices=[
        questionary.Choice("Claude Code", value="claude", ...),
    ],
).ask()
```

Only "Claude Code" appears in the checkbox. Codex CLI, Cursor, and
GitHub Copilot are missing.

**Violates**: FR-016, CHK037.

(My `tool-surface-review.md` claimed the host-selection invariants
were centralized. They are — for the bulk-copy *route*. But the
interactive picker that drives `ai_tools` is hard-coded to Claude
upstream of that. I missed it.)

### B-7: CI smoke job runs `tests/smoke/`, NOT feature-019 fixtures [P1 — BLOCKER]

**Verified at `.github/workflows/ci.yml:64-88`**: the smoke job runs
`python -m pytest tests/smoke -q` with `CLAUDE_CODE_SMOKE=1`. This
runs the legacy 018-era smoke tests, **not**:

- `tests/integration/test_smoke_claude.py`
- `tests/integration/test_smoke_codex.py`
- `tests/integration/test_smoke_cursor.py`
- `tests/integration/test_smoke_claude_lsp.py`

Those 4 are the feature-019 fixtures (CHK001-CHK004, CHK011), each
gated by its own env var (`CLAUDE_CODE_SMOKE`, `CODEX_SMOKE`,
`CURSOR_SMOKE`). None of those vars are set by the smoke job. The
Cursor spike outcome at
`specs/019-plugin-native-arch/discussion/tasks-phase/cursor-subagent-outcome.json`
is still `"pending"`, yet `docs/release-notes-v1.0.md:106-117` assumes
the PASS branch.

**Violates**: FR-029, SC-008, CHK001-CHK004, CHK011/CHK012.

### B-8: 48 ruff errors + 55 format issues [P2 — BLOCKER]

**Verified**:

```
$ python -m ruff check src/ tests/
Found 48 errors.
[*] 40 fixable with the `--fix` option

$ python -m ruff format --check src/ tests/
55 files would be reformatted
```

CI's `static-unit` job at `.github/workflows/ci.yml:56-59` runs both
ruff checks. **The branch fails CI today** before any other gate.

Representative failures:
- `src/dotnet_ai_kit/agent_generators.py:24` import ordering
- `src/dotnet_ai_kit/cli.py:990, 991` f-strings without placeholders
- `src/dotnet_ai_kit/manifest.py:298` line too long
- `src/dotnet_ai_kit/render.py:15` unused import
- `tests/test_cli.py:19` unused import (`pytest`)

### B-9: `verification.md` checklist all unchecked [P2]

`specs/019-plugin-native-arch/checklists/verification.md` still has all
CHK001-CHK063 boxes unchecked. The tasks file's final checkpoint claims
all CHK items are checked off. This is a release-gate process drift.

## Required fixes for v1.0.0

### F-B1 (BLOCKER) — Skip `copy_profile` + `copy_hook` for plugin-native hosts

Three call sites in `cli.py` and two in `copier.py`. Each needs the
same gate that the bulk-copy path already has:

```python
# cli.py:1102 — BEFORE
for tool_name in ai_tools:
    try:
        profile_path = copy_profile(target, tool_name, ...)

# cli.py:1102 — AFTER
for tool_name in ai_tools:
    if tool_name in PLUGIN_NATIVE_HOSTS:
        # FR-034: profile resolved at hook/tool-use time, not init
        continue
    try:
        profile_path = copy_profile(target, tool_name, ...)
```

Apply same change at:
- `cli.py:1102` (init)
- `cli.py:1874` (upgrade)
- `cli.py:2459` (configure)
- `copier.py:1087, 1109` (linked-secondary)

The `copy_hook` calls at `cli.py:1120-1126, 1893-1900, 2476-2482`
should also be guarded — they only fire if `_*_profile_path` was set,
which won't happen for Claude after the fix. But to be defensive,
explicitly skip on `claude in ai_tools and claude in PLUGIN_NATIVE_HOSTS`.

**Pair with**: rewrite `tests/test_cli.py::test_init_force_profile`
and similar to **assert the negation** (no `.claude/rules/`
directory exists post-init for Claude).

**Effort**: ~3 hours including test rewrite.

### F-B2 (BLOCKER) — Migrate `init`/`configure` to write `UserConfig`

`init` and `configure` must call `save_user_config()` (existing
function) and write a `UserConfig` instance with `enabled_hosts` /
`plugin_version` / `retention` / `permission_profile`. The legacy
`DotnetAiConfig` writer at `cli.py:905-910, 2310-...` must be
replaced.

A bridging task — many tests will reference the old shape and need
updates. Estimate 4-6 hours.

### F-B3 (BLOCKER) — Migrate `init`/`configure` to write `ProjectMetadata`

`save_project()` at `config.py:127-144` must emit the
top-level-keys shape required by `schemas/project-yml.schema.json`.
Existing `load_project()` should be updated to read both shapes for
backward read-compat during the migration window.

**Effort**: ~3-4 hours.

### F-B4 (BLOCKER) — `check` validates against published schemas

In `cli.py::check`, replace `load_project()` schema check with raw
YAML + `jsonschema.validate(yaml.safe_load(path), schema)`. Map
`jsonschema.ValidationError` to FR-031's "invalid project metadata
schema" exit class.

**Effort**: ~2 hours.

### F-B5 (BLOCKER) — Copilot freshness compares re-rendered output

In `cli.py::check::copilot_freshness`, the algorithm must be:

```python
for managed_copilot_path in manifest.entries_with(host_owner="copilot"):
    # Re-render from CURRENT plugin source + CURRENT project metadata
    rendered_now = render_copilot_file(managed_copilot_path, current_metadata)
    on_disk = managed_copilot_path.read_bytes()
    if sha256(rendered_now) != sha256(on_disk):
        report_stale(managed_copilot_path)
```

This catches metadata changes (B-5's probe case) AND plugin-source
changes. Existing hash-only check stays as a cheaper first-pass; the
re-render is the authoritative second pass.

**Effort**: ~3 hours.

### F-B6 (BLOCKER) — `configure` interactive picker lists all 4 hosts

`cli.py:2286-2297` — expand `questionary.checkbox(choices=...)` to:

```python
choices=[
    questionary.Choice("Claude Code", value="claude",
                       checked="claude" in current_tools),
    questionary.Choice("Codex CLI", value="codex",
                       checked="codex" in current_tools),
    questionary.Choice("Cursor", value="cursor",
                       checked="cursor" in current_tools),
    questionary.Choice("GitHub Copilot", value="copilot",
                       checked="copilot" in current_tools),
]
```

Remove the "v1.0: Claude only" comment. Add a test that asserts all 4
hosts appear.

**Effort**: ~30 minutes.

### F-B7 (BLOCKER) — Wire feature-019 smoke tests into CI

`.github/workflows/ci.yml:64-88` `smoke:` job must run
`tests/integration/test_smoke_*.py` with the appropriate env vars:

```yaml
env:
  CLAUDE_CODE_SMOKE: "1"
  CODEX_SMOKE: "1"        # NEW
  CURSOR_SMOKE: "1"       # NEW

steps:
  - run: |
      python -m pytest \
        tests/integration/test_smoke_claude.py \
        tests/integration/test_smoke_claude_lsp.py \
        tests/integration/test_smoke_codex.py \
        tests/integration/test_smoke_cursor.py \
        tests/smoke -q
```

Plus install the host CLIs in the runner (the runner image needs
`claude`, `codex`, `cursor` on PATH). If a host's CLI install is
infeasible in CI, that host's gate must be either nightly-cron-only
or explicit OOS — not silently skipped.

**Effort**: ~2-3 hours including CI debugging.

### F-B8 (BLOCKER) — Fix all ruff errors

```
python -m ruff check --fix src/ tests/
python -m ruff format src/ tests/
```

40 of 48 are auto-fixable; 8 need manual review (f-strings, line
length). Then re-verify locally with `--check`.

**Effort**: ~1 hour.

### F-B9 — Check off `verification.md` only for actually-passing gates

Stop assuming PASS. Check off each CHK001-CHK063 only after the
referenced test/gate has actually passed in CI.

## OOS implementation plans (user requested all 3 in v1.0.0)

### OOS-005 — Full Cursor sub-agent generation [RECOMMEND INCLUDE]

**Cursor docs status (web research, May 2026)**:
- **[Cursor 2.4](https://memu.pro/blog/cursor-2-4-subagents-skills-memory)**
  shipped subagents as a first-class feature.
- **[Cursor 2.5](https://cursor.com/changelog/2-5)** added async
  subagents + plugin sandbox controls.
- **[Cursor Plugins Reference](https://cursor.com/docs/plugins/building)**
  documents the layout: agents at `.cursor/agents/` (project) or
  `~/.cursor/agents/` (user); plugin manifest at
  `.cursor-plugin/plugin.json` with `"agents": "<dir>"` reference.
- **Frontmatter fields**: `name` (kebab-case), `description`, `model`,
  `readonly`, `is_background`.

**This matches our current implementation**. The previous loader
ambiguity (research.md:43, plan-phase round 2-3) is **resolved by
Cursor's 2.4/2.5 docs**. OOS-005 is no longer blocked by a docs gap.

**What we have today**:
- `src/dotnet_ai_kit/agent_generators.py:203-216` —
  `generate_cursor_agent()` works (not a stub).
- `.cursor-plugin/plugin.json` declares `"agents": "./agents/"`.
- `agents/dotnet-ai-architect.md` — the spike fixture.
- Spike outcome JSON `cursor-subagent-outcome.json` — `"pending"`.

**Implementation steps**:

1. **Run the smoke fixture** with Cursor CLI installed:
   ```
   export CURSOR_SMOKE=1
   pytest tests/integration/test_smoke_cursor.py -v
   ```
   This is the gate per `cursor-fixture-decision.contract.md`.

2. **If PASS**: Generate the 12 remaining specialists:
   ```python
   from pathlib import Path
   from dotnet_ai_kit.agent_generators import generate_cursor_agent
   for src in Path('agents-source').glob('*.md'):
       if src.stem == 'dotnet-ai-architect':
           continue  # already the fixture
       out = Path('agents') / src.name
       out.write_text(generate_cursor_agent(src), encoding='utf-8')
   ```

3. **Update spike outcome** to `passed` with timestamp + CI run URL.

4. **Confirm the meta-test** `tests/unit/test_fr029_cursor_fail_path.py`
   still passes (default-assume-pass is the PASS branch).

5. **Update traceability.md** to mark OOS-005 RESOLVED.

**If the smoke FAILS in CI**: follow the well-documented fail-path
at `contracts/cursor-fixture-decision.contract.md:34-50` — remove the
`agents` field from the Cursor manifest, raise NotImplementedError
in `generate_cursor_agent()`, defer to v1.1.

**Effort**: 2-3 hours (mostly Cursor CLI environment setup).

### OOS-003 — `bin/` launcher [RECOMMEND CLARIFY-SCOPE FIRST]

**Web research findings (May 2026)**:

The PyPA standard for distributing a Python CLI as an executable is
**`[project.scripts]`** in `pyproject.toml` — which we already have:

```toml
[project.scripts]
dotnet-ai = "dotnet_ai_kit.cli:app"
```

When a user runs `pip install dotnet-ai-kit` or
`uv tool install dotnet-ai-kit`, the installer creates a launcher
script in the user's `Scripts/` (Windows) or `bin/` (Unix) directory
that wires up the entry point. This is
**[the entry points specification](https://packaging.python.org/specifications/entry-points/)**
in the PyPA standard, defined by PEP 517 build backends.

So `dotnet-ai` is ALREADY a `bin/` launcher in the user-install
sense. **What does adding `bin/` to the source repo gain?**

Three meaningful interpretations:

1. **"Plugin-less standalone use"** — a single-file executable that
   doesn't require `pip install` first.
   - Tool: **[shiv](https://github.com/linkedin/shiv)** (zipapp +
     auto-unpacked deps) or
     **[PyInstaller](https://pyinstaller.org)** (full binary +
     interpreter).
   - Per `realpython.com/python-zipapp`: shiv builds a `.pyz` zip
     archive with deps bundled; PEX is similar. PyInstaller bundles
     the interpreter for fully-standalone use.
   - Caveat: PyInstaller cannot cross-compile; would need 3-OS CI
     builds.

2. **"Repo-tree wrapper for source checkouts"** — a thin
   `bin/dotnet-ai` shell script + `bin/dotnet-ai.cmd` that runs
   `python -m dotnet_ai_kit.cli "$@"` against the source tree. Useful
   for contributors who haven't `pip install -e .` yet.

3. **"CI/CD ergonomics"** — a self-contained invocation pattern for
   GitHub Actions / Azure Pipelines (e.g. `bin/dotnet-ai check`
   instead of `pip install` first).

**Recommendation**: **Ship interpretation #2** (the cheapest, smallest
risk) as the v1.0 deliverable for OOS-003:

```
bin/
├── dotnet-ai           # POSIX (chmod +x); runs `python -m dotnet_ai_kit.cli "$@"`
├── dotnet-ai.cmd       # Windows cmd wrapper
└── README.md           # explains: this is for source-tree use;
                         # `pip install dotnet-ai-kit` is the supported
                         # path for end users
```

If the user actually wants interpretation #1 (true standalone
executable), that's a v1.1 scope item — shiv vs PyInstaller is a
separate spike with cross-platform + supply-chain implications.

**Effort for interpretation #2**: ~1 hour (write 2 wrappers + a
README + a 3-OS test that `bin/dotnet-ai --version` succeeds from a
fresh checkout).

### OOS-004 — Native Codex CLI plugin agents [CANNOT SHIP — Codex docs gap is real]

**Web research findings (May 2026)** — fetched authoritatively from
**[developers.openai.com/codex/plugins](https://developers.openai.com/codex/plugins)**:

> "A plugin can contain: **Skills**: reusable instructions for
> specific kinds of work... **Apps**: connections to tools...
> **MCP servers**: services that give Codex access to additional
> tools..."
>
> "**The documentation does not mention support for an 'agents'
> primitive** in Codex plugins as of the content provided."

Codex CLI v0.117.0 (March 2026) elevated plugins to a first-class
workflow primitive — **but with three primitives (Skills / Apps /
MCP servers), NOT agents**.

**This is exactly the deferral cause the spec records at A-006 /
OOS-004**:
- spec.md `A-006`: "Codex CLI's documented plugin primitives cover
  skills, model-context-protocol servers, and hooks. Native plugin
  agents for Codex are not yet documented and are therefore explicitly
  deferred to a future release."
- `agent_generators.py:190-200` raises `NotImplementedError` with the
  exact OOS-004 message.

**Per spec FR-035** (host admission gate):

> "A new host MUST NOT be added to the supported-host list or the
> configure UI unless it has all of: a documented host-native install/
> update path, **documented artifact primitives for the assets being
> exposed**..."

We cannot add `agents/` to the Codex plugin without violating FR-035.
**If we ship native Codex agents in v1.0.0, we'd be shipping a
capability against an undocumented primitive — the exact failure
mode FR-035 forbids.**

**My recommendation**: **OOS-004 cannot ship in v1.0.0**. The
admission gate is binding. The user is welcome to override this if
they have evidence of Codex's agents primitive that the public docs
don't yet show — but the web research as of 2026-05-18 says no such
primitive exists.

**Best forward-compatible scaffolding** if maintainer wants to
prepare the ground:

1. Keep `generate_codex_agent()` raising NotImplementedError (current).
2. Add a `codex` block under `host_overrides:` in each
   `agents-source/<name>.md` with TBD fields — so when Codex's docs
   land the agent primitive, only the generator needs implementing.
3. Document in `data-model.md` that `host_overrides.codex` is reserved
   for the future agents primitive.
4. File a v1.1 tracking issue: "Implement OOS-004 when
   developers.openai.com/codex/plugins documents an `agents:` field
   in the manifest schema."

**Effort**: ~30 minutes for the scaffolding. The actual generator
implementation is blocked on Codex.

## Aggregated findings from prior reviews

### From `review.md` (CLI-narrow) — superseded

My earlier `AGREED-WITH-NOTES` verdict is wrong; see Correction
section. The only finding from that review that survives is:

- **Note 1**: CI hasn't been triggered on this branch. Still true; now
  ALSO needs the smoke-job rewire (F-B7) before triggering.

### From `tool-surface-review.md` — F1-F6 all still apply

| # | Issue | Status |
|---|---|---|
| F1 | CHANGELOG.md missing v1.0.0 entry | UNCHANGED — HIGH |
| F2 | commands/init.md describes pre-019 bulk-copy | UNCHANGED — HIGH (note: aligns with B-1's frozen-profile issue at the doc layer) |
| F3 | commands/configure.md:126 stale | UNCHANGED — MEDIUM |
| F4 | AGENTS.md root has stale counts | UNCHANGED — MEDIUM |
| F5 | CONTRIBUTING.md has stale counts + csharp-ls reference | UNCHANGED — MEDIUM |
| F6 | rules/cursor/ empty manifest reference | UNCHANGED — LOW-MEDIUM (resolved by OOS-005 if generation lands) |

### From `content-quality-and-oos-review.md` — F-A through F-L survive

| # | Issue | Status |
|---|---|---|
| F-A | 9 skills/core/ missing `when_to_use` | UNCHANGED — MEDIUM |
| F-B | 6 workflow/detection skills missing `metadata.agent` | UNCHANGED — LOW |
| F-C | async-concurrency.md has `paths:` (only universal) | UNCHANGED — LOW |
| F-D | 5/16 rules missing "Related Skills" section | UNCHANGED — MEDIUM |
| F-E | 3 truly empty section headers | UNCHANGED — LOW-MED |
| F-F | host_overrides applied 1/14 in agents-source | UNCHANGED — MEDIUM (doc fix) |
| F-G | 8 Newtonsoft.Json refs without rationale | UNCHANGED — MEDIUM |
| F-H | knowledge/grpc-patterns.md orphan | UNCHANGED — LOW |
| F-I | configuration.md mixed MUST/must | UNCHANGED — LOW |
| F-L | plan-artifacts/SKILL.md thin (78 lines) | UNCHANGED — LOW |

## Consolidated pre-tag punch list

In order of release priority:

### P0 — Release-gating BLOCKERS (must fix)

| ID | Description | Effort |
|---|---|---|
| F-B1 | Skip copy_profile/copy_hook for PLUGIN_NATIVE_HOSTS in init/upgrade/configure/linked-secondary | 3h |
| F-B2 | Migrate init/configure to write UserConfig (`enabled_hosts:`) | 4-6h |
| F-B3 | Migrate save_project to write ProjectMetadata (top-level keys) | 3-4h |
| F-B4 | check validates raw YAML against published schemas | 2h |
| F-B5 | Copilot freshness re-renders + compares | 3h |
| F-B6 | configure picker lists all 4 hosts | 30m |
| F-B7 | CI smoke job runs `tests/integration/test_smoke_*` with env vars | 2-3h |
| F-B8 | Fix 48 ruff errors + 55 format issues | 1h |
| F-B9 | Update verification.md checklist only for passing gates | 30m |
| **Subtotal P0** | | **20-23 hours** |

### Update legacy tests that assert the bugged behavior

| Task | Effort |
|---|---|
| Rewrite `tests/test_cli.py::test_init_force_profile`, `test_upgrade_force_calls_profile`, etc., to assert plugin-native hosts get **no** per-solution rule/profile artifact | 2-3h |
| Update `tests/test_copier_hooks.py` 8 references to `.claude/rules/architecture-profile.md` — should assert `not exists` for plugin-native | 2h |
| Add a CLI-probe test (`tests/integration/test_init_probe.py`) that calls `dotnet-ai init` end-to-end and validates the emitted YAML against the published schemas | 2h |
| **Subtotal** | **6-7 hours** |

### OOS items requested for v1.0.0

| ID | Recommendation | Effort |
|---|---|---|
| OOS-005 | INCLUDE if Cursor smoke passes locally | 2-3h |
| OOS-003 | INCLUDE interpretation #2 (source-tree bin/ wrappers) | 1h |
| OOS-004 | **CANNOT INCLUDE** — Codex docs don't support agents primitive (FR-035 admission gate); ship forward-compatible scaffolding only | 30m |
| **Subtotal** | | **3.5-4.5 hours** |

### Tool surface (F1-F6 from tool-surface-review)

| ID | Effort |
|---|---|
| F1 CHANGELOG v1.0.0 entry | 30m |
| F2 commands/init.md rewrite | 30m |
| F3 commands/configure.md:126 | 5m |
| F4 AGENTS.md counts | 10m |
| F5 CONTRIBUTING.md counts + .mcp.json desc | 10m |
| F6 rules/cursor/ — drop or populate (auto-resolved by OOS-005 if generated) | 15m |
| **Subtotal** | **1.5h** |

### Content polish (F-A through F-L from content-quality review)

| ID | Effort |
|---|---|
| F-A 9 core skills + when_to_use | 30m |
| F-D 5 rules + Related Skills | 30m |
| F-G Newtonsoft rationale | 20m |
| F-H grpc-patterns links | 10m |
| F-I configuration.md MUST/must | 5m |
| F-E 3 empty headers | 10m |
| F-C async-concurrency paths: | 2m |
| F-B 6 workflow skills agent (doc convention) | 5m |
| F-L plan-artifacts review | 15m |
| F-F host_overrides clarification in data-model.md | 15m |
| **Subtotal** | **~2.5h** |

### Grand total

| Tier | Effort |
|---|---|
| P0 BLOCKERS | 20-23h |
| Test corrections | 6-7h |
| OOS items (per user request, with OOS-004 limited to scaffolding) | 3.5-4.5h |
| Tool surface | 1.5h |
| Content polish | 2.5h |
| **TOTAL to v1.0.0 ship-ready** | **~33-39 hours** |

This is roughly **a full week of focused maintainer work**. The spec
+ tests + plugin scaffolding is all in place; what remains is the
runtime-behavior gap (B-1 through B-7) + lint cleanup (B-8) +
documentation polish + the 2 includable OOS items.

## What I'd recommend the maintainer do next

1. **Acknowledge the BLOCKED verdict**. Codex was right. My earlier
   AGREED-WITH-NOTES was wrong, and this consolidated doc explains
   why.

2. **Sequence the P0 fixes** in this order (smallest blast radius
   first):
   - F-B8 (ruff cleanup, 1h, unblocks CI)
   - F-B6 (configure picker, 30m, smallest semantic change)
   - F-B1 (copy_profile skip, 3h, core behavioral fix)
   - F-B2 + F-B3 (config + project schema migration, parallel, 7-10h)
   - F-B4 (check validation, 2h, depends on F-B3)
   - F-B5 (Copilot freshness, 3h, independent)
   - F-B7 (CI smoke wiring, 2-3h, validates the others)

3. **Test correction sprint** — replace 8+ tests that assert the
   bugged behavior with tests that assert the fixed behavior, then
   add the CLI-probe integration test.

4. **OOS-005 conditionally** — run the Cursor smoke fixture; if it
   passes, generate the 12 specialists; if it fails, follow the
   well-documented fail-path.

5. **OOS-003 ship interpretation #2** (source-tree wrappers, 1h).

6. **OOS-004 do NOT include** — ship forward-compatible
   `host_overrides.codex` scaffolding only; file a v1.1 tracking issue
   referencing the Codex docs at `developers.openai.com/codex/plugins`.

7. **Tag v1.0.0 only after** all P0 BLOCKERS resolved + CI green +
   verification.md checked off based on actually-passing gates.

## Verification methodology

Every claim in this review is reproducible:

- **B-1 probe**: `dotnet-ai init <tmp> --ai claude --type generic --json`
  then `find <tmp> -type f`
- **B-2/B-3 probe**: validate emitted YAML against
  `schemas/config-yml.schema.json` / `schemas/project-yml.schema.json`
  with `jsonschema.validate`
- **B-4 probe**: `dotnet-ai check <tmp> --host copilot --json` and
  inspect `checks[]` array
- **B-5 probe**: edit `config.yml` company name, run check, observe
  `copilot_freshness: pass` despite the staleness
- **B-6**: read `cli.py:2286-2297`
- **B-7**: read `.github/workflows/ci.yml:64-88`
- **B-8**: `python -m ruff check src/ tests/` and
  `python -m ruff format --check src/ tests/`

Content quality findings reproducible via:

```
python scripts/quality_scan.py    # round 1
python scripts/quality_scan2.py   # round 2
python scripts/quality_scan3.py   # round 3
python scripts/quality_scan4.py   # round 4
```

## Sources for web-researched OOS guidance

- [Cursor Plugins Reference (May 2026)](https://cursor.com/docs/plugins/building)
- [Cursor 2.4 Subagents announcement](https://memu.pro/blog/cursor-2-4-subagents-skills-memory)
- [Cursor 2.5 changelog (plugins + async subagents)](https://cursor.com/changelog/2-5)
- [Codex CLI Plugins reference (OpenAI)](https://developers.openai.com/codex/plugins)
- [Codex CLI Plugin System blog (Mar 2026)](https://codex.danielvaughan.com/2026/03/30/codex-cli-plugin-system/)
- [PyPA Entry points specification](https://packaging.python.org/specifications/entry-points/)
- [shiv — bundled zipapp distribution](https://github.com/linkedin/shiv)
- [Python zipapp tutorial (Real Python)](https://realpython.com/python-zipapp/)
- [PyInstaller (cross-platform Python executables)](https://medium.com/@touhidulislamnl/building-cross-platform-python-executables-exe-with-pyinstaller-bf698accdbc5)

Sources:
- [Cursor Plugins Reference](https://cursor.com/docs/plugins/building)
- [Cursor 2.4 Subagents](https://memu.pro/blog/cursor-2-4-subagents-skills-memory)
- [Cursor 2.5 changelog](https://cursor.com/changelog/2-5)
- [Codex CLI Plugins (OpenAI)](https://developers.openai.com/codex/plugins)
- [Codex CLI Plugin System blog](https://codex.danielvaughan.com/2026/03/30/codex-cli-plugin-system/)
- [Python entry_points specification](https://packaging.python.org/specifications/entry-points/)
- [shiv project](https://github.com/linkedin/shiv)
- [Python zipapp tutorial](https://realpython.com/python-zipapp/)
- [PyInstaller cross-platform guide](https://medium.com/@touhidulislamnl/building-cross-platform-python-executables-exe-with-pyinstaller-bf698accdbc5)
