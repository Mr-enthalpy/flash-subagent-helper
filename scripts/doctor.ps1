param(
    [switch]$Live,
    [switch]$ConfirmCost,
    [string]$Deployment = (Join-Path (Split-Path -Parent $PSScriptRoot) 'deployment.local.toml')
)
. (Join-Path $PSScriptRoot 'common.ps1')
if ($Live -and -not $ConfirmCost) {
    throw 'Live mode may make a real API request and consume tokens. Add -ConfirmCost explicitly.'
}
$arguments = @('doctor', '--deployment', $Deployment)
if ($Live) { $arguments += '--live' }
if ($ConfirmCost) { $arguments += '--confirm-cost' }
Invoke-PackageTool @arguments
