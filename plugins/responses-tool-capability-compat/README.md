# Responses Tool Capability Compatibility

This provider-independent CCR plugin removes tool *types* declared unsupported
by a selected compatibility profile. It does not match named tools or vendors.

Installation is version-sensitive. The deployment package copies this directory
but intentionally does not edit CCR's internal runtime gateway configuration.
For the tested CCR Desktop 3.0.20 UI, open **Extensions → Install → Choose
folder** and select this plugin directory. `plugin.json` then resolves
`index.cjs`; do not select the module file directly. Verify gateway surface and
the `trusted-code` plus `core-gateway-config` permissions before enabling it.
The offline package contract loads
`plugin.json`, invokes `setup()`, follows the returned core-gateway registration,
and calls `transformRequest` with a mock Responses request. Passing that test
proves package shape, not live CCR activation. Confirm enablement in CCR Desktop;
use an explicitly authorized live smoke to confirm namespace compatibility.
