# BLOCK-WITH-CONCERNS

Do not merge. The requested baseline checks are green, but commit 16 leaves
multiple feature-contract failures in the highest-risk surface.

## Required Checks

- `pytest --tb=no -q`: GREEN, `720 passed, 25 skipped in 44.82s`.
- `python scripts/measure_always_on.py`: GREEN, `2880` tokens, `68.0%` reduction, target band pass.
- `python scripts/doc_lint.py`: GREEN, `24 files scanned`.
- `python scripts/check.py --static-only`: GREEN.

## Blockers

1. **Host selection is not isolated. `init --ai codex` writes Claude files.**

   Spec requires init to write files only for selected hosts at `specs/019-plugin-native-arch/spec.md:171`. Current init calls `copy_permissions(...)` unconditionally after the host loop at `src/dotnet_ai_kit/cli.py:1109-1118`; `copy_permissions` always targets `target_dir / ".claude" / "settings.json"` at `src/dotnet_ai_kit/copier.py:1325-1360`.

   Failing assertion:
   `assert not (tmp_path / ".claude" / "settings.json").exists(), "init --ai codex must not write Claude settings"`

   Actual: assertion fails; `.claude/settings.json` exists after `dotnet-ai init --ai codex`.

2. **Copilot init is not render-only; it still takes the legacy command-copy path.**

   FR-007 requires Copilot init to render the three Copilot-native content classes at `specs/019-plugin-native-arch/spec.md:155`. Instead, Copilot still has a legacy `commands_dir` of `.github/agents/commands` at `src/dotnet_ai_kit/agents.py:36-42`; because Copilot is not in `PLUGIN_NATIVE_HOSTS`, init enters the bulk-copy branch at `src/dotnet_ai_kit/cli.py:958-982` before the Copilot render call at `src/dotnet_ai_kit/cli.py:1039-1050`.

   Failing assertion:
   `assert not (tmp_path / ".github" / "agents" / "commands").exists(), "Copilot init must not write legacy command-agent files"`

   Actual: assertion fails; `dotnet-ai init --ai copilot` writes `.github/agents/commands/dai.*.agent.md` files.

3. **Copilot repository-wide render is still a placeholder, not the full contract.**

   The Copilot instructions contract requires project identity, the five convention rule bodies, path-scoped pointers, active architecture profile, and agent quick reference at `specs/019-plugin-native-arch/contracts/copilot-instructions.contract.md:13-17`. The implementation returns a hard-coded placeholder at `src/dotnet_ai_kit/hosts/copilot.py:299-341`, including the comment that full jinja2 render is follow-up at `src/dotnet_ai_kit/hosts/copilot.py:300-305`. That conflicts with the "no v1.1 deferrals" claim for commit 16.

   Failing assertion:
   `assert "async-concurrency" in body, "repository-wide Copilot instructions must inline convention rule bodies"`

   Actual: assertion fails; output contains `_Convention rule bodies will be inlined here in the full render._`.

4. **`upgrade --copilot` cannot refresh its own managed renders without `--force-render`.**

   US2 requires the Copilot refresh action to reflect changed metadata at `specs/019-plugin-native-arch/spec.md:60`, and FR-015 requires `upgrade --copilot` to re-render using current plugin source and project metadata at `specs/019-plugin-native-arch/spec.md:172`. The render code treats every existing Copilot file as a user-consent conflict at `src/dotnet_ai_kit/hosts/copilot.py:153-156`, `src/dotnet_ai_kit/hosts/copilot.py:169-173`, and `src/dotnet_ai_kit/hosts/copilot.py:190-195`; the CLI exits non-zero on those conflicts at `src/dotnet_ai_kit/cli.py:1601-1603`.

   Failing assertion:
   `assert result.exit_code == 0, result.output`

   Actual: `upgrade --copilot --json` exits `1` after init, with `written: []` and every previously rendered file under `pending_user_consent`; the updated `project.yml` value is not rendered.

5. **Copilot manifest ownership and freshness detection are incomplete.**

   The contract says `dotnet-ai check` must report stale Copilot renders and that renders are recorded in the manifest with `host_owner: "copilot"` at `specs/019-plugin-native-arch/contracts/copilot-instructions.contract.md:21-27`; SC-006 repeats stale-render detection at `specs/019-plugin-native-arch/spec.md:232`. Current `_MANIFEST_SCAN_DIRS` only includes `.github/copilot-instructions.md`, not `.github/instructions/` or `.github/agents/`, at `src/dotnet_ai_kit/cli.py:523-534`. Init then finalizes the manifest through that incomplete scan at `src/dotnet_ai_kit/cli.py:1154-1158`. The validation command still has a stubbed freshness pass at `src/dotnet_ai_kit/cli.py:3043-3053`.

   Failing assertions:
   `assert rendered_agent_paths <= manifest_paths`
   `assert result.exit_code == 15, result.output`

   Actual: all rendered `.github/agents/*.agent.md` files are missing from the manifest, and `dotnet-ai check --host copilot --json` returns exit code `0` with `copilot_freshness: pass` after `project.yml` changes.

6. **Linked-secondary Copilot deployment preserves the legacy copy architecture.**

   The linked-secondary edge case requires the secondary writer to honor the same plugin-native footprint and not preserve the old copy architecture at `specs/019-plugin-native-arch/spec.md:138`; FR-033 repeats that requirement at `specs/019-plugin-native-arch/spec.md:205`. Current `deploy_to_linked_repos` sends render-only/future hosts into the legacy bulk-copy branch at `src/dotnet_ai_kit/copier.py:1037-1083`, then calls `copy_commands` and `copy_rules` at `src/dotnet_ai_kit/copier.py:1086-1093`. There is no `CopilotHost.render(...)` path for linked secondaries.

   Failing assertion:
   `assert (secondary / ".github" / "copilot-instructions.md").is_file(), "linked Copilot deploy must render Copilot instructions"`

   Actual: assertion fails; linked Copilot deploy does not render `.github/copilot-instructions.md`.

## Verdict

BLOCK-WITH-CONCERNS. The green baseline does not cover the failing Copilot and host-selection contracts above. These are not nits; they break US2, FR-014, FR-015, FR-017, FR-033, SC-006, and SC-014.
