param(
    [switch]$Apply,
    [string]$Deployment = (Join-Path (Split-Path -Parent $PSScriptRoot) 'deployment.local.toml')
)
. (Join-Path $PSScriptRoot 'common.ps1')
if (-not $Apply) {
    Invoke-PackageTool plan --deployment $Deployment
    Write-Host 'Dry-run only. Re-run with -Apply after reviewing the plan.'
    exit 0
}
Invoke-PackageTool apply --deployment $Deployment
