# Quickstart: Validate 023 Corpus Correctness and Delivery Foundation

Run from repository root.

## Standing Gates

```powershell
dotnet build dotnet-ai-kit.slnx -warnaserror
dotnet test dotnet-ai-kit.slnx
dotnet format dotnet-ai-kit.slnx --verify-no-changes
dotnet run --project src/DotnetAiKit.Cli -- generate --check
```

## Artifact Repair Checks

```powershell
# Run targeted artifact/content tests added by this feature.
dotnet test dotnet-ai-kit.slnx --filter "FullyQualifiedName~Artifact"
dotnet test dotnet-ai-kit.slnx --filter "FullyQualifiedName~MediatorPolicyRepair"
dotnet test dotnet-ai-kit.slnx --filter "FullyQualifiedName~V2ResidueRepair"

# Confirm generated output is updated only through projection.
dotnet run --project src/DotnetAiKit.Cli -- generate
dotnet run --project src/DotnetAiKit.Cli -- generate --check
```

## Cursor Delivery Check

```powershell
dotnet test dotnet-ai-kit.slnx --filter "FullyQualifiedName~Cursor"
Test-Path build\cursor\.cursor-plugin\plugin.json
Test-Path build\cursor\agents
```

## Manifest Integrity Check

```powershell
dotnet test dotnet-ai-kit.slnx --filter "FullyQualifiedName~Check"
```

Expected behavior:

- Valid manifest passes.
- Missing manifest fails clearly.
- Tampered manifest fails manifest integrity.

## Review Phase Checklist

Before final polish:

- Review changed authored artifacts under `artifacts/`.
- Review changed source under `src/`.
- Review generated output only to confirm it reflects authored/projector changes.
- Confirm MediatR policy is consistent in touched files.
- Confirm no contradictory v1/Python CLI residue remains in touched files.
- Run all standing gates.
