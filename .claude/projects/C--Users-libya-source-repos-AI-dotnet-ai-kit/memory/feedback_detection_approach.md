---
name: detection-must-be-behavioral
description: Detection system must analyze project behavior/data-flow not keyword matching - user strongly prefers AI-assisted detection
type: feedback
---

Detection must analyze what the project DOES (data flow, handler behavior, architecture layers) not match keywords/class names.

**Why:** Real projects use custom naming. `LoadFromHistory` could be `RehydrateAggregate` or `BuildFromEvents`. `ICommitEventService` could be `IEventPersister`. Keyword matching breaks on any naming variation.

**How to apply:**
- Layer 1: Parse Program.cs to understand what the app configures (gRPC server? REST? ServiceBus? DB?)
- Layer 2: Analyze handler behavior — does it save to DB? Call other services? Publish events?
- Layer 3: Analyze project structure (folders, references, layers)
- Use AI (Claude/Copilot/Cursor) to analyze code semantically when pattern matching isn't enough
- Apply same behavioral approach to generic architectures (VSA, clean-arch, modular monolith)
- Never rely on specific class/method names — focus on what the code DOES
