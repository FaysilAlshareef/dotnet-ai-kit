AGREED-CLEAN-SIGN-OFF

Scope: verified ONLY the six round-3 Codex blocking corrections.

1. Fixed — `specs/019-plugin-native-arch/plan.md:375` lists current packaging targets as `.codex-plugin/`, `.cursor-plugin/`, `agents-source/`, `agents-claude/`, `agents/`, `agents-copilot-templates/`, rules, and schemas. `agents-cursor/` is only a historical note, not a current target.

2. Fixed — `specs/019-plugin-native-arch/plan.md:389` commit 3 acceptance now says Cursor manifest uses scalar relative paths for `skills`, `rules`, `mcpServers`, `hooks`, plus conditional `agents: "./agents/"`; it does not say `rules/subagents references`.

3. Fixed — `specs/019-plugin-native-arch/plan.md:411` commit 6 fixture path is `agents/<one-fixture>.md`, described as the Cursor build-output directory.

4. Fixed — `specs/019-plugin-native-arch/data-model.md:135` section 7 source-of-truth is `agents-source/<name>.md`, not `agents/<name>.md`.

5. Fixed — `specs/019-plugin-native-arch/contracts/cursor-fixture-decision.contract.md:48` fail-path step 7 says to drop `agents/` build output, the current Cursor-format directory referenced as `./agents/`.

6. Fixed — `specs/019-plugin-native-arch/plan.md:101` contracts count now says 18 files.

All six corrections landed. Plan-phase debate is closed; Claude may proceed to `/speckit.tasks`.
