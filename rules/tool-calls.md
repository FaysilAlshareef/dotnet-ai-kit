---
alwaysApply: true
description: Guides AI assistants to use sequential tool calls and verify tool availability.
---

# Tool Call Best Practices

## Sequential Tool Calls

Use sequential tool calls instead of chaining commands with `&&`.
Each tool call should be a single, focused operation.

### DO

- Run one command per tool call
- Check the result of each command before proceeding
- Use separate tool calls for build, test, and format steps

### DO NOT

- Do not chain commands with `&&` (e.g., `dotnet build && dotnet test`)
- Do not chain commands with `;` unless failures are acceptable
- Do not use `||` for fallback logic in a single tool call
- Do not combine unrelated operations in one shell invocation

### Example -- Correct

Step 1: `dotnet build`
Step 2: (check result) then `dotnet test`
Step 3: (check result) then `dotnet format --verify-no-changes`

### Example -- Incorrect

Single call: `dotnet build && dotnet test && dotnet format --verify-no-changes`

## Tool Availability

Before constructing a command, verify the tool is available:

- Check if `dotnet` is on PATH before running .NET commands
- Check if `git` is on PATH before running git commands
- Check if `gh` is on PATH before running GitHub CLI commands
- Check if `docker` is on PATH before running container commands

If a tool is not available, inform the user and suggest installation:

| Tool     | Install URL                             |
|----------|-----------------------------------------|
| dotnet   | https://dot.net/download                |
| git      | https://git-scm.com/downloads           |
| gh       | https://cli.github.com                  |
| docker   | https://docs.docker.com/get-docker/     |

## Error Handling

- Read the full error output before retrying a command
- Do not retry the same command without changing something
- Report clear error messages to the user with suggested fixes
