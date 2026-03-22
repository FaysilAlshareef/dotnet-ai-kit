---
alwaysApply: true
description: Enforces resource-based localization in all projects using resource files.
---

# Localization Rules

If the existing project does not use localization, do not add it unless asked.
If it uses a different pattern (IStringLocalizer vs Phrases), follow the existing pattern.

## Core Rules

- NEVER use plain strings in gRPC responses, error messages, or user-facing output
- ALWAYS use `Phrases.{Key}` from resource files for all user-facing strings
- Default culture is set from project config
- Secondary languages go in `Phrases.{lang}.resx` (e.g., `Phrases.en.resx`)

## Microservice Mode

- Use `EntitiesLocalization` for entity display names
- `ThreadCultureInterceptor` handles culture switching via the `language` gRPC header
- Control panel uses `IStringLocalizer` for view localization

## Generic Mode

- Use `IStringLocalizer` or the `Phrases` pattern based on what the project already uses
- If neither exists and localization is requested, prefer `IStringLocalizer<T>`

## Detection Instructions

1. Check if the project has any `.resx` files or `IStringLocalizer` usage
2. If localization exists, follow the same pattern for all new code
3. If no localization exists, use plain strings unless explicitly asked to add localization
4. When adding new strings, always add them to the resource file -- never inline
