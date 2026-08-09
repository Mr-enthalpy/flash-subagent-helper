# Deployment

## New machine

1. Install and authenticate official Codex.
2. Install CCR and configure the upstream provider credential in CCR.
3. Create an independent local CCR client credential and place it in an
   environment variable or credential store.
4. Run `bootstrap.ps1` to collect non-secret parameters.
5. Run offline doctor and deployment dry-run.
6. Review `DEPLOYMENT PLAN`, then run `deploy.ps1 -Apply`.
7. Run `validate.ps1`, fully restart Codex, and optionally run paid live doctor.

## Existing machine

The deployer parses and inspects the existing Codex configuration. It removes
only its previous marked block and appends the newly rendered block. It aborts
if any managed role name is present outside that block. Root model/provider,
auth, MCP, other agents/tools, and unrelated instructions are preserved.

## Plan and compatibility states

`deploy.ps1` is dry-run by default. `-Apply` writes only after backup. An unknown
CCR version reports `UNVERIFIED CCR VERSION` and aborts unless the user adds
`-AllowUnverifiedCcr` after manually validating the hook. `INCOMPATIBLE` must
never be overridden.

Revision manifests record paths, backup paths, package version, timestamp, and
artifact hashes—not secret values. Rollback restores only the preceding package
revision. Uninstall removes only unchanged package-owned artifacts and its
marked block; it never runs Git reset/clean or deletes unknown configuration.
