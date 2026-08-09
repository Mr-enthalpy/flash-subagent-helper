# Architecture

The package exposes four operational layers:

1. **Codex root/orchestrator** — explicitly preserved and never assigned the
   worker provider by this package.
2. **Agent pool** — seven role intents share a fixed package-owned Codex provider
   named `ccr_flash_worker`. Workspace-write networking is explicitly denied in
   the current Codex-native sandbox table.
3. **Versioned worker profile** — one tested Codex-native ModelInfo template plus
   the Responses tool-type policy. It stays deliberately close to upstream Codex.
4. **CCR gateway/deployment target** — owns the real route, upstream provider,
   provider credential, and effective model identity.

Repository configuration is publishable intent. `deployment.local.toml` is
non-secret but machine-local and ignored. Secret values are external. Generated
artifacts are deterministic and are installed with a revision manifest.

Ownership is narrow: `[model_providers.ccr_flash_worker]`, seven `[agents.*]`
tables, seven generated role files, one worker model catalog, and one CCR plugin
directory. `package.toml` is the sole source for marker, roles, provider id, and
plugin id. Unmanaged same-name objects cause a conflict.

The persistent file model follows the rule of two: `roles/`, one
`profile/deepseek-flash-responses/`, one local deployment file, and one plugin.
It should split into registries only after a second materially different
model/protocol implementation exists.
