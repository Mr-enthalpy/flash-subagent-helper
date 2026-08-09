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
  -> declarative model-family, role, compatibility, and deployment configuration
  -> deterministic renderer and ownership-aware deployer
  -> local Codex typed roles + model catalog + CCR compatibility plugin
  -> OpenAI Responses-compatible DeepSeek Flash deployment
```

Core logic is provider-independent. Provider and route differences are limited
to `deployment.local.toml`, which is git-ignored. See [architecture](docs/architecture.md).

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

See [VERSION_MATRIX.md](VERSION_MATRIX.md) and `compatibility.lock.toml`. Unknown
CCR versions are `UNVERIFIED` and real apply aborts unless the user supplies an
explicit override after review.

## Deployment and validation

The deployer merges a stable, marked `[agents.*]` block into the Codex user
configuration. It preserves the official root model/provider, authentication,
other agents, MCP servers, tools, and unrelated instructions. Same-name
unmanaged agents are a hard conflict. Every apply writes a local revision
manifest and backups outside the repository.

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
