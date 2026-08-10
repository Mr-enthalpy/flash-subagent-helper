# Subagent Lifecycle and Runtime Capability Gate

Policy intent and runtime capability are separate. Subagents are reusable,
context-bearing workers with role/workstream affinity. Reuse is nevertheless
capability-gated: a fresh worker plus an old summary is checkpoint continuation,
not same-thread reuse.

The declaration lives in `policy/subagent-lifecycle.toml` and is installed as a
package-managed block inside root `developer_instructions`; the latest sanitized
test evidence lives in `validation/subagent-runtime-capabilities.toml`. Neither
source file contains credentials, prompts, request bodies, thread ids, machine
paths, or provider-specific routing.

## Current tested baseline

| Capability | Result |
|---|---|
| mailbox packet validation | PASS |
| mailbox enqueue | PASS |
| fresh spawn after enqueue | PASS |
| SubagentStart delivery | PASS |
| hook receipt verification | PASS |
| typed worker spawn | PASS only for complete verified transaction |
| parallel typed workers | PASS |
| same-thread follow-up | FAIL |
| same-thread PROJECT SYNC | FAIL |
| heterogeneous reload identity | UNVERIFIED |
| independent auditor | PASS |
| workspace write | PASS |
| Guardian auto-review | PASS |

`spawn_typed_worker = PASS` never means a naked `spawn_agent` call. It means:

```text
authoritative packet whose literal first line is TASK
  -> enqueue for exact role
  -> READY_TO_SPAWN for role + task_name + receipt
  -> fresh physical child with fork_turns="none"
  -> matching SubagentStart receipt status hook_emitted
  -> DISPATCHED
```

The receipt created by enqueue is the correlation identity. `task_name` is a
short, non-sensitive audit label, not the authoritative payload or a queue
selector. The tested mailbox consumes by role + FIFO, so only one unconsumed
packet per role is safe. Complete acknowledgement for A before enqueueing B for
the same role; the resulting workers may then execute in parallel.

Failure compensation is part of the contract: enqueue failure forbids spawn;
spawn failure after enqueue cancels the exact receipt; a missing/mismatched
receipt remains `SPAWNED_UNVERIFIED` and is a transport failure. A worker that
returns `TASK_NOT_RECEIVED` has not received a business assignment. Inspect the
receipt, queue, ordering, role binding, strict packet grammar, and
`SubagentStart` before considering provider diagnosis or retry.

The provider-safe marker probe accepted the follow-up call but replayed the old
assignment. Sanitized CCR inspection found the initial marker and no delta
marker in the observed request, while the old request reached upstream with a
successful status. This is classified as `CODEX_CHILD_HANDOFF_FAILURE`; the CCR
compatibility plugin must not cache task history or implement a parallel resume
protocol.

## Degraded continuation

While follow-up or PROJECT SYNC is not PASS, use one coherent assignment per
workstream and finish likely-to-continue work with:

```text
WORKSTREAM CHECKPOINT
WORKSTREAM
CURRENT STATE
CURRENT UNDERSTANDING
FILES / SYMBOLS
DECISIONS ALREADY MADE
INVARIANTS
KNOWN FAILURES
TEST STATUS
NEXT LIKELY STEP
UNRESOLVED
```

A fresh typed worker receives only:

```text
TASK
ROLE
MODE
CONTINUATION VIA CHECKPOINT
WORKSTREAM
PREVIOUS CHECKPOINT
CHANGES SINCE CHECKPOINT
OBJECTIVE
INVARIANTS
WRITE_SCOPE
ACCEPTANCE
RETURN
```

Call this `CONTINUATION VIA CHECKPOINT`. Do not use `send_message` as a resume
substitute, and do not report queued delivery as executed work. If same-thread
sync is unavailable, use `PROJECT STATE RECOVERY` with the checkpoint and the
relevant current diff/state.

This preserves a logical worker (role + workstream + checkpoint affinity)
across fresh physical children. It is degraded continuity, never same-thread
reuse. Every continuation packet still enters through the same mailbox
transaction and still begins with `TASK`.

## Package boundary

In package 0.4.x the mailbox implementation and `SubagentStart` registration
are operator-managed external dependencies. The package installs the root gate
and diagnoses their presence, registration, validator, and queue count; it does
not claim ownership of or rewrite `hooks.json`. This avoids an undeclared patch-
series ownership expansion. External-worker deployment cannot be marked READY
on a new machine until the mailbox transport smoke passes with queue zero.

## Revalidation

After Codex, multi-agent runtime, custom-provider child routing, CCR, or
Responses compatibility changes, rerun typed spawn, DELTA, PROJECT SYNC,
heterogeneous reload identity, independent auditor, workspace-write, and
Guardian smokes. Promote same-thread reuse only after both DELTA and sync pass.
If reload identity remains unverified, claim active-thread reuse only.

Live probes use random harmless markers and may consume provider tokens. Never
store Authorization headers, keys, cookies, prompts, full request bodies, user
data, or dynamic thread ids in this repository.
