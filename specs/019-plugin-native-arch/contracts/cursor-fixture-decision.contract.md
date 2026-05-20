# Contract: Cursor Sub-Agent Fixture Decision Rule

**Spec source**: spec A-005, SC-008, OOS-005; CP6 binding from plan-phase round 2
**Test**: `tests/integration/test_smoke_cursor.py` + `tests/unit/test_fr029_cursor_fail_path.py`
**Verification checklist**: CHK003, CHK004

## Purpose

Hard CI-level decision rule for the Cursor sub-agent fixture. Spec language already says "the release must not quietly ship a failed capability as supported" (FR-001 + edge case "Experimental host capability with undocumented loader"); this contract makes that rule mechanically enforceable.

## The fixture

One Cursor-format sub-agent file at `agents/<single-fixture-name>.md` (per round-3 P2 resolution: Cursor manifest points to `./agents/`, which is the Cursor build-output directory; source-of-truth markdown body lives in `agents-source/<name>.md`).

The fixture's frontmatter follows Cursor's verified shape per `cursor/plugins/agent-compatibility/agents/startup-review.md`: `name`, `description`, `model`, `readonly`.

The fixture is referenced from `.cursor-plugin/plugin.json`'s `agents` field pointing to `./agents/`.

## Pass condition

`tests/integration/test_smoke_cursor.py` (gated by `CURSOR_SMOKE=1` env var + `cursor` CLI on PATH) MUST pass:

1. Install the dotnet-ai-kit plugin in Cursor (via `/add-plugin` or symlink to `~/.cursor/plugins/local/dotnet-ai-kit/`)
2. Query Cursor's listing of available sub-agents
3. Assert the fixture is present in the listing

When the smoke test passes:
- The `agents` field stays in `.cursor-plugin/plugin.json`
- Full Cursor sub-agent generation lands (all 13 specialists, not only the one fixture)
- Spec A-005 outcome recorded as "spike passed"
- Release notes state "Cursor sub-agent generation shipped" (CHK062)

## Fail condition

If `test_smoke_cursor.py` FAILS in CI:

The PR CI fails the build. The only path to a green build is for the **same PR** to make ALL of the following changes:

1. **Remove `agents` field from `.cursor-plugin/plugin.json`** (the Cursor manifest no longer advertises sub-agent support)
2. **Update `cursor-plugin.schema.json`** to make `agents` field absent (not just optional)
3. **Update `spec.md`**:
   - A-005 → "Cursor sub-agent support is deferred to v1.1 because the v1 spike fixture failed under Cursor's loader"
   - SC-008 → remove the Cursor smoke fixture from the mandatory-pass list; document that Cursor's smoke fixture failed and the spec was revised
   - OOS-005 → "Full Cursor sub-agent generation deferred to v1.1 (spike failed)"
4. **Update `checklists/verification.md`** CHK003 / CHK004 to reflect the deferral
5. **Update release notes** to state "Cursor sub-agent generation deferred to v1.1" (CHK062 — alternative branch)
6. **Update `agent_generators.py`** to disable `generate_cursor_agent()` (raise NotImplementedError with clear message)
7. **Update Cursor packaging** to drop the `agents/` build output (the Cursor-format agent files; per round-3 P2, this is the Cursor build-output directory referenced by the manifest as `./agents/`)

The CI rule: if `test_smoke_cursor.py` fails AND any of items 1-7 are missing, the build fails.

## Verification

A meta-test `tests/unit/test_fr029_cursor_fail_path.py` (CHK052 area) verifies the consistency:

- Fixture `tests/fixtures/cursor_fixture_pass/`: `.cursor-plugin/plugin.json` has `agents`, spec A-005 says "passed", spec OOS-005 mentions deferral hypothetically
- Fixture `tests/fixtures/cursor_fixture_fail/`: `.cursor-plugin/plugin.json` has NO `agents` field, spec A-005 says "failed and deferred", spec OOS-005 confirms deferral, release notes confirm deferral
- Test asserts the consistency: `agents` field presence ↔ spec language ↔ release-notes language

In CI, the actual outcome runs `test_smoke_cursor.py`; the meta-test ensures the codebase is in a consistent state for either outcome.

## What this contract MUST NOT allow

- MUST NOT allow silent ship of a failed capability (the spec already says this; this contract is the enforcement)
- MUST NOT allow `.cursor-plugin/plugin.json` to advertise `agents` while the smoke fixture is failing
- MUST NOT allow spec/contracts/release notes to drift out of sync with the actual fixture outcome
