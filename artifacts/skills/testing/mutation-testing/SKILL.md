---
name: mutation-testing
description: "Configures Stryker.NET mutation testing to score how effectively a suite kills injected faults, and enforces a minimum mutation score as a CI gate. Use when line/branch coverage looks high but you need to prove the assertions actually detect regressions. Do NOT use for writing the tests being measured (use unit-testing) or for measuring runtime latency/throughput (use performance-testing)."
metadata:
  category: "testing"
  agent: "test-engineer"
---
# Stryker.NET Mutation Testing

## Core Principles

- Coverage measures *executed* lines; **mutation score** measures *asserted* behaviour. A surviving mutant is a fault your tests did not catch.
- Stryker mutates the code under test (negate conditionals, swap operators, empty method bodies), re-runs the suite, and reports each mutant as Killed, Survived, No Coverage, or Timeout.
- Score = killed / (killed + survived + no-coverage). Set a `break` threshold so CI fails below it.
- Scope each run to one project (`Stryker.csproj` target) and exclude generated/migration code to keep runs fast and signal high.
- Run on changed projects in PRs (incremental via `--since`); run the full suite nightly — full mutation runs are slow.

## Setup

```bash
dotnet tool install -g dotnet-stryker
# From the test project's directory:
dotnet stryker
```

```json
// stryker-config.json (next to the test project)
{
  "stryker-config": {
    "project": "MyApp.Domain.csproj",
    "test-projects": ["../MyApp.Domain.Tests/MyApp.Domain.Tests.csproj"],
    "reporters": ["html", "progress", "cleartext"],
    "thresholds": { "high": 85, "low": 70, "break": 70 },
    "mutate": [
      "!**/Migrations/**.cs",
      "!**/*.g.cs"
    ],
    "since": { "target": "origin/master" }
  }
}
```

```yaml
# CI gate (GitHub Actions) — non-zero exit when score < break threshold
- name: Mutation testing
  run: |
    dotnet tool restore
    dotnet stryker --reporter cleartext --reporter html
  # Stryker exits non-zero automatically when below "break"; the step fails.
```

## Reading & Acting on Results

- Triage **Survived** mutants first: each one names a behaviour no test asserts — add or strengthen an assertion.
- **No Coverage** means the line is never exercised — that is a coverage gap, fix with a new test, not by raising the threshold.
- Mark genuinely-equivalent mutants (semantically identical to the original) ignored via `// Stryker disable` comments rather than weakening the threshold.

## Gotchas

- A flaky test inflates Timeout/Survived counts — stabilise the suite before trusting the score.
- Mutating I/O-heavy or integration code yields long, noisy runs; mutate domain/logic projects where assertions are dense.
- Raise the `break` threshold gradually as you kill mutants; starting at 80%+ on a legacy suite just blocks every PR.

## References

- https://stryker-mutator.io/docs/stryker-net/introduction/
- https://stryker-mutator.io/docs/stryker-net/configuration/
