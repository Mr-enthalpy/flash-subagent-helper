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
of compatibility. `VERIFIED` requires passing Codex and CCR contract probes plus
the controlled live smoke appropriate to the change.
