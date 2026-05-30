---
applyTo: "**/*.cs"
---
# Deterministic Enforcement (rule ↔ analyzer pairings)

These markdown conventions are ALSO enforced at build time by the shipped `Dotnet.Ai.Kit.Analyzers` NuGet:

| Convention (advisory rule) | Analyzer diagnostic | Default severity |
|---|---|---|
| security / async-concurrency — no `async void` | `DAK0001` | warning (elevate to error via `.editorconfig`) |
| add-aggregate — no public setters on aggregates | `DAK0004` | warning |

Advisory rules guide (probabilistic, in-context); analyzers enforce (deterministic, at build). When a
convention is mechanically checkable, pair it here so the two layers cannot silently drift (FR-F6).
