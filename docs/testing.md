# Test Layers

## STATIC — default CI

No Codex or CCR required: TOML/JSON/CJS parsing, source/reference checks,
deployment allowlist, secret scan, deterministic rendering, managed merge
invariants, generated consistency, and the provider-free external-worker
transport state-machine regression (strict TASK grammar, ordering gate, exact
role, fresh child, acknowledgement, compensation, expiry, and queue zero).

## LOCAL — no upstream call

With local Codex/CCR installed: discovery, version reporting, role and catalog
registration, local credential *presence* (not value), copied-extension
presence, and the packaged CCR extension contract. That contract does not prove
CCR activation. Run `codex-contract-smoke.ps1` to place the render in a
temporary isolated Codex home, consume every role with `codex debug prompt-input`,
and load the catalog with `codex debug models`. Current Codex rejects
`--strict-config` on debug commands, so exact-key allowlists provide the unknown-
field guard. These contracts perform no upstream request.

Offline doctor also checks the 0.4.x external mailbox prerequisite without
reading TASK contents: mailbox script present, `SubagentStart` hook registered,
provider-safe `validate-packet` PASS, queue state accessible, current follow-up
capability visible, and no queued/claimed/temporary residue. A non-empty queue
is reported as `MAILBOX QUEUE NOT EMPTY` and is never cleared automatically.

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
2. from a new Codex session prepare a harmless packet whose literal first line
   is `TASK`, enqueue it for the exact read-only role, and require
   `READY_TO_SPAWN`;
3. fresh-spawn the exact role with `fork_turns="none"`, then require the
   matching role + task_name receipt status `hook_emitted`; only now record
   `DISPATCHED`;
4. repeat the transaction for one workspace-write worker with one isolated fixture path;
5. require Guardian auto-review and record parent/reviewer/provider/protocol and
   redacted HTTP/approval status;
6. use a fresh read-only auditor through its own mailbox transaction;
7. remove only the fixture and confirm queue, claimed entries, temporary packet
   files, and validation fixtures are zero/absent.

If spawn fails after enqueue, cancel the exact receipt. If acknowledgement is
missing or the worker returns `TASK_NOT_RECEIVED`, stop business validation and
classify `TASK_TRANSPORT_FAILURE`; do not repair with `followup_task` or
`send_message`. Because the current mailbox selects role + FIFO, same-role
dispatches are staged serially through acknowledgement even when the delivered
workers will run concurrently.

The live lifecycle gate additionally runs random-marker typed spawn, same-thread
DELTA, PROJECT SYNC, heterogeneous reload identity, parallel worker, independent
auditor, workspace-write, and Guardian probes. Record only the matrix and
sanitized marker-presence/status evidence described in
`subagent-runtime-capabilities.md`; never store prompt or request bodies.

These probes are intentionally operator-driven rather than disguised as an
automated lifecycle harness. They can consume tokens and require permission to
use the selected provider. They must not print prompts, request bodies,
credentials, or user data.

The required fresh-machine `MAILBOX TRANSPORT SMOKE` is: harmless TASK packet →
enqueue → exact-role fresh read-only worker (`fork_turns="none"`) → matching
`hook_emitted` → exact fixture result → queue zero. Role/provider load alone is
not deployment readiness.
