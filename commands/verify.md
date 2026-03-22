---
description: "Run build, test, and format verification pipeline per affected repo"
---

# /dotnet-ai.verify — Verification Pipeline

You are an AI coding assistant executing the `/dotnet-ai.verify` command.
Your job is to run a verification pipeline and report PASS/FAIL/WARN per check.

## Input

Flags: `--dry-run` (preview checks without running), `--verbose` (diagnostic output),
       `--skip-tests` (skip test suite, run build + format only)

## Step 1: Identify Affected Repos

1. Find the active feature in `.dotnet-ai-kit/features/`.
2. Detect mode: **generic** or **microservice**.
3. Identify repos to verify:
   - Generic: current directory (single repo).
   - Microservice: each repo from `service-map.md` or config.
4. For each repo, verify the feature branch exists: `feature/{NNN}-{short-name}`.
5. If `--verbose`, print: "Verifying {N} repos."

## Step 2: Load Skills

- Read `skills/quality/architectural-fitness/SKILL.md` for quality checks
- If proto files detected: `skills/microservice/grpc/service-definition/SKILL.md`
- If K8s files detected: `skills/devops/kubernetes/SKILL.md`

## Step 3: Run Verification Checks (per repo)

For each affected repo, run the following checks in order:

### Check 1: Build (always)

```bash
dotnet build --no-restore --configuration Release
```

- PASS: exit code 0, no errors
- FAIL: compilation errors (report error messages)
- WARN: compilation warnings (report count)

If build fails, stop remaining checks for this repo (tests cannot run).

### Check 2: Tests (unless --skip-tests)

```bash
dotnet test --no-build --configuration Release --logger "console;verbosity=minimal"
```

- PASS: all tests pass
- FAIL: any test fails (report failing test names and messages)
- WARN: no test projects found (not necessarily an error)

### Check 3: Resource Check (mode-adaptive)

**Only runs if**: project contains `Phrases.resx` or similar resource files.

Detection: scan for `*.resx` files in the project.

Checks:
- All resource keys in `Phrases.resx` have corresponding entries in `Phrases.en.resx`
- No orphaned resource keys (keys in code but missing from resx)
- Resource keys referenced in code actually exist in the resx files

- PASS: all resources consistent
- FAIL: missing translations or orphaned keys
- WARN: unable to verify (complex references)

### Check 4: Proto Check (mode-adaptive)

**Only runs if**: `.proto` files exist in the project or contracts/ directory.

Detection: scan for `*.proto` files.

Checks:
- Proto files compile without errors
- Request/Response messages are consistent between client and server protos
- Microservice mode: client proto in gateway matches server proto in service repo

- PASS: all protos consistent
- FAIL: proto compilation errors or mismatches
- WARN: unable to cross-reference (missing partner repo)

### Check 5: K8s Check (mode-adaptive)

**Only runs if**: Kubernetes manifest files exist (`*.yaml` or `*.yml` in a k8s/ or deploy/ directory).

Detection: scan for K8s-style YAML files with `kind:` and `apiVersion:` fields.

Checks:
- All environment variables referenced in code have entries in K8s manifests
- ConfigMap and Secret references resolve
- Service names match between manifests and application config

- PASS: all env vars and configs present
- FAIL: missing env vars or broken references
- WARN: unable to fully verify (complex templating like Helm)

### Check 6: Format Check (always)

```bash
dotnet format --verify-no-changes --verbosity minimal
```

Uses the project's `.editorconfig` if present.

- PASS: no formatting issues
- FAIL: formatting violations found (report file count)
- WARN: no .editorconfig found (using defaults)

## Step 4: Compile Results

Save results to `verify.md` in the feature directory:

```markdown
# Verification Report: {Feature Name}

**Feature**: {NNN}-{short-name} | **Date**: {DATE}

## Results

| Repo | Build | Tests | Resources | Proto | K8s | Format | Overall |
|------|-------|-------|-----------|-------|-----|--------|---------|
| {repo} | PASS | PASS | SKIP | SKIP | SKIP | PASS | PASS |
| {repo2} | PASS | FAIL | PASS | PASS | WARN | PASS | FAIL |

## Details

### {Repo Name}
- **Build**: PASS (0 errors, 3 warnings)
- **Tests**: PASS (42 passed, 0 failed)
- **Resources**: SKIP (no resx files detected)
- **Proto**: SKIP (no proto files detected)
- **K8s**: SKIP (no manifests detected)
- **Format**: PASS (no violations)

### {Repo2 Name}
- **Build**: PASS
- **Tests**: FAIL
  - `OrderTests.CreateOrder_ShouldSucceed`: Expected 200, got 400
- ...
```

## Step 5: Report to User

```
Verification complete for {NNN}-{short-name}.

  {Repo}:  Build PASS | Tests PASS | Format PASS  → PASS
  {Repo2}: Build PASS | Tests FAIL | Format PASS  → FAIL

Overall: {PASS|FAIL}

{If FAIL}:
  Fix failing checks and re-run /dotnet-ai.verify
  Or: /dotnet-ai.implement --resume (to fix and rebuild)

{If PASS}:
  All checks passed. Ready for PR.
  Next: /dotnet-ai.pr
```

## Dry-Run Behavior

When `--dry-run` is active:
- Print which repos WOULD be verified
- Print which checks WOULD run (based on file detection)
- Show checks that would be SKIPPED and why
- Do NOT execute any commands (build, test, format)
- Prefix output with `[DRY-RUN]`

## Error Handling

- dotnet SDK not found: "dotnet SDK required. Install from https://dot.net"
- No feature branch: "No feature branch found. Run /dotnet-ai.implement first."
- Build timeout: report FAIL with timeout info
- Repo not accessible: SKIP that repo, report reason
