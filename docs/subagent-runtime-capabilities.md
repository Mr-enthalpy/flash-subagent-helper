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
| typed worker spawn | PASS |
| parallel typed workers | PASS |
| same-thread follow-up | FAIL |
| same-thread PROJECT SYNC | FAIL |
| heterogeneous reload identity | UNVERIFIED |
| independent auditor | PASS |
| workspace write | PASS |
| Guardian auto-review | PASS |

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
CONTINUATION
ROLE
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

## Revalidation

After Codex, multi-agent runtime, custom-provider child routing, CCR, or
Responses compatibility changes, rerun typed spawn, DELTA, PROJECT SYNC,
heterogeneous reload identity, independent auditor, workspace-write, and
Guardian smokes. Promote same-thread reuse only after both DELTA and sync pass.
If reload identity remains unverified, claim active-thread reuse only.

Live probes use random harmless markers and may consume provider tokens. Never
store Authorization headers, keys, cookies, prompts, full request bodies, user
data, or dynamic thread ids in this repository.
