<#
.SYNOPSIS
  PowerShell wrapper around scripts/check.py (T004 / FR-038).
.DESCRIPTION
  Forwards all arguments to the Python entry point. Exits with pytest's exit
  code so it can be used as a pre-commit hook on Windows.
#>
$python = if ($env:DOTNET_AI_PYTHON) { $env:DOTNET_AI_PYTHON } else { "python" }
$here = Split-Path -Parent $MyInvocation.MyCommand.Definition
& $python (Join-Path $here "check.py") @args
exit $LASTEXITCODE
