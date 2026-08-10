# Version Matrix

| Component | Verified baseline | Status |
|---|---:|---|
| Package schema | 2 | VERIFIED |
| Package | 0.4.1 | VERIFIED offline |
| Codex CLI | 0.146.0 | VERIFIED local schema baseline |
| CCR Desktop | 3.0.20 | Extensions folder-picker flow verified; version remains audit-only |
| CCR extension packaging | manifest `setup()` → core gateway registration → `transformRequest` | package contract VERIFIED; activation requires operator/live confirmation |
| Platform | Windows 11 x64 class | VERIFIED offline |
| Model family | DeepSeek Flash-compatible | deployment identity must be verified |
| Responses profile | `deepseek-flash-responses@1.1.0` | VERIFIED fixtures + Codex contract |
| Last verified | 2026-08-10 | — |
| Subagent policy | READY | deterministic root merge contract VERIFIED offline |
| Same-thread reuse | DEGRADED | DELTA and PROJECT SYNC failed |
| Heterogeneous reload | UNVERIFIED | no reliable unload trigger |
| Initial TASK transport | PASS with precondition | external mailbox enqueue → fresh spawn → `hook_emitted`; naked spawn is not PASS |

No row promises compatibility with “latest.” This matrix is audit history, not
a compatibility oracle. The Codex consumer and packaged CCR extension contracts
are offline evidence; CCR activation requires operator confirmation, while
upstream compatibility requires the controlled live smoke.

Sensitive points include typed agent schema, `fork_turns`, Multi-Agent V2 tool
surface, model catalog/load lifecycle, auto-review override semantics, Guardian,
namespace encoding, apply-patch representation, CCR routers/transformers and
final upstream pipeline, Responses tools, and provider route aliases.

## Closed audit decisions

`read-only` roles retaining `[sandbox_workspace_write] network_access = false`
is **CLOSED / WON'T FIX — INTENTIONAL DEFENSE-IN-DEPTH**. Under the current
Codex schema, long-term network denial outweighs structural neatness; revisit
only when a read-only-specific deny field or stable fail-closed contract exists.
