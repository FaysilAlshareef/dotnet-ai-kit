# Prompt For /speckit.specify: 026-v2-progressive-disclosure-and-triggering

Create a feature specification for `026-v2-progressive-disclosure-and-triggering`.

The goal is to improve corpus usability and selector precision without blanket resource bloat. Use `planning/29-v2-execution-plan-fidelity-and-enhancement.md` Phases G, H, and I2/I3 as the primary scope. Use `planning/28-v2-artifact-and-tooling-enhancement-plan.md` W3, W4, and W6 as supporting context. Use `planning/30-artifacts-content-review.md` for description and progressive-disclosure debt.

Required scope:

- Move code-dense skill bodies into progressive-disclosure resources:
  - Multi-variant content goes to `references/<variant>.md`.
  - Large concrete examples go to `examples/`.
  - Keep `SKILL.md` lean and action-oriented.
- Target the code-dense skills identified in planning:
  - `multi-tenancy`, `fluent-validation`, `feature-flags`, `input-sanitization`, `caching-strategies`, `signalr-realtime`
  - `scalar-docs`, `batch-processing`, `aggregate-testing`, `listener-pattern`, `outbox`
  - Include other high-value candidates from `planning/30` where the same pattern is clearly present.
- Add or improve compilable/syntax-valid examples for the heavy microservice band and command/query generator guidance where examples add value.
- Deepen genuinely thin skills called out in planning, especially AI and Blazor Hybrid guidance, without turning every skill into a resource bundle.
- Add `evals/cases.jsonl` for high-confusion selector clusters:
  - auth
  - blazor
  - aspire
  - gateway
  - messaging bus
  - dapr
  - EF/data
- Extend the deterministic triggering/confusion-matrix harness so these evals are loaded and verified.
- Backfill description-standard gaps:
  - Legacy agent descriptions and boundaries.
  - Domain rule descriptions missing `Use when` / `Do NOT use`.
  - Knowledge docs with placeholder migrated descriptions.
  - Self-referential skill descriptions.
- Agent boundaries must name sibling agents by name, not by file path.

Out of scope for this feature:

- Adding W7 new skills/agents.
- Building new analyzers.
- Profile delivery mechanics.
- C# script porting unless needed only as a reference/example cleanup.

The generated `tasks.md` must include a dedicated `Review & Verification` phase after implementation phases and before final polish. That review must verify resource relocation did not remove required guidance, descriptions meet the selector standard, eval cases pass the confusion matrix, generated resources project to all hosts, and all standing gates pass.

Success criteria must include:

- Targeted skills are leaner and their deeper content is available through resources.
- No blanket resource directories are added to every skill.
- New eval clusters pass deterministic triggering checks.
- Agent/rule/knowledge descriptions are materially improved and projection remains drift-clean.
