# Prompt For /speckit.specify: 030-v2-release-distribution-and-fidelity-closeout

Create a feature specification for `030-v2-release-distribution-and-fidelity-closeout`.

The goal is to make the kit installable end-to-end as a released product and to close the fidelity items no other feature owns. Use `planning/26-v2-build-plan-and-decisions.md` BD-3 (framework-dependent `dotnet tool` GA distribution) and AR-7 item (d) (release/rollback plan) as the distribution authority. Use `planning/27-post-022-fidelity-and-defect-audit.md` items A8, A9, and R1–R5 (sequenced as Phase F in `planning/29-v2-execution-plan-fidelity-and-enhancement.md`) as the closeout inventory. This feature deliberately precedes `029-v2-kit-mcp-server`: the corpus-location decision made here is an input to the 029 plan.

Required scope:

- Release pipeline:
  - Add a tag-triggered release workflow that packs and publishes `DotnetAiKit.Tool` and `Dotnet.Ai.Kit.Analyzers` to NuGet.org, with the version stamped from a single source and release notes derived from `CHANGELOG.md`.
  - Version the plugin manifest and marketplace output under `build/` in lockstep with the tool version, and document how users install and update from the git-hosted marketplace.
  - Define rollback for a bad release: NuGet deprecate/unlist for packages, marketplace pin to the previous tag for the plugin, and the order in which they are applied.
- Install story and first-run integrity:
  - Add an end-to-end install smoke: pack, install the tool from the local nupkg into an isolated tool path, validate the plugin, `init` a sample solution, fire `hook pretooluse` and `hook stop` through the installed binary, and pass `check`.
  - Harden bare `dotnet-ai` hook invocation: hooks must fail soft with actionable guidance when the tool is missing or shadowed by a stale shim earlier on PATH, and `check` diagnostics must name the exact fix.
  - Decide and implement corpus location for installed tools: where `dotnet-ai` resolves the corpus when run outside this repository (embedded in the package, resolved from the installed plugin path, or explicit `--artifacts`), with documented precedence rules. `029` consumes this decision.
- Cross-host load parity:
  - Verify Codex, Cursor, and Copilot outputs load or parse per each host's documented contract — a real validator where one exists, a structural contract test where none does — equivalent in spirit to the existing `claude plugin validate --strict` smoke.
- Fidelity closeout (byte-stable; the drift gate must prove no generated-output change):
  - A8: add an architecture fitness test — Core references no other kit project and no third-party packages; Application references no Hosts, Infrastructure, Cli, or Spectre.
  - A9: reword the `CompositionRoot` init `NotSupportedException` so plugin-native and render-only hosts are described as intentionally out of scope, not "not implemented yet".
  - R1–R5: delete the duplicate `ClaudeProjector.FrontmatterBuilder`; extract a single shared YAML scalar escaper to replace the five copy-pasted ones; introduce `PluginNativeHostBase` across the four projectors; route `manifest.yml` parsing through the injected `IArtifactSerializer`; populate or remove the unused failure channels in `OrchestrateService`/`ConfigureService`/`MigrateService`.
- Documentation truth:
  - Corpus counts in `README.md` and `CLAUDE.md` currently disagree with the loaded corpus; correct them and guard documented counts with an acceptance test (or generate them) so they cannot drift again.
  - Refresh `README.md` and `docs/setup-*.md` install instructions to match the released install path.

Out of scope for this feature:

- The kit MCP server runtime (`029`).
- Native AOT publishing (deferred by BD-3).
- New skills, agents, or artifact content changes beyond documentation accuracy.
- Package code-signing beyond standard NuGet publish requirements.
- Telemetry or usage analytics.

The generated `tasks.md` must include a dedicated `Review & Verification` phase after implementation phases and before final polish. That review must verify the release workflow is dry-run-proven without publishing, no credentials or secrets are committed, the install smoke passes from a clean environment, the refactors leave generated output byte-identical, the fitness test fails on a seeded layering violation, documentation counts match the loaded corpus, and all standing gates pass.

Success criteria must include:

- A tag-triggered release workflow exists and its pack + isolated-install + hook-fire smoke passes in CI without publishing.
- Corpus location for installed tools is implemented, tested, documented, and ready for `029` to consume.
- Codex, Cursor, and Copilot outputs pass load/structure verification.
- The A8 fitness test catches a seeded layering violation; R1–R5 and A9 land with `generate --check` drift-clean.
- Documented corpus counts are test-guarded and correct.
- All standing gates pass.
