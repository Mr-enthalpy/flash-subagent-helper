Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PackageRoot = Split-Path -Parent $PSScriptRoot
$PackageTool = Join-Path $PSScriptRoot 'package_tool.py'

function Invoke-PackageTool {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    & python $PackageTool @Arguments
    if ($LASTEXITCODE -ne 0) { throw "package_tool.py failed with exit code $LASTEXITCODE" }
}
