# Provider Integration Guide

To add a CCR upstream target, supply these non-secret facts in
`deployment.local.toml`:

- CCR provider id/display name;
- local CCR endpoint and route id;
- upstream model selector;
- independently verified effective model identity;
- supported protocol;
- selected compatibility profile;
- the *name* of the local client-key environment variable.

Configure the upstream endpoint and credential directly in CCR outside this
repository. Never pass secret values as script arguments or write them to the
deployment file. Confirm that the route actually reaches a DeepSeek Flash-
compatible deployment; similar display names are not proof of identity.

Compatibility is selected by observed capability, not provider name. A new
provider needing the same tool-type policy reuses `deepseek_responses_v4`; a
different capability set receives a new versioned profile and fixtures.

See [provider-neutral example](providers/example-provider.md).
