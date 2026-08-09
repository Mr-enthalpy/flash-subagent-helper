# Test Layers

## STATIC — default CI

No Codex or CCR required: TOML/JSON/CJS parsing, source/reference checks,
deployment allowlist, secret scan, deterministic rendering, managed merge
invariants, and generated consistency.

## LOCAL — no upstream call

With local Codex/CCR installed: discovery, version/interface detection, role and
catalog registration, local credential *presence* (not value), plugin/profile
load, and gateway plugin registration structure.

## COMPATIBILITY — mock request

Provider-independent fixtures exercise 19 tools/7 namespaces, 12 normal tools,
function/custom apply-patch preservation, namespace tool-choice fallback,
selector isolation, final Responses endpoint filtering, and idempotence.

## LIVE — explicit, never required by CI

Live acceptance is a controlled operator procedure:

1. run `doctor.ps1 -Live -ConfirmCost` for a minimal route/plugin request;
2. from a new Codex session enqueue and spawn a read-only typed worker;
3. enqueue and spawn one workspace-write worker with one isolated fixture path;
4. require Guardian auto-review and record parent/reviewer/provider/protocol and
   redacted HTTP/approval status;
5. verify the mailbox receipt is emitted and queue returns to zero;
6. use a fresh read-only auditor;
7. remove only the fixture and confirm no packet/temp residue.

The live request can consume tokens and requires permission to use the selected
provider. It must not print prompts, request bodies, credentials, or user data.
