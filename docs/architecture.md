# Architecture

The package separates five layers:

1. **Codex root/orchestrator** — explicitly preserved and never assigned the
   worker provider by this package.
2. **Agent pool** — seven role intents with sandbox and role-specific policy;
   provider/model fields are injected only by the renderer.
3. **CCR gateway** — local authentication and protocol adaptation.
4. **Compatibility profile** — capability-based Responses transformations,
   independent of vendor identity.
5. **Deployment target** — provider id, route selector, effective model identity,
   endpoint, and environment-variable name.

Repository configuration is publishable intent. `deployment.local.toml` is
non-secret but machine-local and ignored. Secret values are external. Generated
artifacts are deterministic and are installed with a revision manifest.

Ownership is narrow: seven `[agents.*]` tables, seven generated role files, one
worker model catalog, and one CCR plugin directory. Stable markers identify the
managed Codex block. Unmanaged same-name roles cause a conflict rather than an
overwrite.
