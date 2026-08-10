# Architecture

The package exposes four operational layers:

1. **Codex root/orchestrator** — explicitly preserved and never assigned the
   worker provider by this package.
2. **Agent pool** — seven role intents share a fixed package-owned Codex provider
   named `ccr_flash_worker`. Sandboxed-process network access and Codex web
   search are separately and explicitly disabled by the current profile.
3. **Versioned worker profile** — one tested Codex-native ModelInfo template plus
   the Responses tool-type policy. It stays deliberately close to upstream Codex.
4. **CCR gateway/deployment target** — owns the real route, upstream provider,
   provider credential, and effective model identity.

Repository configuration is publishable intent. `deployment.local.toml` is
non-secret but machine-local and ignored. Secret values are external. Generated
artifacts are deterministic and are installed with a revision manifest.

`policy/subagent-lifecycle.toml` is the provider-independent source for worker
lifecycle intent and degraded continuation semantics. The sanitized tested
baseline lives in `validation/subagent-runtime-capabilities.toml`. Both are
validated and deterministically rendered into audit artifacts. The 0.3.x
deployer still preserves root `developer_instructions`; changing that ownership
boundary requires a minor release and explicit migration contract.

Ownership is narrow: `[model_providers.ccr_flash_worker]`, seven `[agents.*]`
tables, seven generated role files, one worker model catalog, and one CCR plugin
directory. The plugin directory is copied for operator activation through CCR
Desktop Extensions; the package never edits CCR's internal runtime gateway
configuration. `package.toml` is the sole source for marker, roles, provider id,
profile id, activation policy, and plugin id. Unmanaged same-name objects cause
a conflict.

The persistent file model follows the rule of two: `roles/`, one
`profile/deepseek-flash-responses/`, one local deployment file, and one plugin.
It should split into registries only after a second materially different
model/protocol implementation exists.

Within a patch release series, the semantic managed target set is immutable.
Role/provider/plugin ownership changes require a minor version and explicit
lifecycle handling rather than an inferred migration.
