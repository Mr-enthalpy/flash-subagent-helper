# Version Matrix

| Component | Verified baseline | Status |
|---|---:|---|
| Package schema | 2 | VERIFIED |
| Package | 0.2.0 | VERIFIED offline |
| Codex CLI | 0.146.0 | VERIFIED local schema baseline |
| CCR | local build version unresolved | version is audit-only |
| CCR adapter | `gateway_plugin_v1`: `plugins[]` + `providerPlugins.transformRequest` | executable contract required |
| Platform | Windows 11 x64 class | VERIFIED offline |
| Model family | DeepSeek Flash-compatible | deployment identity must be verified |
| Responses profile | `deepseek-flash-responses@1.0.0` | VERIFIED fixtures + Codex contract |
| Last verified | 2026-08-09 | — |

No row promises compatibility with “latest.” This matrix is audit history, not
a compatibility oracle. Current compatibility is decided by executable Codex
and CCR contract probes plus controlled live smoke.

Sensitive points include typed agent schema, `fork_turns`, Multi-Agent V2 tool
surface, model catalog/load lifecycle, auto-review override semantics, Guardian,
namespace encoding, apply-patch representation, CCR routers/transformers and
final upstream pipeline, Responses tools, and provider route aliases.
