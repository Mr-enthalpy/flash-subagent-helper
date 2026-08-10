# Troubleshooting

## TASK_NOT_RECEIVED

This is an initial local TASK transport failure, not a DeepSeek refusal or HTTP
provider failure. Stop business-level evaluation and inspect, in order:

1. whether a matching receipt exists;
2. receipt status (`hook_emitted` is required);
3. mailbox queue/claimed/temp counts;
4. whether enqueue completed before spawn;
5. whether enqueue role exactly matched `agent_type`;
6. whether the packet's literal first line was exactly `TASK` (`TASK:` and
   leading metadata are invalid);
7. whether the `SubagentStart` hook actually ran;
8. only then provider/runtime evidence.

Do not use `followup_task` to repair the missed initial delivery: a resumed
thread does not trigger `SubagentStart`, and the current same-thread follow-up
capability is FAIL. `send_message` enqueue is not execution. Clear only the
identified stale receipt and perform at most a justified controlled retry after
understanding the failure.

Initial delivery failure (`TASK_NOT_RECEIVED`) and same-thread continuation
failure (follow-up accepted but the old assignment replays) are different
failure domains. The former is reliably avoidable through enqueue → fresh spawn
→ matching `hook_emitted`; the latter remains a Codex child handoff limitation.

## HTTP 429

HTTP 429 is provider/gateway rate or capacity pressure. Inspect request pacing,
parallelism, and provider limits. It is not fixed by mailbox cancellation and
must not share an undifferentiated retry handler with `TASK_NOT_RECEIVED`.

## LOCAL CCR 401

**Symptom:** `Invalid API key` at the local gateway. **Typical cause:** Codex is
using an expired profile-generated client key. **Long-term fix:** use an
independent CCR client credential referenced by a configurable environment
variable name.

## RESPONSES_MODEL_NOT_SUPPORTED

A visible model name does not prove the upstream deployment. Inspect the CCR
route, effective provider, effective model, and upstream protocol/capability.

## RESPONSES_FEATURE_NOT_SUPPORTED tool.namespace

`tool.namespace` means a top-level tool object such as `{ "type": "namespace" }`,
not a field named `namespace`. Select a compatibility profile that removes the
unsupported tool *type* in the final upstream request path and applies the
configured tool-choice fallback.

## PLUGIN TEST PASSES BUT LIVE REQUEST STILL FAILS

Module tests do not prove registration in CCR's live pipeline. Check active CCR
Desktop Extensions for the enabled plugin, then inspect before/after tool counts
and a redacted summary of the final upstream body. The package never edits
`gateway.config.json`. Never log prompts or credentials.

## CCR LOCAL AUTH vs UPSTREAM AUTH

Codex-to-CCR local client authentication and CCR-to-provider upstream
authentication are separate hops. Identify which hop returned 401 before acting.

## MODEL CATALOG CHANGE NOT EFFECTIVE

Codex may load model catalog metadata only at startup. Fully exit every Codex
Desktop/CLI process and start a new session.

## CODEX AUTO REVIEW 502

**VERSION-SENSITIVE:** a default reviewer selector may not be serviceable through
a custom provider route. This package renders `auto_review_model_override` to the
selected worker deployment. Revalidate current Codex Guardian semantics after
every upgrade; do not restore an unavailable reviewer alias as a workaround.

## UPSTREAM TIMEOUT

Do not classify a network timeout as an authentication or tool-compatibility
failure. Correlate redacted CCR status and retry policy separately.

## ENVIRONMENT VARIABLE CHANGED BUT CODEX STILL FAILS

Desktop Codex may retain its startup environment. Fully exit all Codex processes
and restart after changing the environment.

## WRONG DEPLOYMENT BEHIND SIMILAR MODEL NAME

Third-party routes may assign similar names to different deployments. Never infer
identity or capabilities from a display/model name alone; verify the effective
deployment with the provider.
