---
alwaysApply: true
description: Enforces test naming, structure, and isolation patterns for both .NET and Python tests.
---

# Testing Rules

Detect the project language and test framework before applying rules.
Match the existing test style. Never introduce a different test framework.

## Naming Convention

- .NET test methods: `{Method}_{Scenario}_{ExpectedResult}`
  - Example: `CreateOrder_WithValidData_ReturnsSuccess`
  - Example: `Handle_WhenEntityNotFound_ReturnsFalse`
  - Example: `Apply_DuplicateEvent_ThrowsConcurrencyException`
- Python test functions: `test_{scenario}_{expected}` (snake_case)

## Structure

- Use **Arrange-Act-Assert** with clear visual separation
- Each section should be identifiable without comments (blank line between sections)
- One logical assertion per test (multiple `Assert` calls are fine if testing one concept)

## .NET Test Patterns

### Aggregate Testing (Event-Sourced)
1. Create aggregate via constructor or factory method
2. Call the domain method under test
3. Verify the correct event was raised with expected data

### Event Handler Testing (Query Side)
1. Create the entity in its expected pre-state
2. Create an event with the relevant data
3. Call the handler's `Handle` method
4. Verify the entity's state was updated correctly

### EF Core / Database Tests
- Use `InMemoryDbContext` or test fixtures with isolated databases
- Never share database state between tests
- Clean up or use unique IDs to avoid cross-test interference

## Python Test Patterns

- Use `tmp_path` fixture for all filesystem tests
- Use `tempfile` module — never hardcode `/tmp` or `%TEMP%`
- Mock external calls (`subprocess`, network) — never hit real services
- Each test file should have 5-10 focused test functions

## MUST NOT

- Do not call real services (HTTP, gRPC, Service Bus, database servers) in unit tests
- Do not share mutable state between tests
- Do not test implementation details — test behavior
- Do not use `Thread.Sleep` or `Task.Delay` in tests — use async patterns
- Do not write tests that depend on execution order

## Detection Instructions

1. Check for existing test projects and their naming patterns
2. Identify the test framework (xUnit, NUnit, MSTest, pytest)
3. Look for existing test utilities (Fakers, Asserts, Fixtures)
4. Follow the established patterns for all new tests

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A CORRESPONDING TEST
```

New public methods, handlers, and services require tests. If you wrote code without a test, write the test now.

## Rationalization Table

| Excuse | Reality |
|--------|---------|
| "It's too simple to test" | Simple code breaks. A test takes 30 seconds to write. |
| "I'll write tests later" | Later never comes. Write it now. |
| "The build passes" | Build checks compilation, not correctness. |
| "It's just a DTO/model" | DTOs with logic (validation, computed properties) need tests. |
| "Manual testing is enough" | Manual testing can't be re-run. Automated tests can. |
| "The handler just calls a service" | Test the handler. Services change. Integration matters. |
| "Test setup is too complex" | Complex setup = complex code. Simplify the design. |
| "Existing code has no tests" | You're improving the codebase. Add tests for what you change. |

## Related Skills
- `skills/core/fluent-validation/SKILL.md` — validation testing patterns
