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
  -> seven role files + one versioned DeepSeek Flash Responses profile
  -> deterministic renderer and ownership-aware deployer
  -> Codex root (preserved) + fixed local provider ccr_flash_worker
  -> CCR route + provider selected outside Codex
  -> OpenAI Responses-compatible DeepSeek Flash deployment
```

The Codex layer never receives an upstream provider id. It always uses the
package-owned `ccr_flash_worker`; provider credentials and routes remain CCR
responsibilities. See [architecture](docs/architecture.md).

## Requirements

- Windows PowerShell 7+
- Python 3.11+
- Node.js 20+
- installed and authenticated official Codex client
- installed CCR gateway
- a separately configured upstream credential and CCR local client credential

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
explicit paid smoke only if permitted:

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
upgrade triggers, not proof of compatibility. Apply requires the selected CCR
adapter's executable contract probe to pass; there is no version bypass flag.

## Deployment and validation

The deployer merges one stable marked block containing the package-owned local
provider and `[agents.*]` registrations. It preserves the official root model
and provider, authentication, other agents, MCP servers, tools, and unrelated
instructions. Same-name unmanaged objects are hard conflicts. Every apply
writes a local revision manifest and backups outside the repository.

- [Deployment guide](docs/deployment.md)
- [Provider integration](docs/provider-integration.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Test layers and live acceptance](docs/testing.md)
- [Upgrade procedure](docs/upgrade.md)
- [User responsibilities](USER_RESPONSIBILITIES.md)

OpenAI documents Codex user/project configuration layering and precedence in
[Config basics](https://developers.openai.com/codex/config-basic), typed workers
in [Subagents](https://developers.openai.com/codex/subagents), and Guardian
behavior in [Auto-review](https://developers.openai.com/codex/auto-review).
