#!/usr/bin/env pwsh
# Claude PreToolUse hook (Windows parity, FR-040). Injects matching .claude/rules bodies as additionalContext.
$ErrorActionPreference = 'Stop'

$raw = [Console]::In.ReadToEnd()
try { $event = $raw | ConvertFrom-Json } catch { exit 0 }
$filePath = $event.tool_input.file_path
$rulesDir = Join-Path (Get-Location) '.claude/rules'
if (-not $filePath -or -not (Test-Path $rulesDir)) { exit 0 }

$rel = $filePath -replace '\\', '/'
$parts = New-Object System.Collections.Generic.List[string]

foreach ($rule in Get-ChildItem -Path $rulesDir -Filter '*.md' | Sort-Object Name) {
    $text = Get-Content -LiteralPath $rule.FullName -Raw -Encoding utf8
    if ($text -notmatch '(?s)^---\r?\n(.*?)\r?\n---\r?\n(.*)$') { continue }
    $frontmatter = $Matches[1]; $body = $Matches[2].Trim()
    $globs = [regex]::Matches($frontmatter, '-\s*"([^"]+)"') | ForEach-Object { $_.Groups[1].Value }
    $apply = $false
    if (-not $globs) { $apply = $true }
    else {
        foreach ($g in $globs) {
            $pattern = '^' + [regex]::Escape($g).Replace('\*\*/', '.*').Replace('\*\*', '.*').Replace('\*', '[^/]*') + '$'
            if ($rel -match $pattern) { $apply = $true; break }
        }
    }
    if ($apply) { $parts.Add($body) }
}

if ($parts.Count -gt 0) {
    @{ hookSpecificOutput = @{ hookEventName = 'PreToolUse'; additionalContext = ($parts -join "`n`n") } } | ConvertTo-Json -Depth 5 -Compress
}
exit 0
