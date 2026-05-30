#!/usr/bin/env pwsh
# Claude Stop/SubagentStop hook (Windows parity, FR-040). Blocks completion until build + tests are green.
$ErrorActionPreference = 'Stop'

function Block($reason) {
    @{ decision = 'block'; reason = $reason } | ConvertTo-Json -Compress
    exit 0
}

& dotnet build --nologo | Out-Null
if ($LASTEXITCODE -ne 0) { Block 'dotnet build failed - fix the build before completing.' }

& dotnet test --nologo | Out-Null
if ($LASTEXITCODE -ne 0) { Block 'dotnet test failed - fix the failing tests before completing.' }

exit 0
