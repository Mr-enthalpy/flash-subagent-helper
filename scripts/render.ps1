param(
    [string]$Deployment = (Join-Path (Split-Path -Parent $PSScriptRoot) 'deployment.local.toml'),
    [string]$Output = (Join-Path (Split-Path -Parent $PSScriptRoot) 'out')
)
. (Join-Path $PSScriptRoot 'common.ps1')
Invoke-PackageTool render --deployment $Deployment --output $Output
