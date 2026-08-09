. (Join-Path $PSScriptRoot 'common.ps1')
Invoke-PackageTool validate
& node --test (Join-Path $PackageRoot 'plugins\responses-tool-capability-compat\test\capability-compat.test.cjs')
if ($LASTEXITCODE -ne 0) { throw 'Compatibility tests failed.' }
