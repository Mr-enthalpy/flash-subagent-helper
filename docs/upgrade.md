# Upgrade Procedure

For any Codex, CCR, DeepSeek API family, compatibility plugin, or provider API
upgrade:

1. snapshot the current version matrix and local revision manifest;
2. run offline validation and secret scan;
3. inspect upstream schema/hook/release changes;
4. run all compatibility fixtures;
5. run offline/local doctor;
6. run a controlled, explicitly authorized live read-only and isolated-write
   smoke, including Guardian auto-review, receipt, independent audit, cleanup,
   strict mailbox TASK delivery, same-thread DELTA, PROJECT SYNC, and
   heterogeneous reload identity;
7. update `VERSION_MATRIX.md` and the profile version/baseline;
8. mark the version VERIFIED only after every required layer passes.

Starting successfully or reporting a familiar version is insufficient evidence
of compatibility. A packaged extension contract is not evidence of activation
inside CCR. `VERIFIED` requires the Codex contract, explicit CCR extension
activation, and the controlled live smoke appropriate to the change.

Package 0.2 and 0.3 use different CCR ownership contracts. Package 0.3 and 0.4
also differ: 0.4 explicitly owns a marked block inside root
`developer_instructions`. Do not cross either minor ownership boundary in place.
Uninstall with the currently installed package's original checkout, confirm its
baseline is restored, then install the next minor version.

Patch releases must not add or remove managed roles, change the managed marker
or local provider id, or change the managed plugin path/id. Those changes alter
the managed target set and require a minor version bump. The deployer records
the semantic set in each revision manifest and fails closed on a same-minor
mismatch; it does not attempt an automatic ownership migration.

When the Codex sandbox/network schema changes, re-check that the intentional
read-only defense-in-depth declaration is still accepted and whether Codex now
offers a more precise read-only network-deny field or a documented stable
fail-closed contract.

Runtime lifecycle capabilities are partial and must not be collapsed into a
single READY flag. Upgrade validation updates the sanitized capability report;
same-thread reuse is promoted only when both DELTA delivery and PROJECT SYNC
pass. An unverified heterogeneous reload permits active-thread reuse only.

After any Codex/Multi-Agent/custom-provider/CCR/Responses change, rerun the
mailbox transaction separately: strict packet validation, exact-role enqueue,
fresh typed spawn with `fork_turns="none"`, matching `hook_emitted`, exact
fixture result, and queue zero. A naked spawn must never be promoted to PASS.
Re-check that `SubagentStart` registration remains accepted. In the 0.4.x
series the mailbox and `hooks.json` remain operator-managed external
dependencies; taking package ownership requires a minor lifecycle boundary.

Codex config schema upgrades must also rerun the root consumer contract. Confirm
that top-level `developer_instructions` remains a string, the managed policy is
accepted, unrelated operator instructions survive apply/uninstall, and root
model/provider values remain unchanged.
