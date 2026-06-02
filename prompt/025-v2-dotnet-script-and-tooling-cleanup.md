# Prompt For /speckit.specify: 025-v2-dotnet-script-and-tooling-cleanup

Create a feature specification for `025-v2-dotnet-script-and-tooling-cleanup`.

The goal is to dogfood .NET 10 file-based apps for bundled skill scripts and clean up related tooling gaps. Use `planning/29-v2-execution-plan-fidelity-and-enhancement.md` Phase E as the authoritative scope, and use `planning/28-v2-artifact-and-tooling-enhancement-plan.md` W2 as supporting rationale.

Required scope:

- Port the four existing Python skill scripts to .NET file-based C# scripts:
  - `constitution/scaffold_constitution`
  - `checklist/generate_checklist`
  - `fix/repro_test`
  - `release/bump_version`
- Scripts must be BCL-only and must not use `#:package`, NuGet restore, network calls, or project-local dependencies.
- Scripts must be invoked with `dotnet run --file <script>.cs` to avoid project-cone ambiguity.
- Update script trust handling so `.cs` scripts are recognized as executable bundled scripts and are never auto-run without explicit consent.
- Add the two deterministic new C# scripts:
  - `event-catalogue` generator script using the corrected event construction pattern.
  - `changelog-gen` script using deterministic `git log` parsing, not brittle pipe/grep behavior.
- Fix the event-catalogue broken `Activator.CreateInstance` sample as part of the script extraction.
- Resolve `IGitClient`/`GitCliClient` dead-code status by either wiring it into `OrchestrateService` dirty-tree skip behavior or deleting it with rationale.
- Keep generated output byte-stable and update all projected host skill resources by regeneration.

Out of scope for this feature:

- Adding scripts to `add-*`, `command-generator`, or `query-generator`; those remain judgment-codegen and should use examples, not deterministic scripts.
- Progressive-disclosure relocation beyond script extraction.
- New W7 skills/agents.
- Kit MCP server runtime.

The generated `tasks.md` must include a dedicated `Review & Verification` phase after implementation phases and before final polish. That review must verify no Python script remains in the targeted script set, `.cs` scripts are trust-marked, scripts run with `dotnet run --file`, scripts are no-network, generated output is drift-clean, and all standing gates pass.

Success criteria must include:

- Existing script behavior is preserved after C# porting.
- Each C# script has a smoke test or deterministic command test.
- `.cs` script trust recognition is tested.
- No `#:package` appears in bundled scripts.
- `event-catalogue` and `changelog-gen` no longer ship the reported broken behavior.
