# Spec Prompts

These prompts are intended to be pasted into `/speckit.specify` one at a time, in order.

Run the normal command flow for each feature:

```text
/speckit.specify -> /speckit.clarify -> /speckit.plan -> /speckit.tasks -> /speckit.analyze -> /speckit.implement
```

There is no separate `/speckit.review` command in `.claude/commands`. Each prompt therefore requires the generated `tasks.md` to include an explicit `Review & Verification` phase after implementation phases and before final polish.

Recommended order:

1. `023-v2-corpus-correctness-and-delivery-foundation.md`
2. `024-v2-profile-rule-and-dynamic-delivery.md`
3. `025-v2-dotnet-script-and-tooling-cleanup.md`
4. `026-v2-progressive-disclosure-and-triggering.md`
5. `027-v2-analyzers-and-deterministic-enforcement.md`
6. `028-v2-expansion-skills-and-agents.md`
7. `029-v2-kit-mcp-server.md`
