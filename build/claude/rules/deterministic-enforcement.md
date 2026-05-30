---
name: deterministic-enforcement
description: "Declares which markdown rules and profiles have a paired Roslyn analyzer diagnostic so the advisory and deterministic layers stay in sync. Use when adding or changing a convention that should be mechanically enforced at build time. Do NOT use for advisory-only guidance (use the relevant domain rule)."
paths:
  - "**/*.cs"
---
# Deterministic Enforcement (rule ↔ analyzer pairings)

These markdown conventions are ALSO enforced at build time by the shipped `Dotnet.Ai.Kit.Analyzers` NuGet:

| Convention (advisory rule) | Analyzer diagnostic | Default severity |
|---|---|---|
| security / async-concurrency — no `async void` | `DAK0001` | warning (elevate to error via `.editorconfig`) |
| add-aggregate — no public setters on aggregates | `DAK0004` | warning |

Advisory rules guide (probabilistic, in-context); analyzers enforce (deterministic, at build). When a
convention is mechanically checkable, pair it here so the two layers cannot silently drift (FR-F6).
