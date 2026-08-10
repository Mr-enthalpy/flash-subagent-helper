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
12. install and maintain the external DeepSeek TASK mailbox script and its
    `SubagentStart` hook in `CODEX_HOME` for package 0.4.x;
13. run the mailbox transport smoke and confirm a matching `hook_emitted`
    receipt plus an empty queue before declaring external workers ready.

Users must review every apply plan, verify the effective provider/model identity,
keep credentials outside this repository, restart Codex when required, and rerun
offline plus controlled live acceptance after version changes. Users must also
enable the copied compatibility extension through CCR Desktop Extensions; the
repository never mutates CCR's internal runtime gateway configuration.
The repository also does not silently modify `hooks.json` in the 0.4.x ownership
series. A future package-managed mailbox/hook requires an explicit minor-version
ownership boundary; until then, doctor treats it as an external prerequisite.
