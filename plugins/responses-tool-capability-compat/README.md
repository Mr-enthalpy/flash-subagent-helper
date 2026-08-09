# Responses Tool Capability Compatibility

This provider-independent CCR plugin removes tool *types* declared unsupported
by a selected compatibility profile. It does not match named tools or vendors.

Installation is version-sensitive. The package detector must identify a known
CCR transformer or custom-router interface before registration. Unknown CCR
versions require an explicit compatibility override and manual review.
