---
applyTo: "**/*.cs"
---
# Error Handling (domain)

- Match the project's existing error model: `Result<T>` OR exceptions + ProblemDetails — not both.
- Throw for truly exceptional cases; return `Result`/typed failures for expected ones.
- Never swallow exceptions; preserve the stack and add context.
