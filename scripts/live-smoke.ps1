param(
    [switch]$ConfirmCost,
    [string]$Deployment = (Join-Path (Split-Path -Parent $PSScriptRoot) 'deployment.local.toml')
)
. (Join-Path $PSScriptRoot 'common.ps1')
if (-not $ConfirmCost) {
    throw 'LIVE smoke may make real API requests and consume tokens. Add -ConfirmCost explicitly.'
}
Write-Host 'Phase 1: minimal live Responses compatibility request'
Invoke-PackageTool doctor --deployment $Deployment --live --confirm-cost
Write-Host 'Phase 2 requires a new Codex session and typed-worker mailbox orchestration.'
Write-Host 'Follow docs/testing.md: read-only worker, isolated write, Guardian, receipt, fresh audit, cleanup.'
