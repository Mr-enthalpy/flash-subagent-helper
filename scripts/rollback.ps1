param([string]$Deployment = (Join-Path (Split-Path -Parent $PSScriptRoot) 'deployment.local.toml'))
. (Join-Path $PSScriptRoot 'common.ps1')
Invoke-PackageTool rollback --deployment $Deployment
