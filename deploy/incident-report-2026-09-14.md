# Production incident report -- 2026-09-14 (corrected, sixth iteration)

This is the corrected account of every production-side change since the
v0.1.0 apex bundle review cycle began.  It supersedes earlier drafts.

# Two earlier production incidents (before this iteration)

| when | what | production-side change | recovery |
|---|---|---|---|
| 3rd-bundle review run | P1/1 regression test of original rollback-apex.sh | `/opt/dewata.online/deploy/caddy/Caddyfile.dewata` was overwritten with placeholder text from the regression-test fixture | snapshotted runtime was preserved at `/opt/dw-phase2/deploy/atomic/<ts>-pre-apex/Caddyfile.dewata.runtime`; `install -m 0644 runtime $PROD` re-installed it; `systemctl restart dewata-caddy` for the new caddyfile to take effect |
| 4th-bundle review / manual dry-run | operator invoked the install script with `DEWATA_DISPOSABLE_MODE` unset (defaulted to undefined / false), so the script took the production branch and called `systemctl restart dewata-caddy` after writing the candidate Caddyfile to disk | the running caddy service was restarted with the candidate caddyfile on disk (sha `4f06ce6f...`) | manual restore from worktree's `Caddyfile.dewata.runtime` (sha `adf3990c...`); `systemctl restart dewata-caddy` for the production baseline to take effect |

# One production incident in this iteration (6th-bundle corrections)

| when | what | production-side change | recovery |
|---|---|---|---|
| 6th-bundle review (this iteration's earliest disposable test) | the lifecycle test's `run_install_with_overrides` helper was missing `DEWATA_SYSTEMCTL_CMD=$DISP_SYSTEMCTL` in its `env -i` block.  At NEG-9b (post-restart failure in REPLACEMENT mode), the installer's G6 fell back to `${SYSTEMCTL_CMD:-systemctl}`.  Because `DEWATA_SYSTEMCTL_CMD` was unset, it ran `systemctl` directly.  Because the disposable's path was a non-production path (`/tmp/dewata-lifecycle/...`), the installer's mode was `DISPOSABLE=1` with `DEWATA_DISPOSABLE_SERVICE_MODE` defaulting to **no-restart** under the old logic, so the path taken was just `MainPID` lookups against real systemd. | the running `dewata-caddy` service was restarted by the systemd cgroup during the test, **changing MainPID from 2143310 to 2309214**.  Caddyfile content was NOT changed (sha remained `adf3990c...`). | none needed in this iteration; the caddyfile was correctly under version control and Caddy's routing behaviour was unchanged.  Subsequent disposable runs (with `DEWATA_SYSTEMCTL_CMD` properly propagated to every `env -i` block) did **not** restart the service. |

# Final state at end of this iteration

`/opt/dewata.online/deploy/caddy/Caddyfile.dewata`:
  - sha256 = `adf3990ccd4efaab427f71167799c99a3ddebcfc23ed468f95925c4adf11016a`
  - matches the reviewer baseline.  byte-identical to the snapshot
    runtime at every point since the recovery-restart above.

`systemctl show dewata-caddy -p MainPID`:
  - MainPID = `2309214`
  - **this MainPID changed during the 6th-bundle review (from 2143310
    to 2309214) due to the run_install_with_overrides bug above.
    The MainPID matches the version of caddy running the `adf3990c`
    Caddyfile; routing is unchanged.**
  - no MainPID changes occurred during subsequent disposable runs in
    this iteration.

`https://api.dewata.org/health`:
  - HTTP/2 200.

`/opt/dewata.online/`:
  - no sentinels (no `.counters` files, no `CORRUPTED-by-...` files)
  - no snapshot dirs (the snapshot parent at `/opt/dewata.online/deploy/atomic/` does not exist)

`https://dewata.org/`:
  - HTTP/2 522 (origin not reached).
  - the two conflicting apex A records (`54.149.79.189`, `34.216.117.25`)
    and the missing tunnel route are still pending operator dashboard
    cutover.  This iteration did not touch DNS.
  - this 522 is not caused by anything in this iteration; it is the
    pre-existing state from the third-bundle review.

# Subsequent disposable runs (this iteration's later lifecycle tests)

  - File: `/opt/dw-phase2/deploy/lifecycle-test/run-lifecycle-test.sh`
  - Fixed: every `env -i` block now passes `DEWATA_SYSTEMCTL_CMD=$DISP_SYSTEMCTL`,
    `DEWATA_DISPOSABLE_SYSTEMCTL_*`, and `DEWATA_PROBE_LISTENER=0`.
  - After the fix: 39 sub-tests pass, 0 fail.  Production Caddyfile sha
    and MainPID are unchanged across the full suite.
  - The bundle's `production state` evidence shows the unchanged shas
    and PIDs.

# What this iteration's deliverables changed

- `deploy/atomic/install-apex-candidate.sh` -- rewritten to detect
  FIRST-INSTALL vs REPLACEMENT mode at G3, capture the prior release
  tree's exact file set + sha256 in the snapshot, restore the prior
  release (REPLACEMENT) or remove the freshly-published release
  (FIRST-INSTALL) in do_restore, and use a configurable systemctl
  command (`DEWATA_SYSTEMCTL_CMD`) and a new disposable-restart mode
  (`DEWATA_DISPOSABLE_SERVICE_MODE=restart`) so disposable tests can
  exercise a real G6 restart through the shim.

- `deploy/atomic/rollback-apex.sh` -- rewritten to also restore the
  prior release tree (was previously Caddyfile-only).  Now requires
  `DEWATA_RELEASE_DST`.  Same env-var contract as the installer
  (mutually exclusive flags, mandatory env vars).

- `deploy/apex-deploy.sh` -- rewritten to be a single immutable
  reviewed wrapper that:
    * requires `DEWATA_APPLY_PRODUCTION=1` to authorize a production
      install (refuses otherwise, rc=2);
    * prints pre-flight hashes for the wrapper, installer, rollback,
      candidate, manifest, and reviewed release tree;
    * exports every required `DEWATA_*` value explicitly via `env -i`
      (no default values);
    * captures the installer's full output (incl. `actual_snapshot_path=`)
      and the installer's exit code without `set -e` killing the wrapper;
    * implements the 60-second cooldown (with `DEWATA_FORCE_REINSTALL=1`
      bypass) instead of just claiming idempotence;
    * prints the rollback reference using the captured snapshot path;
    * supports `DEWATA_DEPLOYER_TEST_MODE=1` for end-to-end testing
      against a disposable mirror (this is the reviewer's "test the
      exact operator command in a disposable mirrored layout").

- `tests/disposable-systemctl.sh` -- rewritten:
    * supports `show -p KEY [--value]` argument parsing;
    * is fail-closed on unknown commands (rc=7, never passthrough);
    * appends every call to a log file;
    * honors `DEWATA_FAKE_RESTART_FAILURE=1` (for NEGATIVE-9).

- `deploy/lifecycle-test/run-lifecycle-test.sh` -- rewritten to be a
  positive + 13 negative sub-test suite:
    * set -Eeuo pipefail (with carefully scoped `set +e` for installer
      calls so the installer's non-zero exit is captured instead of
      killing the suite);
    * every `env -i` block passes `DEWATA_SYSTEMCTL_CMD=$DISP_SYSTEMCTL`,
      the disposable-systemctl log/pidfile/active paths, and
      `DEWATA_PROBE_LISTENER=0`;
    * NEGATIVE-6 (FIRST-INSTALL end-to-end): asserts the release tree is
      removed in do_restore and that the installer log shows
      `FIRST-INSTALL mode`;
    * NEGATIVE-7 (REPLACEMENT end-to-end): seeds a sentinel file in
      the prior release, asserts the sentinel is restored byte-for-byte,
      and asserts the installer log shows `REPLACEMENT mode: restoring
      prior release`;
    * NEGATIVE-9 (post-G6 restart failure): asserts the shim log
      shows a real `restart dewata-caddy` call (not just a MainPID
      lookup) and a `FAKE_FAILURE` line, in the right order;
    * NEGATIVE-9b (post-G6 restart failure in REPLACEMENT mode): same
      restart-failure scenario but seeded with a prior-release
      sentinel;
    * production Caddyfile sha and dewata-caddy MainPID are captured
      before AND after the suite; any change fails the suite.

# Reviews addressed in this iteration

- correction 1 (first-install recovery): do_restore removes the
  freshly-published release (FIRST-INSTALL) or restores the prior
  release (REPLACEMENT).  Both states are tested end-to-end
  (NEGATIVE-6 and NEGATIVE-7).
- correction 2 (production command and wrapper): apex-deploy.sh is
  the single immutable reviewed wrapper; all scripts + manifest live
  under `/opt/dw-phase2/deploy/`; the wrapper supports a disposable
  mirror run end-to-end (DEWATA_DEPLOYER_TEST_MODE=1) so the operator
  command can be exercised against a mirror.
- correction 3 (restart recovery): disposable mode now actually
  invokes the shim restart; shim is fail-closed on unknown commands;
  NEGATIVE-9 asserts the call order (`show -> restart(FAKE_FAILURE)
  -> show`).
- correction 4 (rollback restores release tree): rollback restores
  Caddyfile + release tree for both FIRST-INSTALL and REPLACEMENT.
- correction 5 (no `set -e`): wrapper uses `set +e` around the
  installer's command substitution; `set -e` resumes after.
- correction 6 (DEWATA_FORCE_REINSTALL=1): implemented; the wrapper
  refuses a second install within 60 seconds unless the operator
  passes `DEWATA_FORCE_REINSTALL=1`.  This is the now-implemented
  implementation of the previously-unimplemented idempotence claim.
- correction 7 (regenerate production manifest): the bundle's
  production manifest is regenerated against the latest worktree HEAD
  in this iteration.
- correction 8 (preflight hashes): added; pre-flight sha256 is printed
  for wrapper, installer, rollback, candidate, manifest, and reviewed
  release tree (counts + aggregate).
