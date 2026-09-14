# Production incident report -- 2026-09-14 (corrected, 5th iteration)

This is the corrected account of every production-side change since the
v0.1.0 apex bundle review cycle began.  It supersedes earlier drafts.

# Timeline summary (from oldest to newest)

| when | what | production-side change | recovery |
|---|---|---|---|
| 3rd-bundle review run | P1/1 regression test of original rollback-apex.sh | `/opt/dewata.online/deploy/caddy/Caddyfile.dewata` was overwritten with placeholder text from the regression-test fixture | snapshotted runtime was preserved at `/opt/dw-phase2/deploy/atomic/<ts>-pre-apex/Caddyfile.dewata.runtime`; `install -m 0644 runtime $PROD` re-installed it; `systemctl restart dewata-caddy` for the new caddyfile to take effect |
| 4th-bundle review / manual dry-run | operator invoked the install script with `DEWATA_DISPOSABLE_MODE` unset (defaulted to undefined / false), so the script took the production branch and called `systemctl restart dewata-caddy` after writing the candidate Caddyfile to disk | the running caddy service was restarted with the candidate caddyfile on disk (sha `4f06ce6f...`) | manual restore from worktree's `Caddyfile.dewata.runtime` (sha `adf3990c...`); `systemctl restart dewata-caddy` for the production baseline to take effect |
| 5th-bundle review / current iteration | disposable lifecycle runs only; no installer, rollback, restart, cleanup, or failure injection against `/opt/dewata.online` | NONE | n/a |

# Final state at end of this iteration

`/opt/dewata.online/deploy/caddy/Caddyfile.dewata`:
  - sha256 = `adf3990ccd4efaab427f71167799c99a3ddebcfc23ed468f95925c4adf11016a`
  - matches the reviewer baseline.  byte-identical to the snapshot
    runtime at every point since the recovery-restart above.

`systemctl show dewata-caddy -p MainPID`:
  - MainPID = `2143310`
  - this PID was set during the second recovery-restart above.
  - it has been unchanged across all of the current iteration's
    sub-tests (lifecycle test, install-script standalone dry-runs,
    mutex-mode dry-runs).

`https://api.dewata.org/health`:
  - HTTP/2 200.

`/opt/dewata.online/`:
  - no sentinels (no `.counters` files, no `CORRUPTED-by-...` files)
  - no snapshot dirs (the snapshot parent at `/opt/dewata.online/deploy/atomic/` is empty; all this iteration's snapshots live under `/tmp/dewata-lifecycle/atomic/`)

`https://dewata.org/`:
  - HTTP/2 522 (origin not reached).
  - the two conflicting apex A records (`54.149.79.189`, `34.216.117.25`)
    and the missing tunnel route are still pending operator dashboard
    cutover.  This iteration did not touch DNS.
  - this 522 is not caused by anything in this iteration; it is the
    pre-existing state from the third-bundle review.

# What changed in this iteration's deliverables

- installer (deploy/atomic/install-apex-candidate.sh): rewritten from
  scratch.  Now has mutually-exclusive DEWATA_DISPOSABLE_MODE /
  DEWATA_APPLY_PRODUCTION flags, mandatory env vars (no mutable
  defaults), bidirectional manifest verify, atomic publish, no-op check,
  do_restore with the correct step order (caddyfile on disk first,
  then release tree, then validate, then verify sha, then restart).

- rollback (deploy/atomic/rollback-apex.sh): rewritten.  Same env-var
  contract as the installer (mutually-exclusive flags, mandatory env
  vars, no-op check, snapshot dir required to exist as a directory,
  failure-injection hooks for testing).

- deploy wrapper (deploy/apex-deploy.sh): rewritten.  Requires
  DEWATA_APPLY_PRODUCTION=1, refuses to run a second time within 60
  seconds, captures the installer's actual snapshot path from stdout,
  passes every required DEWATA_* value explicitly via env -i.

- tests/disposable-systemctl.sh (NEW): a shim that the lifecycle test
  uses via DEWATA_SYSTEMCTL_CMD.  The installer's systemctl show /
  restart calls never reach the real production systemctl during
  testing.

- deploy/lifecycle-test/run-lifecycle-test.sh: rewritten as a
  positive + 10 negative sub-test suite.  Each negative scenario
  is a separate sub-test with its own failure-injection hook
  (DEWATA_FAKE_FAIL_AT_GATE={g3-post-publish,g4,g5,g6},
  DEWATA_FAKE_RECOVERY_VALIDATION_FAILURE, DEWATA_FAKE_RESTART_FAILURE).
  Pre- and post-snapshot production Caddyfile sha256 and dewata-caddy
  MainPID.  All sub-tests log to /tmp/dewata-lifecycle.install.out.<N>
  in addition to the canonical /tmp/dewata-lifecycle.install.out.

- deploy/atomic/RELEASES/v0.1.0-pre1.MANIFEST.txt: the actual deployment
  release manifest, included in the bundle.
