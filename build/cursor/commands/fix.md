---
description: "Runs a TDD bug-fix loop — write a failing test reproducing the symptom, fix it, then verify the test passes. Use when fixing a reported bug. Do NOT use for new feature work (use implement) or standards review (use review)."
---
# /dotnet-ai.fix — TDD Bug-Fix Loop

Fix a bug the disciplined way: reproduce → fix → verify.

## Usage
```
/dotnet-ai.fix $ARGUMENTS
```

## Steps
1. **Reproduce**: write a failing test that captures the reported symptom; confirm it fails for the right reason.
2. **Fix**: make the minimal change that turns the test green; respect existing conventions (do not refactor unrelated code).
3. **Verify**: run build + tests; confirm the new test passes and nothing regressed.
4. Report the root cause and the test that now guards it.

This is a user-invoked command (off the always-loaded listing).
