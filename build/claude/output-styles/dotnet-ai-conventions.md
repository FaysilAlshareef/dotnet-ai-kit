---
name: dotnet-ai-conventions
description: Always-on dotnet-ai-kit .NET conventions and enforcement discipline.
---
# dotnet-ai-kit conventions (always-on)

While this plugin is enabled, when working in this .NET solution:

- Follow the projected domain rules in `.claude/rules/*.md` for the file you are editing (they load by `paths:` scope); universal rules always apply.
- Respect the detected architecture profile's boundaries; do not cross layer/dependency lines.
- Mechanical conventions are enforced by the shipped Roslyn analyzer (DAK0001 no `async void`; DAK0004 aggregates expose no public setters) — write code that compiles clean under them.
- Do not claim a task done without fresh build + test evidence (the Stop gate verifies this).
- Prefer the bundled skill examples/scripts over improvising; never auto-run a bundled script without consent.
