---
name: error-handling
description: "Applies the project's structured error-handling pattern (Result or ProblemDetails) consistently. Use when adding error paths, validation, or exception handling in C# files. Do NOT use for logging/metrics configuration (use observability)."
metadata:
  paths: "**/*.cs"
  analyzer-backed: "false"
---
# Error Handling (domain)

- Match the project's existing error model: `Result<T>` OR exceptions + ProblemDetails — not both.
- Throw for truly exceptional cases; return `Result`/typed failures for expected ones.
- Never swallow exceptions; preserve the stack and add context.
