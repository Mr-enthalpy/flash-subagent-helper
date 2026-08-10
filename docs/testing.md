# Test Layers

## STATIC — default CI

No Codex or CCR required: TOML/JSON/CJS parsing, source/reference checks,
deployment allowlist, secret scan, deterministic rendering, managed merge
invariants, and generated consistency.

## LOCAL — no upstream call

With local Codex/CCR installed: discovery, version reporting, role and catalog
registration, local credential *presence* (not value), copied-extension
presence, and the packaged CCR extension contract. That contract does not prove
CCR activation. Run `codex-contract-smoke.ps1` to place the render in a
temporary isolated Codex home, consume every role with `codex debug prompt-input`,
and load the catalog with `codex debug models`. Current Codex rejects
`--strict-config` on debug commands, so exact-key allowlists provide the unknown-
field guard. These contracts perform no upstream request.

## COMPATIBILITY — mock request

Provider-independent fixtures exercise 19 tools/7 namespaces, 12 normal tools,
function/custom apply-patch preservation, namespace tool-choice fallback,
selector isolation, final Responses endpoint filtering, and idempotence.

## AUTOMATED LIVE — explicit, never required by CI

`doctor.ps1 -Live -ConfirmCost` automates only the minimal CCR/Responses route
and compatibility request. It can consume tokens. Passing it does not prove
typed-worker lifecycle, Guardian, receipt, or reload behavior.

## OPERATOR-DRIVEN LIVE — explicit, never required by CI

Live acceptance is a controlled operator procedure:

1. run `doctor.ps1 -Live -ConfirmCost` for a minimal route/plugin request;
2. from a new Codex session enqueue and spawn a read-only typed worker;
3. enqueue and spawn one workspace-write worker with one isolated fixture path;
4. require Guardian auto-review and record parent/reviewer/provider/protocol and
   redacted HTTP/approval status;
5. verify the mailbox receipt is emitted and queue returns to zero;
6. use a fresh read-only auditor;
7. remove only the fixture and confirm no packet/temp residue.

The live lifecycle gate additionally runs random-marker typed spawn, same-thread
DELTA, PROJECT SYNC, heterogeneous reload identity, parallel worker, independent
auditor, workspace-write, and Guardian probes. Record only the matrix and
sanitized marker-presence/status evidence described in
`subagent-runtime-capabilities.md`; never store prompt or request bodies.

These probes are intentionally operator-driven rather than disguised as an
automated lifecycle harness. They can consume tokens and require permission to
use the selected provider. They must not print prompts, request bodies,
credentials, or user data.
