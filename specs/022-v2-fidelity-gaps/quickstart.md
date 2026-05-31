# Quickstart — validate the v2 fidelity-gap feature

End-to-end validation once the phases land. All commands from repo root; all must stay green.

## Baseline gates (every phase)

```bash
dotnet build dotnet-ai-kit.slnx -warnaserror -c Release      # 0/0
dotnet test  dotnet-ai-kit.slnx -c Release                   # all green
dotnet format dotnet-ai-kit.slnx --verify-no-changes         # clean
dotnet run --project src/DotnetAiKit.Cli -- generate --check  # drift-clean
```

## F1 — hooks runnable (US2)

```bash
# the generated command must run the v2 backend, not the v1 shim
echo '{"tool_input":{"file_path":"src/obj/x.g.cs"}}' | dotnet-ai hook pretooluse   # → deny JSON
echo '{"stop_hook_active":true}' | dotnet-ai hook stop                             # → empty (allow)
# init/check warns if a shadowing shim is on PATH:
dotnet run --project src/DotnetAiKit.Cli -- check        # warns on a non-v2 dotnet-ai
```
Acceptance smoke executes the *generated* `hooks.json` command string (not a hand-built one).

## F2 — skill resources (US1)

```bash
# resources present where required:
ls artifacts/skills/commands/constitution/scripts/        # non-empty
ls artifacts/skills/commands/add-aggregate/examples/      # compilable C#
dotnet run --project src/DotnetAiKit.Cli -- generate
ls build/claude/skills/add-aggregate/examples/            # copied into the host tree
dotnet run --project src/DotnetAiKit.Cli -- generate --check   # drift-clean with resources present
```
Corpus-integrity test asserts the required-set per skill-kind.

## F3 — goldens (US4)

```bash
dotnet test --filter "FullyQualifiedName~Hosts.Tests"     # Verify goldens green
# induce a projector format change → the matching *.verified.* test fails (independent of drift gate)
```

## F4 — eval matrix (US3)

```bash
ls artifacts/skills/cqrs/*/evals/cases.jsonl
dotnet test --filter "FullyQualifiedName~Triggering"      # confusion matrix passes
# induce a description collision → a case fails
```

## F5 — user-file policy (US5)

```bash
mkdir -p /tmp/sol/.claude && echo '{"hooks":{"X":1},"my":"edit"}' > /tmp/sol/.claude/settings.json
dotnet run --project src/DotnetAiKit.Cli -- init /tmp/sol
cat /tmp/sol/.claude/settings.json    # "my":"edit" preserved (merged or backed up), reported in init output
```

## F6 — install smoke (US7)

```bash
claude plugin validate build/claude --strict   # Validation passed
claude plugin validate build --strict           # Validation passed (marketplace)
# (acceptance smoke skips gracefully if the claude CLI is absent)
```

## F7/F8 — channels + parity

```bash
ls build/claude/output-styles/ 2>/dev/null      # forced-output-style artifact (F7)
ls artifacts/skills/microservice/controlpanel/blazor-hybrid/SKILL.md   # parity (F8) or a recorded de-scope in planning/23
# SchemaVersion guard: an artifact with an out-of-range schema version fails load with guidance
```

## Done when

All of [spec.md](spec.md) SC-022-1…7 pass, the four host outputs stay drift-clean, and `claude plugin validate --strict` passes for plugin + marketplace.
