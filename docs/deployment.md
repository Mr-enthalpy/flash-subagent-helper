# Deployment

## New machine

1. Install and authenticate official Codex.
2. Install CCR and configure the upstream provider credential in CCR.
3. Create an independent local CCR client credential and place it in an
   environment variable or credential store.
4. Run `bootstrap.ps1` to collect non-secret parameters.
5. Run offline doctor and deployment dry-run.
6. Review `DEPLOYMENT PLAN`, then run `deploy.ps1 -Apply`.
7. In CCR Desktop Extensions, install/enable the copied
   `responses-tool-capability-compat` directory.
8. Run `validate.ps1`, fully restart Codex and CCR, and optionally run paid live
   doctor.

## Existing machine

The deployer parses and inspects the existing Codex configuration. It removes
only its previous marked block and appends the newly rendered block. It aborts
if any managed role name is present outside that block. Root model/provider,
auth, MCP, other agents/tools, and unrelated instructions are preserved.

## Plan and compatibility states

`deploy.ps1` is dry-run by default. `-Apply` writes only after all structural
preflight checks and the packaged extension contract pass. That probe loads the
manifest module, calls `setup()`, follows its core-gateway registration, and
exercises `transformRequest` with a provider-neutral request. It does **not**
claim that the installed CCR has activated the extension. Offline status is
therefore `MANUAL_ACTIVATION_REQUIRED`, not `VERIFIED`.

The only deployment choices are the CCR local URL, the environment-variable
name containing its local client key, the CCR model selector, and optionally an
operator-verified effective model identity. `ccr_flash_worker`, the profile,
and manual activation policy are package-controlled. The renderer rejects non-loopback
gateway URLs so a CCR local client credential cannot be sent to a remote host.

Revision manifests record paths, backup paths, package version, timestamp, and
artifact hashes—not secret values. A converged apply is a NOOP and creates no
revision. Rollback restores only the preceding package revision. Uninstall
restores the first-install baseline and removes only unchanged package-owned
artifacts and its marked block; it never runs Git reset/clean or deletes unknown
configuration.

## 0.2 to 0.3 lifecycle boundary

Version 0.2 managed an internal CCR runtime file; 0.3 deliberately does not.
The 0.3 deployer refuses an in-place 0.2 lifecycle upgrade. Use the original
0.2 checkout to uninstall its deployment, confirm CCR runtime configuration is
restored, then deploy 0.3 and enable the extension through CCR Desktop.
