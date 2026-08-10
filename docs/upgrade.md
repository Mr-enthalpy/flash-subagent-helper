# Upgrade Procedure

For any Codex, CCR, DeepSeek API family, compatibility plugin, or provider API
upgrade:

1. snapshot the current version matrix and local revision manifest;
2. run offline validation and secret scan;
3. inspect upstream schema/hook/release changes;
4. run all compatibility fixtures;
5. run offline/local doctor;
6. run a controlled, explicitly authorized live read-only and isolated-write
   smoke, including Guardian auto-review, receipt, independent audit, cleanup;
7. update `VERSION_MATRIX.md` and the profile version/baseline;
8. mark the version VERIFIED only after every required layer passes.

Starting successfully or reporting a familiar version is insufficient evidence
of compatibility. A packaged extension contract is not evidence of activation
inside CCR. `VERIFIED` requires the Codex contract, explicit CCR extension
activation, and the controlled live smoke appropriate to the change.

Package 0.2 and 0.3 use different CCR ownership contracts. Do not apply 0.3 over
an active 0.2 deployment. Uninstall with the original 0.2 checkout first, then
install 0.3 and activate the copied extension through CCR Desktop.

Patch releases must not add or remove managed roles, change the managed marker
or local provider id, or change the managed plugin path/id. Those changes alter
the managed target set and require a minor version bump. The deployer records
the semantic set in each revision manifest and fails closed on a same-minor
mismatch; it does not attempt an automatic ownership migration.

When the Codex sandbox/network schema changes, re-check that the intentional
read-only defense-in-depth declaration is still accepted and whether Codex now
offers a more precise read-only network-deny field or a documented stable
fail-closed contract.
