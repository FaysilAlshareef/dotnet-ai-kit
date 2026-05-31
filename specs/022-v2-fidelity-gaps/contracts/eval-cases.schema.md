# Contract: `evals/cases.jsonl` schema + confusion-matrix gate (FR-022-06/07)

## File

`artifacts/skills/<category>/<skill>/evals/cases.jsonl` — one JSON object per line (JSONL), authored for ambiguous-cluster skills (mediator, CQRS, eventing, testing, architecture, gateway/control-panel).

```jsonl
{"query": "dispatch a command through a thin mediator port", "expect": "mediator-abstraction", "topk": 1}
{"query": "add an event-sourced aggregate root with domain events", "expect": "add-aggregate", "topk": 1}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `query` | string | yes | natural-language trigger phrase |
| `expect` | string | yes | skill `name` that MUST rank within `topk` |
| `topk` | int | no (default 1) | acceptable rank window |

**Validation**: `expect` MUST be a real skill name (else the loader fails, like the broken-edge gate). Each cluster MUST have ≥1 case per member to be a meaningful matrix.

## Gate (deterministic, no network — NFR-1)

For every case across a cluster:
1. Score each cluster skill's `description` against `query` (the existing `TriggeringOracleTests` lexical scorer, generalized).
2. PASS iff `expect` ranks within `topk` AND no sibling ranks strictly above it.
3. CI fails on any miss (SC-D / SC-022-3).

**Negative test**: editing a description to collide with a sibling MUST flip a case to fail (proves the gate has teeth).

A live-LLM eval (≥20 queries/skill, held-out) is a tracked follow-on (AR-6); this contract is the deterministic cluster gate.
