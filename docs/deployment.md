# Deployment

## New machine

1. Install and authenticate official Codex.
2. Install CCR and configure the upstream provider credential in CCR.
3. Create an independent local CCR client credential and place it in an
   environment variable or credential store.
4. Run `bootstrap.ps1` to collect non-secret parameters.
5. Run offline doctor and deployment dry-run.
6. Review `DEPLOYMENT PLAN`, then run `deploy.ps1 -Apply`.
7. Install and enable the copied extension using the version-sensitive procedure
   below.
8. Install the external DeepSeek TASK mailbox script under `CODEX_HOME/scripts`
   and register its command for the typed roles in `CODEX_HOME/hooks.json`.
   Package 0.4.x diagnoses but does not own these two operator-managed files.
9. Run offline doctor and require script present, hook registered, packet
   validator PASS, and queue EMPTY.
10. Run `validate.ps1`, fully restart Codex and CCR, and optionally run paid live
    doctor plus the mailbox transport smoke.

## Existing machine

The deployer parses and inspects the existing Codex configuration. It replaces
only its previous marked TOML block and its marked root-policy block inside the
top-level `developer_instructions` string. It aborts if any managed role name is
present outside the TOML block, or if the root string uses syntax that cannot be
located and rewritten safely. Root model/provider, auth, MCP, other agents/tools,
and operator-owned root instructions are preserved.

`hooks.json` and the external mailbox script are preserved as operator-managed
dependencies. The deployment plan lists them under `external_dependencies`;
the package neither copies nor removes them in the 0.4.x ownership series.

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

Revision manifests record paths, backup paths, package version, timestamp,
artifact hashes, and only the boolean needed to distinguish a package-created
root assignment—not instruction contents or secret values. A converged apply is
a NOOP and creates no revision. Rollback restores only the preceding package
revision. Uninstall removes both managed blocks and unchanged package-owned
artifacts. If the remaining config is semantically equal to the first-install
baseline, its exact backup bytes are restored; otherwise unrelated operator
edits are retained. It never runs Git reset/clean or deletes unknown config.

## CCR Desktop extension activation

**CCR-SENSITIVE — verified against CCR Desktop 3.0.20 on 2026-08-10.** The UI
loads a folder containing `plugin.json`; it does not require selecting the module
file directly. A changed UI, manifest format, or permission model can cause the
extension to be absent or leave namespace tools unfiltered.

1. Locate the copied directory shown in the deployment plan:
   `<CCR_HOME>/plugins/responses-tool-capability-compat`.
2. Open **CCR Desktop → Extensions → Install → Choose folder**.
3. Select the `responses-tool-capability-compat` **directory**, not
   `index.cjs`.
4. Before accepting, inspect `plugin.json` and verify module `index.cjs`, gateway
   surface enabled, and permissions `trusted-code` plus `core-gateway-config`.
5. Install it and keep it enabled, then restart CCR.

For an unverified CCR version, stop if these UI fields or permissions differ.
Do not edit an internal gateway runtime file. Re-run the package contract and a
controlled live namespace smoke after activation.

## Patch-series ownership rule

Patch releases within `0.4.x` must preserve the semantic managed target set:
the config marker, local provider id, model catalog path, role names/paths, and
CCR plugin id/path, plus root-policy ownership. Revision manifests record this
set and refuse a patch apply when it changes. Adding/removing a role or changing
an ownership contract requires a minor package version bump and an explicit
uninstall/redeploy path.

## 0.2 to 0.3 lifecycle boundary

Version 0.2 managed an internal CCR runtime file; 0.3 deliberately does not.
The 0.3 deployer refuses an in-place 0.2 lifecycle upgrade. Use the original
0.2 checkout to uninstall its deployment, confirm CCR runtime configuration is
restored, then deploy 0.3 and enable the extension through CCR Desktop.

## 0.3 to 0.4 root-policy ownership boundary

Version 0.3 packaged root lifecycle intent as an audit artifact but did not
install it. Version 0.4 owns one marked semantic block inside the existing root
`developer_instructions` string. The 0.4 deployer refuses an in-place 0.3
upgrade. Uninstall the active 0.3 deployment with its original checkout, review
the 0.4 dry-run plan, then apply 0.4. Existing operator root instructions are
merged and preserved; no root model/provider setting changes.

## Mailbox ownership boundary

Initial authoritative DeepSeek assignment delivery depends on a local mailbox
and `SubagentStart` hook that predate this repository's 0.4 ownership contract.
They are therefore an explicit external dependency, not an implied generated
artifact. A new machine must obtain the reviewed mailbox implementation and
register the hook through the operator's Codex configuration process. Doctor
checks only non-secret structure and counts; it never reads TASK bodies or
clears unknown queue entries.

Moving mailbox code/hook registration under package deployment requires a minor
version with safe `hooks.json` merge, backup, rollback, uninstall, and conflict
semantics. Do not introduce that ownership in a 0.4 patch.
