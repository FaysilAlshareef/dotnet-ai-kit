# Phase 0 Research — v2 Planning-Fidelity Gaps

Decisions that resolve the spec's clarifications and the unknowns in the plan's Technical Context. Format: Decision · Rationale · Alternatives considered.

## R1 — Hook launcher / `dotnet-ai` resolution (FR-022-10)

**Decision**: The generated `hooks.json` keeps invoking the **global `dotnet-ai` tool** (`dotnet-ai hook pretooluse|stop`). Robustness is added around it: (1) `init` and `check` detect a **shadowing shim** — a `dotnet-ai` on PATH whose resolved path is not the v2 .NET tool (e.g. `…/Python*/Scripts/dotnet-ai*`) — and warn with the remediation; (2) `HookCommand` already fails safe and stays so (FR-022-12); (3) the setup docs make `dotnet tool install --global DotnetAiKit.Tool` an explicit prerequisite; (4) an acceptance smoke executes the generated command string and asserts protocol output.

**Rationale**: The hook backend *is* the .NET tool. A Claude plugin is the projected `build/claude/` markdown tree — it carries no .NET runtime/binary, so it cannot self-contain the backend. Requiring the tool is the honest dependency; the real defect is the *stale v1 shim shadowing* + the tool not being installed, both of which are detectable and documentable.

**Alternatives considered**:
- *Plugin-root-relative launcher* (`${CLAUDE_PLUGIN_ROOT}/bin/dai-hook`): rejected — it would have to bundle the .NET runtime/binary per-RID into the plugin (heavy, non-portable, defeats the markdown-plugin model).
- *`dotnet <abs-path-to-dll>`*: rejected — same discovery problem (must locate the dll), and brittle across installs.
- *Bundle a trimmed self-contained single-file exe in the plugin*: deferred with Native-AOT packaging (BD-3); out of scope here.

## R2 — Skill resource depth (FR-022-01/02, AR-5)

**Decision**: Author resources only where they add value (AR-5 opt-in), firm subset:
- `constitution`/`checklist`/`fix`/`release` → workflow `scripts/` (+ `examples/` for `fix`'s failing-test pattern and `release`'s changelog snippet).
- `add-*` (7) → **one canonical compilable C# `examples/`** each (the artifact it generates), plus template `assets/` only where the generator fills a template.
- Ambiguous-cluster skills → `evals/` (see R3).
Bare `SKILL.md` remains valid for self-sufficient knowledge skills.

**Rationale**: 26/AR-5 overrides 23 §368's "every skill"; blanket boilerplate dirs add noise + token/scan cost without value. The firm subset is what FR-D33 + code-gen value actually require.

**Alternatives considered**: *Resource dirs on all 181* (23 §368 literal) — rejected per AR-5. *No resources at all* — rejected; FR-D33 is a firm requirement and code-gen examples are high-value.

## R3 — Eval case format + scoring (FR-022-06/07, AR-6)

**Decision**: `evals/cases.jsonl` per cluster skill — one JSON object per line: `{ "query": "...", "expect": "<skill-name>", "topk": 1 }`. The harness loads all cluster cases and runs a **deterministic top-k lexical score** (the existing `TriggeringOracleTests` scorer, generalized) to assert the correct skill outranks its siblings; CI fails on a miss. A live-LLM eval (≥20 queries/skill) stays a follow-on (AR-6).

**Rationale**: Deterministic + no-network (NFR-1) + reproducible in CI; matches the existing oracle. Clusters first (AR-6) keeps it tractable and high-signal.

**Alternatives considered**: *Live-LLM scoring in CI* — rejected (network + nondeterminism + cost; AR-6 defers). *Embedding-similarity* — rejected (adds a model dependency; lexical is sufficient for sibling-disambiguation at cluster scope).

## R4 — Golden-output testing (FR-022-08/09, NFR-6)

**Decision**: Use **Verify.Xunit** (already referenced) in `Hosts.Tests`. One golden per artifact-type × host (skill/agent/rule/command) + one each for the plugin manifests, `marketplace.json`, `hooks.json`, `AGENTS.md`, `copilot-instructions.md`. Baselines committed as `*.verified.*`; an induced projector format change must fail its golden independent of the drift gate.

**Rationale**: Pins *intent* (the emitted shape), which the drift gate (diff vs committed `build/`) does not. Verify is the planned tool (HANDOFF, NFR-6) and is already a dependency.

**Alternatives considered**: *Rely on the drift gate alone* — rejected (NFR-6 explicitly wants golden output; drift only catches divergence from the committed baseline, not whether the shape is intended). *834 per-file baselines* — rejected (maintenance cost; shape coverage is sufficient).

## R5 — User-owned-file policy (FR-022-13/14, AR-7b)

**Decision**: A shared `UserFilePolicy` (Application) classifies each host write as **managed** (always (re)written) or **user-owned** (`.claude/settings.json`, `AGENTS.md`, `.cursor/rules`, `.github/*`). For user-owned files: if absent → write; if present + unchanged-from-managed → refresh; if present + user-edited → **merge** (JSON deep-merge for `settings.json`) or **back up + diff-preview + mark `PendingConsent`** when a safe merge is impossible. Invalid JSON → back up + warn, never discard. `HostWriteResult.{Preserved,ForceRendered,PendingConsent}` report the outcome. Backups use the existing `BackupRotationService` (3-keep, NFR-7).

**Rationale**: FR-K/AR-7b names this; today `ClaudeHostAdapter` clobbers `settings.json`. The fields already exist on `HostWriteResult` — wire them. Deep-merge for JSON is deterministic; consent/backup for the rest is safe.

**Alternatives considered**: *Always overwrite* (today) — rejected (data loss). *Always skip if present* — rejected (managed refreshes never land). *3-way merge with a stored base* — deferred (needs a stored baseline per file; backup+diff is sufficient for v2.0).

## R6 — T2 `prompt` (Haiku) hook + forced output styles (FR-022-15/16)

**Decision**: Add a PreToolUse **`prompt`-type** hook entry (Claude-scoped, AR-3) for judgment-class checks the analyzer can't make, emitting `permissionDecision: deny` + reason via the Haiku model the host runs. Add a **forced-output-style** artifact projected for Claude as an additional rule-delivery channel (AR-10). Both are additive to the wired command-deny + Stop gate.

**Rationale**: planning/24 §2 reserves the `prompt` hook for judgment; AR-10 calls for the output-style channel. Both are Claude-native and don't touch the deterministic floor.

**Alternatives considered**: *Model judgment in the `command` hook* — rejected (the `command` hook is deterministic/zero-model by design; judgment belongs in the `prompt` hook). *Skip output styles* — rejected (AR-10 names it; low cost to project).

## R7 — Install smoke + Codex/Cursor loadability (FR-022-17/18)

**Decision**: Codify `claude plugin validate build/claude --strict` + `build --strict` as an `Acceptance.Tests` smoke that **skips when the `claude` CLI is absent** (so CI without it stays green) and asserts pass when present. For Codex/Cursor: assert their projected layout against each host's documented discovery (Codex `.agents/skills/`, Cursor own path — planning/21); where a host CLI/validator isn't available, assert structural invariants and **record** the `build/codex/skills/` vs `.agents/skills/` tension explicitly rather than silently diverging.

**Rationale**: AR-2 wants per-host install smoke; the `claude` CLI is available and authoritative for Claude. Codex/Cursor use different discovery, so structural assertions + an honest recorded limitation is the verifiable ceiling here.

**Alternatives considered**: *Hard-require the `claude` CLI in CI* — rejected (not always present; skip-if-absent keeps CI portable). *Blind-fix Codex/Cursor layout to `.agents/skills/`* — rejected (unverifiable here; would risk re-introducing a generated-but-unloadable state).

## R8 — SchemaVersion migration check (FR-022-19)

**Decision**: On corpus load, validate each artifact's `SchemaVersion` against a supported range constant; an out-of-range version fails load with a clear "unsupported schema version N; supported ≤ M — run migrate" message. No data migration is authored yet (all artifacts are v1.0.0); this adds the *guard* the field implies.

**Rationale**: FR-L wants versioning + migration; the field exists but nothing enforces it. The guard prevents a future incompatible artifact from loading silently.

**Alternatives considered**: *Full migration engine now* — deferred (no second schema version exists yet; YAGNI per AR-8). *Ignore the field* — rejected (FR-L).

## R9 — `blazor-hybrid` name-parity (FR-022-20)

**Decision**: Author `blazor-hybrid` to the description standard (MAUI Blazor Hybrid reuse of control-panel components), since the catalog names it; it is low-priority but cheap to add and closes the corpus↔catalog name gap. (If authoring proves out-of-scope, record an explicit de-scope note in planning/23 §5.2 instead — either way the two agree.)

**Rationale**: The goal is "no silent divergence between planning and corpus." Authoring is the cleaner close.

**Alternatives considered**: *Leave absent* — rejected (silent divergence is exactly the gap this feature exists to remove).
