# Troubleshooting

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
