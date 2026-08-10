# Codex + CCR + DeepSeek Flash Worker Pool Deployment Package

> **THIS PROJECT IS VERSION-SENSITIVE.**
>
> This project configures a Codex root agent to delegate execution-heavy work
> to typed DeepSeek Flash workers through CCR.
>
> It does not contain or manage API credentials.
>
> Codex, CCR, DeepSeek API, or provider upgrades require doctor and compatibility
> smoke tests before the combination is marked verified.

## Architecture

```text
Persistent intent
  -> seven role files + root lifecycle policy + one versioned Responses profile
  -> deterministic renderer and ownership-aware deployer
  -> Codex root policy (managed merge; root model/provider preserved)
  -> operator-managed mailbox: enqueue -> fresh spawn -> hook_emitted
  -> fixed local provider ccr_flash_worker
  -> CCR route + provider selected outside Codex
  -> OpenAI Responses-compatible DeepSeek Flash deployment
```

The Codex layer never receives an upstream provider id. It always uses the
package-owned `ccr_flash_worker`; provider credentials and routes remain CCR
responsibilities. See [architecture](docs/architecture.md).

The repository also carries a provider-independent, machine-readable subagent
lifecycle policy and a sanitized runtime capability baseline. Policy readiness
does not imply runtime reuse readiness: the tested baseline currently marks
same-thread follow-up and PROJECT SYNC as failed and requires checkpoint-based
degraded continuation. See [runtime capabilities](docs/subagent-runtime-capabilities.md).

## Requirements

- Windows PowerShell 7+
- Python 3.11+
- Node.js 20+
- installed and authenticated official Codex client
- installed CCR gateway
- a separately configured upstream credential and CCR local client credential
- an operator-installed DeepSeek TASK mailbox script and registered
  `SubagentStart` hook in `CODEX_HOME` (external dependency in 0.4.x)

## Quick start

```powershell
git clone <YOUR_REMOTE_URL>
cd codex-ccr-deepseek-worker-pool
.\scripts\bootstrap.ps1
.\scripts\doctor.ps1
.\scripts\deploy.ps1
.\scripts\deploy.ps1 -Apply
.\scripts\validate.ps1
.\scripts\codex-contract-smoke.ps1
```

Review the dry-run plan before `-Apply`, restart Codex completely, then run an
explicit paid smoke only if permitted. The deployer copies the CCR extension but
does not edit CCR's internal runtime configuration: enable
`responses-tool-capability-compat` in CCR Desktop **Extensions** before restart.
For the tested CCR 3.0.20 UI, choose the copied plugin **directory**; its
`plugin.json` resolves the module to `index.cjs`. See the deployment guide.

Version 0.4.x intentionally does not take ownership of an existing
`hooks.json` or mailbox script. Doctor reports this prerequisite explicitly.
External-worker deployment is not READY until an operator has installed the
mailbox/hook and completed the provider-safe enqueue → fresh typed spawn →
matching `hook_emitted` acceptance with queue zero.

```powershell
.\scripts\doctor.ps1 -Live -ConfirmCost
```

## Security model

Only files matching `publish-allowlist.txt` may pass validation. `.gitignore` is
defense in depth, not the trust boundary. `secret-scan.ps1` rejects credential-
shaped values, forbidden auth/runtime files, binary files, and user-specific
Windows paths. Secrets remain in environment variables, the OS credential
store, or CCR's credential store; only configurable environment variable names
are stored here.

## Supported and tested versions

See [VERSION_MATRIX.md](VERSION_MATRIX.md). Versions are audit evidence and
upgrade triggers, not proof of compatibility. Apply requires the packaged
extension contract to pass. That contract verifies the distributable module and
registration shape. The operator confirms enablement in CCR Extensions; a
controlled live smoke separately confirms the required namespace behavior.

## Deployment and validation

The deployer owns two narrow semantic blocks: the local provider/`[agents.*]`
TOML block and a marked root-policy block inside the top-level
`developer_instructions` string. Existing operator instructions are preserved;
unsupported or ambiguous TOML string syntax fails closed. The official root
model/provider, authentication, other agents, MCP servers, and tools are never
replaced. A changed apply writes a revision manifest and full-file backup; an
already-converged apply is a NOOP. Rollback restores the preceding revision,
and uninstall removes only package-owned semantics while restoring the exact
first-install config when no unrelated semantic changes were made.

Version 0.4.0 is the explicit root-policy ownership boundary. An active 0.3.x
deployment must be uninstalled with its original checkout before installing
0.4.0; the deployer refuses to infer that migration.

- [Deployment guide](docs/deployment.md)
- [Provider integration](docs/provider-integration.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Test layers and live acceptance](docs/testing.md)
- [Upgrade procedure](docs/upgrade.md)
- [Subagent lifecycle and runtime capabilities](docs/subagent-runtime-capabilities.md)
- [User responsibilities](USER_RESPONSIBILITIES.md)

OpenAI documents Codex user/project configuration layering and precedence in
[Config basics](https://developers.openai.com/codex/config-basic), typed workers
in [Subagents](https://developers.openai.com/codex/subagents), and Guardian
behavior in [Auto-review](https://developers.openai.com/codex/auto-review).
