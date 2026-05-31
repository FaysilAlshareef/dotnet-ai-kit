---
description: "Generates a feature-specific quality checklist and runs it as a gate before implement or PR. Use when you need a custom acceptance gate derived from a feature spec. Do NOT use for cross-artifact consistency analysis (use analyze) or build/test verification (use verify)."
---
# /dotnet-ai.checklist — Feature Quality Checklist

Generate a custom, feature-specific checklist from the spec and run it as an explicit gate.

## Usage
```
/dotnet-ai.checklist $ARGUMENTS
```

## Steps
1. Read the active feature's `spec.md` (and `plan.md` if present).
2. Derive concrete, testable checklist items per area (functional, data, UX, NFRs, edge cases).
3. Write `checklists/<name>.md` with `- [ ]` items.
4. Run the checklist as a gate: it must be complete before `implement`/`pr` proceed (incomplete items block).

This is a user-invoked command (off the always-loaded listing).
