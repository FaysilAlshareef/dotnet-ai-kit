# Prompt For /speckit.specify: 027-v2-analyzers-and-deterministic-enforcement

Create a feature specification for `027-v2-analyzers-and-deterministic-enforcement`.

The goal is to expand deterministic enforcement behind the advisory rules and profiles. Use `planning/29-v2-execution-plan-fidelity-and-enhancement.md` Phase I1 as the primary scope, and use `planning/28-v2-artifact-and-tooling-enhancement-plan.md` W5.3 as supporting context.

Required scope:

- Add new DAK analyzer diagnostics for high-value mechanical constraints:
  - Cosmos document `id` casing and serialization expectations.
  - `DbContext` lifetime registration errors where they can be detected reliably.
  - Raw SQL parameterization hazards where they can be detected without excessive false positives.
  - `DateTime.Now` or direct wall-clock usage where `TimeProvider` or injected time should be used.
- Define diagnostic IDs, categories, severities, release notes, and tests for each analyzer.
- Add code fixes only where the fix is safe and mechanical. Do not add unsafe code fixes for policy-only warnings.
- Update `deterministic-enforcement` rule/profile metadata so analyzer-backed constraints are accurately represented.
- Populate or repair `analyzer-backed-constraints` profile metadata where appropriate.
- Keep the analyzer package compatible with the existing analyzer project target and Roslyn package strategy.
- Add regression tests in analyzer tests and acceptance tests where needed.

Out of scope for this feature:

- Full semantic enforcement of advisory-only architecture guidance.
- Profile delivery mechanics.
- Artifact content rewrites except updates needed to accurately reference new analyzer coverage.
- W7 expansion skills/agents.

The generated `tasks.md` must include a dedicated `Review & Verification` phase after implementation phases and before final polish. That review must verify analyzer diagnostics are precise, tests cover positive and negative cases, no broad false-positive rule is introduced, analyzer metadata is synchronized with rules/profiles, and all standing gates pass.

Success criteria must include:

- New analyzers report only on intended violations in tests.
- Existing analyzer tests still pass.
- Analyzer release metadata is updated.
- `deterministic-enforcement` no longer overclaims or misattributes analyzer coverage.
