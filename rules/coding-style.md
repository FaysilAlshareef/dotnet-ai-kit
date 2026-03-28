---
alwaysApply: true
description: Enforces C# coding conventions, version-aware (respects detected .NET version).
---

# C# Coding Style

Detect .NET version from `<TargetFramework>` in .csproj files.
Use only features available for the detected version.
Match the existing project style. Never force-upgrade syntax.

## DO (All Versions)

- Use file-scoped namespaces (.NET 6+)
- Use `var` for local variables when type is obvious from the right-hand side
- Use expression-bodied members for single-line methods and properties
- Use `sealed` on classes not designed for inheritance
- Use records for immutable data (event data, DTOs, value objects)
- Use `private set` on entity properties (query side)
- Use factory methods for aggregate creation
- Follow SOLID principles, clean code, and best practices

## DO NOT (All Versions)

- Do not use `DateTime.Now` -- use an injected time provider
- Do not use string concatenation for SQL -- use parameterized queries
- Do not use `async void` -- always return `Task` or `Task<T>`
- Do not catch generic `Exception` unless re-throwing
- Do not use `public set` on domain entity properties
- Do not guess package/framework APIs -- check official documentation first

## DO (Version-Specific)

Only use these when the detected .NET version supports them:
- Primary constructors for DI injection (.NET 8+ / C# 12)
- `required` modifier on properties that must be set (.NET 7+ / C# 11)
- Collection expressions `[..]` (.NET 8+ / C# 12)
- `field` keyword in properties (.NET 14+ / C# 14)

## Key Rule

Before writing any code, detect the project's .NET version and existing style.
Match the C# language level of the existing project.
When in doubt, use the more conservative syntax that works across more versions.

## Related Skills
- `skills/core/solid-principles/SKILL.md` — when to apply and when over-applying hurts
- `skills/core/design-patterns/SKILL.md` — pattern selection for modern C#
- `skills/core/coding-conventions/SKILL.md` — detailed convention patterns
