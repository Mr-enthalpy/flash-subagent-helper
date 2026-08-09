param(
    [switch]$Apply,
    [switch]$AllowUnverifiedCcr,
    [string]$Deployment = (Join-Path (Split-Path -Parent $PSScriptRoot) 'deployment.local.toml')
)
. (Join-Path $PSScriptRoot 'common.ps1')
if (-not $Apply) {
    Invoke-PackageTool plan --deployment $Deployment
    Write-Host 'Dry-run only. Re-run with -Apply after reviewing the plan.'
    exit 0
}
$arguments = @('apply', '--deployment', $Deployment)
if ($AllowUnverifiedCcr) { $arguments += '--allow-unverified-ccr' }
Invoke-PackageTool @arguments
