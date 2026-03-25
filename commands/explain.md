---
description: "Explain architecture patterns, code patterns, or tool commands with examples and diagrams"
---

# Explain

Learn about architecture patterns, code patterns, or tool commands with concise explanations, code examples from project patterns, common mistakes, and optional Mermaid diagrams.

## Usage

```
/dotnet-ai.explain $ARGUMENTS
```

**Examples:**
- `aggregate` -- What is an aggregate? When to use it?
- `event-sourcing` -- How event sourcing works in our stack
- `outbox` -- Outbox pattern explained
- `vsa` -- Vertical Slice Architecture
- `"clean architecture"` -- Clean Architecture pattern
- `implement` -- How /dotnet-ai.implement works
- `--tutorial` -- Interactive 5-step onboarding walkthrough
- `--mistakes` -- Common anti-patterns across all topics
- `aggregate --mistakes` -- Anti-patterns for aggregates specifically
- `--verbose` -- Include all sections (description, usage, code, mistakes, diagram)

## Flags

| Flag | Description |
|------|-------------|
| `--tutorial` | 5-step guided walkthrough building a sample feature (dry-run mode) |
| `--mistakes` | Show anti-patterns and common mistakes only |
| `--dry-run` | Same as default behavior (explain is read-only) |
| `--dry-run` | Same as default behavior (explain is read-only) |
| `--verbose` | Include every section: description, when-to-use, code, mistakes, diagram |
| `--diagram` | Include Mermaid diagram even for non-architecture topics |

## Flow

### Step 1: Parse Topic

Extract topic from `$ARGUMENTS`. Normalize aliases:
- `vsa`, `vertical-slice` -> Vertical Slice Architecture
- `ca`, `clean-arch`, `clean-architecture` -> Clean Architecture
- `ddd` -> Domain-Driven Design
- `cqrs` -> Command Query Responsibility Segregation
- `es`, `event-sourcing` -> Event Sourcing
- Command names: `implement`, `specify`, `plan`, etc. -> tool command explanation

### Step 2: Match Topic to Knowledge Sources

Search in order:
1. **Skills**: match topic to skill directory names (e.g., `aggregate` -> `skills/microservice/command/aggregate-design`)
2. **Knowledge docs**: match to `knowledge/` documents
3. **Commands**: match to `commands/` files for tool command explanations
4. **Architecture patterns**: match to `skills/architecture/` skills

If no match found: provide a general explanation based on .NET ecosystem knowledge, noting it is not from project-specific patterns.

### Step 3: Generate Explanation

Read matched skill/knowledge files and produce:

**Section 1: What It Is** (always included)
- 2-3 sentence description of the pattern or concept
- Contextualized to the project stack (not generic)

**Section 2: When to Use** (always included)
- Bullet list of scenarios where this pattern applies
- Include "Do NOT use when..." counter-examples

**Section 3: Code Example** (unless `--mistakes` only)
- Short code example pulled from skill patterns (not invented)
- Annotated with comments explaining key decisions
- Matches project .NET version and conventions

**Section 4: Common Mistakes** (always included, expanded with `--mistakes`)
- What NOT to do with concrete bad-code examples
- Why it is wrong and what happens
- The correct alternative

**Section 5: How the Tool Supports It** (for architecture/pattern topics)
- Which commands generate code for this pattern
- Which skills contain detailed guidance

**Section 6: Mermaid Diagram** (for architecture topics, or with `--diagram`)
- Visual diagram of the pattern
- For architecture: layer diagram or service flow
- For patterns: sequence diagram or component diagram

### Tutorial Mode (`--tutorial`)

When `--tutorial` is specified (with or without a topic), run a guided walkthrough:

```
Step 1/5: Understanding the Feature Spec
  -> Shows a minimal spec.md example
  -> Explains each section and why it matters
  -> "Ready for the next step? [Y/skip]"

Step 2/5: Planning the Implementation
  -> Shows plan.md with layers/services
  -> Explains dependency order and WHY each component is needed

Step 3/5: Implementing Step by Step
  -> Walks through code generation for each component
  -> After each file: explains what it does and how it fits

Step 4/5: Testing and Verification
  -> Shows test structure and what is verified
  -> Explains test patterns used

Step 5/5: Review and PR
  -> Shows review checklist and PR creation
  -> Explains the full lifecycle completion
```

Tutorial uses `--dry-run` mode internally -- no real changes unless user opts in.
If a topic is specified with `--tutorial`, the walkthrough focuses on that topic.

## Topics Covered

**Architecture patterns**: VSA, Clean Architecture, DDD, Microservices, CQRS, Event Sourcing, Modular Monolith
**Microservice patterns**: Aggregate, Event, Outbox, Handler, Listener, Processor, Gateway, Control Panel
**Code patterns**: Repository, Result pattern, MediatR, FluentValidation, Polly, Options pattern
**Tool commands**: All `/dotnet-ai.*` commands (what, when, how)
**Infrastructure**: Docker, Kubernetes, GitHub Actions, Azure, Aspire

## Source

Explanations are sourced from project skills and knowledge documents, not generic AI knowledge. Code examples match the actual patterns used by the tool.

## Preview / Dry-Run Behavior

Explain is inherently read-only. `--dry-run` and `--dry-run` behave identically to the default -- they display the explanation. No files are ever written or modified.
