# Implement-Phase Round 3: Codex Verification

**Verdict: AGREED-WITH-NITS**

Blocking findings: none.

## Verified Fixes

1. Plain `dotnet-ai upgrade` no longer bulk-copies for Copilot-only configs. The upgrade loop now skips `RENDER_ONLY_HOSTS` before the legacy `copy_commands` / `copy_rules` / `copy_skills` / `copy_agents` branch, and the permissions re-apply is gated by `claude in config.ai_tools`. See `src/dotnet_ai_kit/cli.py:1829`, `src/dotnet_ai_kit/cli.py:1841`, `src/dotnet_ai_kit/cli.py:1931`.

2. `dotnet-ai configure --tools copilot` no longer writes Claude permissions or legacy Copilot command/rule/skill/agent copies. Permissions are gated on `claude in config.ai_tools`; both configure re-copy loops skip `PLUGIN_NATIVE_HOSTS` and `RENDER_ONLY_HOSTS` before the legacy copy path. See `src/dotnet_ai_kit/cli.py:2334`, `src/dotnet_ai_kit/cli.py:2375`, `src/dotnet_ai_kit/cli.py:2389`, `src/dotnet_ai_kit/cli.py:2421`.

3. The two sibling regression tests assert the exact no-bulk-copy/no-Claude-settings behavior. See `tests/unit/test_codex_blockers_resolved.py:225` and `tests/unit/test_codex_blockers_resolved.py:259`.

## Third-Tier Sibling Scan

No new blocking sibling gap found in the feature-019 command surface.

- `init` routes plugin-native hosts and render-only hosts away from bulk copy; only the fallback branch calls legacy copy helpers. Claude permissions are selected-host gated. See `src/dotnet_ai_kit/cli.py:969`, `src/dotnet_ai_kit/cli.py:983`, `src/dotnet_ai_kit/cli.py:993`, `src/dotnet_ai_kit/cli.py:1128`.
- Linked-secondary deploy routes Copilot through `CopilotHost.render()` and continues before bulk copy; plugin-native hosts also avoid bulk copy. See `src/dotnet_ai_kit/copier.py:1050`, `src/dotnet_ai_kit/copier.py:1061`, `src/dotnet_ai_kit/copier.py:1063`, `src/dotnet_ai_kit/copier.py:1096`.
- `render` only resolves content and writes to stdout. See `src/dotnet_ai_kit/cli.py:2604` and `src/dotnet_ai_kit/cli.py:2622`.
- `migrate` classifies manifest entries and moves/removes only manifest-scoped files to backup; it explicitly does not re-render Copilot. See `src/dotnet_ai_kit/cli.py:2661`, `src/dotnet_ai_kit/cli.py:2670`, `src/dotnet_ai_kit/cli.py:2713`, `src/dotnet_ai_kit/cli.py:2790`.
- `check` is documented and implemented as read-only validation, including plugin install, metadata, manifest, and Copilot freshness checks. See `src/dotnet_ai_kit/cli.py:2934`, `src/dotnet_ai_kit/cli.py:2955`, `src/dotnet_ai_kit/cli.py:2980`, `src/dotnet_ai_kit/cli.py:3093`.

## Nit

`extension-add` still has legacy extension behavior: it installs the extension, then `_register_extension_files()` writes command/rule files into any pre-existing host command/rule directories. See `src/dotnet_ai_kit/cli.py:3179`, `src/dotnet_ai_kit/extensions.py:281`, `src/dotnet_ai_kit/extensions.py:293`, `src/dotnet_ai_kit/extensions.py:342`, `src/dotnet_ai_kit/extensions.py:357`, `src/dotnet_ai_kit/extensions.py:374`. I am not blocking on this because feature 019 explicitly keeps the extensions subsystem out of scope. See `specs/019-plugin-native-arch/spec.md:246` and `specs/019-plugin-native-arch/spec.md:261`.

## Permission Gates

No missed fourth write gate found. Permission/settings writes are gated to Claude in init, upgrade, configure, and linked-secondary Claude handling. See `src/dotnet_ai_kit/cli.py:1128`, `src/dotnet_ai_kit/cli.py:1931`, `src/dotnet_ai_kit/cli.py:2334`, `src/dotnet_ai_kit/copier.py:1063`.

## FR Coverage

No new spec-level blocker found. The spec binds no-bulk-copy and selected-host writes at FR-014/FR-015/FR-016 and linked-secondary behavior at FR-033. See `specs/019-plugin-native-arch/spec.md:171`, `specs/019-plugin-native-arch/spec.md:172`, `specs/019-plugin-native-arch/spec.md:173`, `specs/019-plugin-native-arch/spec.md:205`. The traceability table maps FR-001 through FR-035 to tests, including FR-015/FR-016/FR-033. See `specs/019-plugin-native-arch/traceability.md:11`, `specs/019-plugin-native-arch/traceability.md:25`, `specs/019-plugin-native-arch/traceability.md:26`, `specs/019-plugin-native-arch/traceability.md:43`.

## Command Evidence

- Commit 18: `8faeeba feat(019): commit 18 - resolve 2 sibling-gap blockers from Codex round 2`
- `pytest tests/unit/test_codex_blockers_resolved.py -v`: 9 passed
- Sibling-only pytest: 2 passed
- `pytest --tb=no -q`: 729 passed, 25 skipped
- `python scripts/measure_always_on.py`: 2880 total tokens, 68.0% reduction
- `python scripts/doc_lint.py`: OK, 24 files scanned
