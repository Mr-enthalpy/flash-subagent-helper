# Provider-neutral example

1. Configure `fixture-provider` and its credential in a non-repository CCR test
   instance.
2. Put the non-secret CCR model selector and verified effective model identity
   in a local deployment file; do not expose the CCR provider id to Codex.
3. Confirm the route satisfies the packaged profile by capability evidence.
4. Run offline validation, the packaged extension contract, a mock compatibility
   test, activate the extension in CCR Desktop, then run an explicitly authorized
   live smoke.

This example deliberately contains no real endpoint, account, provider brand,
or credential.
