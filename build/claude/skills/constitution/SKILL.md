---
name: constitution
description: "Creates or amends the project's governing constitution — the principles the whole SDD cycle obeys. Use when establishing or changing project-wide principles before specify/plan. Do NOT use to extract existing project knowledge (use learn) or to author a feature specification (use specify)."
disable-model-invocation: true
---
# /dotnet-ai.constitution — Project Constitution

Establish or amend `.dotnet-ai-kit/constitution.md` (the governing principles the cycle enforces).

## Usage
```
/dotnet-ai.constitution $ARGUMENTS
```

## Steps
1. Load the existing constitution if present; otherwise start from the template principles.
2. Apply the requested principle changes; bump the version (MAJOR principle removal/redefinition, MINOR addition/expansion, PATCH wording).
3. Record a Sync Impact Report (version delta, modified principles, follow-ups) at the top.
4. Propagate any dependent template/doc updates.
5. The constitution gates `analyze` and `review` — conflicts there are CRITICAL and resolved by amending spec/plan/tasks, not the principle.

This is a user-invoked command (off the always-loaded listing).
