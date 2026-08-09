# User Responsibilities

This repository does not:

1. install or sign in to official Codex;
2. install CCR;
3. obtain upstream API access;
4. store or configure the upstream credential in CCR;
5. create or store the independent CCR local client credential;
6. place secrets in an environment variable or OS credential store;
7. guarantee that a provider's model selector reaches the intended deployment;
8. pay API token costs;
9. approve networking or live tests;
10. replace review of the dry-run plan and backups;
11. certify compatibility after an upgrade.

Users must review every apply plan, verify the effective provider/model identity,
keep credentials outside this repository, restart Codex when required, and rerun
offline plus controlled live acceptance after version changes.
