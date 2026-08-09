# Responses Tool Capability Compatibility

This provider-independent CCR plugin removes tool *types* declared unsupported
by a selected compatibility profile. It does not match named tools or vendors.

Installation is version-sensitive. The package currently supports one explicit
adapter, `gateway_plugin_v1`. Before registration it parses `plugins[]`, loads
the actual module, invokes `providerPlugins.transformRequest` with a mock final
Responses request, and verifies the transformed result. Version strings are
audit evidence only; a failed contract cannot be overridden.
