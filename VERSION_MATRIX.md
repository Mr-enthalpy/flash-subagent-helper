# Version Matrix

| Component | Verified baseline | Status |
|---|---:|---|
| Package schema | 1 | VERIFIED |
| Package | 0.1.0 | VERIFIED offline |
| Codex CLI | 0.146.0 | VERIFIED local schema baseline |
| CCR | local build version unresolved | UNVERIFIED until detector identifies interface/version |
| CCR plugin interface | `providerPlugins.transformRequest`; `CUSTOM_ROUTER_PATH` adapter available | VERSION-SENSITIVE |
| Platform | Windows 11 x64 class | VERIFIED offline |
| Model family | DeepSeek Flash-compatible | deployment identity must be verified |
| Responses profile | `deepseek_responses_v4@1.0.0` | VERIFIED fixtures |
| Last verified | 2026-08-09 | — |

No row promises compatibility with “latest.” The machine-readable authority is
`compatibility.lock.toml`.

Sensitive points include typed agent schema, `fork_turns`, Multi-Agent V2 tool
surface, model catalog/load lifecycle, auto-review override semantics, Guardian,
namespace encoding, apply-patch representation, CCR routers/transformers and
final upstream pipeline, Responses tools, and provider route aliases.
