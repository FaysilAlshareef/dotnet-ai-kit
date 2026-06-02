# Quickstart: Validating Profile, Rule, and Dynamic Delivery

How to verify this feature end-to-end. Run from the repo root on the `024-v2-profile-rule-and-dynamic-delivery` branch.

## Standing gates (must all pass)

```bash
dotnet build dotnet-ai-kit.slnx -warnaserror
dotnet test  dotnet-ai-kit.slnx
dotnet format dotnet-ai-kit.slnx --verify-no-changes
dotnet run --project src/DotnetAiKit.Cli -- generate --check --out build/
```

## Feature-specific checks

1. **Profile delivery (Claude always-on, single-select)**
   ```bash
   dotnet test dotnet-ai-kit.slnx --filter "FullyQualifiedName~ProfileDelivery"
   ```
   Confirms: `init` writes `.claude/profiles/<arch>.md` (only the resolved arch), the PreToolUse hook injects it always-on, the output-style references the delivered profile, and unknown/absent architecture → `generic`.

2. **Rule/profile dedup + glob coherence**
   ```bash
   dotnet test dotnet-ai-kit.slnx --filter "FullyQualifiedName~RuleProfileCoherence"
   ```
   Confirms: no profile restates a universal rule; the three globs are narrowed; `error-handling`/`performance` stay broad; `deterministic-enforcement` is universal; testing-rule residue is absent.

3. **MCP/LSP projection + determinism**
   ```bash
   dotnet test dotnet-ai-kit.slnx --filter "FullyQualifiedName~McpLspProjection"
   ```
   Confirms: each host gets MCP config from the one descriptor; LSP present for Claude/Copilot and explicitly marked unsupported for Codex/Cursor; nav agents prefer symbol-precise navigation; files are byte-stable.

4. **Drift + golden**
   ```bash
   dotnet run --project src/DotnetAiKit.Cli -- generate --out build/
   dotnet run --project src/DotnetAiKit.Cli -- generate --check --out build/   # expect: no drift
   ```
   Re-accept the `Hosts.Tests` Verify golden when projection shape changes (new profile/MCP/LSP files), then re-run.

5. **Manual smoke (optional) — profile actually reaches an initialized solution**
   ```bash
   # In a scratch .NET solution dir, after `dotnet-ai init` with architecture: clean-arch
   #   .claude/profiles/clean-arch.md exists and contains clean-arch (deduped) guidance
   #   echo a PreToolUse event to `dotnet-ai hook pretooluse` → additionalContext includes the profile body
   ```

## Review & Verification (per FR-021/022, before final polish)

- Profile content reaches initialized/projected host outputs (US1/US3 tests green).
- No duplicate profile/rule injection (dedup check green).
- Generated MCP/LSP files deterministic + `build/` drift-clean.
- All standing gates pass.
