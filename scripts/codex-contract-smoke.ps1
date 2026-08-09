param([string]$Deployment = (Join-Path (Split-Path -Parent $PSScriptRoot) 'tests\fixtures\deployment.test.toml'))
. (Join-Path $PSScriptRoot 'common.ps1')
Invoke-PackageTool codex-contract --deployment $Deployment
