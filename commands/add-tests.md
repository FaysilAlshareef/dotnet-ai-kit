---
description: "Generates test suite for existing code. Use when adding unit or integration tests to untested code."
---

# Add Tests

Scan existing code for classes, handlers, and controllers without test files and generate missing tests. Detects the test framework, mocking library, and follows existing test patterns.

## Usage

```
/dotnet-ai.add-tests $ARGUMENTS
```

**Examples:**
- (no args) -- Scan entire project, generate all missing tests
- `OrderService` -- Generate tests for a specific class
- `--handlers` -- Generate tests for all MediatR handlers
- `--coverage 80` -- Generate tests until estimated 80% coverage
- `--dry-run` -- Show what tests would be generated
- `--list` -- Show file list only
- `--verbose` -- Show scanning and detection details

## Flags

| Flag | Description |
|------|-------------|
| `--handlers` | Target all MediatR/CQRS handlers only |
| `--controllers` | Target all controllers only |
| `--services` | Target all service classes only |
| `--coverage {N}` | Generate tests targeting N% coverage estimate |
| `--dry-run` | Display generated test code without writing |
| `--list` | List test files that would be created with descriptions, no code output |
| `--verbose` | Show scanning progress, pattern detection, coverage estimates |
| `--no-build` | Skip post-generation build and test run |

## Pre-Generation

1. **Detect test project** -- find the test project (`.csproj` with test SDK reference).
   - If no test project exists: report and suggest creating one.
2. **Detect test framework** -- scan test project for:
   - **xUnit**: `[Fact]`, `[Theory]`, `Xunit` namespace
   - **NUnit**: `[Test]`, `[TestCase]`, `NUnit.Framework`
   - **MSTest**: `[TestMethod]`, `[TestClass]`, `Microsoft.VisualStudio.TestTools`
3. **Detect mocking library** -- scan for:
   - **Moq**: `Mock<T>`, `Moq` namespace
   - **NSubstitute**: `Substitute.For<T>`, `NSubstitute` namespace
   - **FakeItEasy**: `A.Fake<T>`, `FakeItEasy` namespace
4. **Learn test patterns** -- scan existing tests for:
   - Naming convention (`{Class}Tests`, `{Class}Should`, `When{Action}_{Result}`)
   - File location pattern (mirror source structure or flat)
   - Arrange/Act/Assert style, fixture usage, builder patterns
   - Existing fakers (`CustomConstructorFaker`, Bogus `Faker<T>`)
5. **Scan for untested code** -- compare source classes to test classes:
   - Handlers without `{Handler}Tests.cs`
   - Controllers without `{Controller}Tests.cs`
   - Services without `{Service}Tests.cs`
   - Apply targeting filter (`--handlers`, `--controllers`, specific class name)
6. **Skip control panel projects** -- no tests required for Blazor UI.

## Load Specialist Agent

Read `agents/test-engineer.md` for testing patterns. Also read the project's primary architect agent for architecture context:
- **Microservice mode**:
  - command → Read `agents/command-architect.md`
  - query-sql → Read `agents/query-architect.md`
  - query-cosmos → Read `agents/cosmos-architect.md`
  - processor → Read `agents/processor-architect.md`
  - gateway → Read `agents/gateway-architect.md`
  - controlpanel → Read `agents/controlpanel-architect.md`
  - hybrid → Read both `agents/command-architect.md` and `agents/query-architect.md`
- **Generic mode** (VSA, Clean Arch, DDD, Modular Monolith):
  - Read `agents/dotnet-architect.md`

Load all skills listed in each loaded agent's Skills Loaded section.

## Skills to Read

- `skills/testing/unit-testing` -- unit test structure, assertions, mocking patterns
- `skills/testing/integration-testing` -- integration test setup, WebApplicationFactory
- `skills/testing/test-fixtures` -- shared fixtures, test data builders, fakers

## Generation Flow

### Step 1: Build Test Plan
- List all untested classes with their type (handler, controller, service, validator)
- If `--coverage {N}` specified: prioritize by impact (handlers first, then services, then controllers)
- Show plan: "Found {X} untested classes. Will generate {Y} test files."

### Step 2: Generate Unit Tests (per untested class)

**For Handlers:**
- Test file: `Test/Commands/{Handler}Tests.cs` or matching existing structure
- Test cases: success path, validation failure, not-found scenario, concurrency conflict
- Mock dependencies using detected mocking library
- Use existing fakers/builders if available

**For Controllers/Endpoints:**
- Test file: `Test/Controllers/{Controller}Tests.cs`
- Test each action method: success, bad request, not found, unauthorized
- Mock handler/service dependencies

**For Services:**
- Test file: `Test/Services/{Service}Tests.cs`
- Test public methods with success and error cases
- Mock external dependencies

**For Validators:**
- Test file: `Test/Validators/{Validator}Tests.cs`
- Test valid input passes, each validation rule triggers on invalid input

### Step 3: Generate Integration Tests (if pattern exists)
- Only if existing integration tests are found in the project
- Test file: `Test/Integration/{Feature}IntegrationTests.cs`
- Use `WebApplicationFactory` or custom test server pattern from existing tests

### Step 4: Generate Supporting Files
- Faker classes for new entities if Bogus/faker pattern detected
- Assertion extensions if custom assertion pattern detected
- Test fixtures if shared fixture pattern detected

## Post-Generation

1. **Run `dotnet build`** on test project -- verify compilation.
2. **Run `dotnet test`** -- verify generated tests pass.
3. **Report:**
   ```
   Generated {N} test files with {M} test methods.
   - Handlers: {X} tested
   - Controllers: {Y} tested
   - Services: {Z} tested
   All tests passing.
   ```

## Preview / Dry-Run Behavior

- `--dry-run`: Show generated test code with file headers. No writes.
- `--list`: List test files that would be created with class counts. No code, no writes.
