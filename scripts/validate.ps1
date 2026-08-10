. (Join-Path $PSScriptRoot 'common.ps1')
Invoke-PackageTool validate
& node --test (Join-Path $PackageRoot 'plugins\responses-tool-capability-compat\test\capability-compat.test.cjs')
if ($LASTEXITCODE -ne 0) { throw 'Compatibility tests failed.' }
& python (Join-Path $PackageRoot 'tests\deployment-lifecycle.test.py')
if ($LASTEXITCODE -ne 0) { throw 'Deployment lifecycle tests failed.' }
& python (Join-Path $PackageRoot 'tests\external-worker-transport.test.py')
if ($LASTEXITCODE -ne 0) { throw 'External worker transport contract tests failed.' }
