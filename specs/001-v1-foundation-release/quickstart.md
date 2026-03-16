# Quickstart: dotnet-ai-kit v1.0

## Prerequisites

- Python 3.10+
- .NET SDK 8.0+
- Git
- An AI dev tool (Claude Code for v1.0)

## Install

```bash
uv tool install dotnet-ai-kit --from git+https://github.com/{user}/dotnet-ai-kit.git
```

## Initialize in an Existing Project

```bash
cd my-dotnet-project
dotnet-ai init . --ai claude
```

The tool auto-detects your architecture, .NET version, and company name.

## Build Your First Feature

```bash
# One command — spec → plan → code → test → review → PR
/dotnet-ai.do "Add order management with tracking"
```

That's it. For complex features, use the step-by-step commands:

```bash
/dotnet-ai.specify "Add order management"
/dotnet-ai.plan
/dotnet-ai.implement
/dotnet-ai.review
/dotnet-ai.pr
```

## Check Progress

```bash
/dotnet-ai.status
```

## Undo a Mistake

```bash
/dotnet-ai.undo
```

## Learn a Pattern

```bash
/dotnet-ai.explain "clean architecture"
/dotnet-ai.explain --tutorial    # Interactive guided walkthrough
```

## Verify the Installation

```bash
dotnet-ai check
```

Expected output:
```
dotnet-ai-kit v1.0.0
Project: MyCompany.Orders (Clean Architecture, .NET 10)
AI Tools: ✓ Claude Code — 25 commands, 6 rules
Config: ✓ Company: MyCompany
```
