# Prompt For /speckit.specify: 023-v2-corpus-correctness-and-delivery-foundation

Create a feature specification for `023-v2-corpus-correctness-and-delivery-foundation`.

The goal is to repair the highest-risk shipped corpus and delivery defects before any expansion work. Use `planning/29-v2-execution-plan-fidelity-and-enhancement.md` as the execution baseline and use `planning/30-artifacts-content-review.md` plus `planning/30-appendix-all-artifacts.md` as the defect inventory. Treat `planning/28-v2-artifact-and-tooling-enhancement-plan.md` as supporting context, not the full scope for this feature.

Required scope:

- Fix the 8 broken shipped artifact samples identified in `planning/30`.
- Fix the serious correctness and security defects identified in `planning/30` section 3 where they are localized enough for this foundation feature.
- Repair MediatR Tier-A policy drift: remove domain-layer `INotification` leaks, stop teaching raw MediatR as the default, and align root CQRS guidance with the existing mediator-abstraction rule.
- Remove obvious v1/Python residue in touched shipped artifacts, including stale `pip install dotnet-ai-kit`, nonexistent Python `mcp_check`, `pytest`/`ruff` references in .NET-only guidance, and stale command names.
- Fix Cursor plugin delivery: the Cursor plugin manifest must live under the Cursor plugin root, any referenced agents must be emitted, and generated manifest references must resolve.
- Wire real manifest integrity into `check`: existence-only `manifest-integrity` is not enough; tampering must be detected by SHA-256 verification or the guarantee must be explicitly renamed and descoped.
- Add regression tests and acceptance gates for the above, including manifest-reference resolution and manifest tamper detection.

Out of scope for this feature:

- Profile delivery and rule/profile deduplication.
- MCP/LSP projection.
- Porting skill scripts to C#.
- Progressive-disclosure relocation into references/examples except where needed to fix a broken sample.
- New W7 skills or agents.
- Kit's own MCP server runtime.

The specification must require generated output to remain single-source from `artifacts/`; do not permit hand edits to `build/` except through regeneration.

The generated `tasks.md` must include a dedicated `Review & Verification` phase after implementation phases and before final polish. That phase must review changed source, changed artifacts, generated build output, policy consistency, and run the standing gates: build, test, format, and `generate --check`.

Success criteria must be concrete:

- All current standing gates pass.
- Cursor plugin manifest references resolve.
- Manifest tampering fails `check`.
- Fixed artifact samples no longer contain the reported broken behavior.
- MediatR Tier-A violations are removed or explicitly redirected to the license-safe abstraction policy.
