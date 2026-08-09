# Provider Integration Guide

To add a CCR upstream target, supply only these non-secret facts in
`deployment.local.toml`:

- local CCR endpoint;
- CCR model selector;
- optionally, an independently verified effective model identity;
- the *name* of the local client-key environment variable.

Configure the upstream endpoint and credential directly in CCR outside this
repository. Never pass secret values as script arguments or write them to the
deployment file. Confirm that the route actually reaches a DeepSeek Flash-
compatible deployment; similar display names are not proof of identity.

Codex always uses `model_providers.ccr_flash_worker`; an upstream provider id is
never a Codex deployment input. Compatibility is selected by observed behavior,
not provider name. A new provider requires no core change when its CCR route
satisfies `deepseek-flash-responses`. A materially different capability set
should first be proven with fixtures; only then is a second profile justified.

See [provider-neutral example](providers/example-provider.md).
