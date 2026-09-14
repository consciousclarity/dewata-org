# Production incident report -- 2026-09-14 (corrected)

# Summary
# -------
# During the third-bundle review of this deployment, a regression test
# in this session produced a temporary production mutation that was
# fully recovered within the same session.  This report is the
# corrected, expanded account of that incident.

# What was created
# ----------------
#   /opt/dewata.online/deploy/caddy/Caddyfile.dewata.CORRUPTED-by-hermes-regression-test-2026-09-14
#
#   (this sentinel filename was chosen deliberately as a marker that
#    a regression test had run; the file was created during the test
#    and removed in the next turn)

# What the corruption actually was
# --------------------------------
# The P1/1 regression test of rollback-apex.sh ran the production-default
# rollback script against a fake snapshot directory.  At that point,
# the rollback script had no env-var override for the production path,
# so it:
#
#   1. Moved /opt/dewata.online/deploy/caddy/Caddyfile.dewata aside
#      into the fake snapshot location (a write to /opt/dewata.online/).
#   2. Overwrote /opt/dewata.online/deploy/caddy/Caddyfile.dewata
#      with the fixture text 'this is not a valid caddyfile'.
#   3. Created the sentinel file noted above.
#
# The session-detector was `bash -n /opt/dewata.online/deploy/caddy/Caddyfile.dewata`
# which returned rc=1 with the literal fixture text on the first line.
# `caddy validate` against the production Caddyfile also returned
# rc=1 with the same fixture text in the error message.

# What was done to recover
# ------------------------
#   1. Re-installed the runtime snapshot Caddyfile:
#        install -m 0644 /opt/dw-phase2/deploy/caddy/Caddyfile.dewata.runtime \
#                    /opt/dewata.online/deploy/caddy/Caddyfile.dewata
#   2. Restarted the production caddy service:
#        systemctl restart dewata-caddy
#      This was necessary because the live caddy process was still
#      running the prior config (with the old sha) -- a Caddyfile
#      change on disk does not auto-reload until caddy is signaled.
#   3. Verified the production caddyfile sha256 matched the reviewer-
#      confirmed baseline:
#        sha256sum /opt/dewata.online/deploy/caddy/Caddyfile.dewata
#        # adf3990ccd4efaab427f71167799c99a3ddebcfc23ed468f95925c4adf11016a
#   4. Verified api.dewata.org/health returned 200.
#   5. Verified find /opt/dewata.online -name '*CORRUPTED*' returned empty.
#   6. Removed the sentinel file:
#        rm /opt/dewata.online/deploy/caddy/Caddyfile.dewata.CORRUPTED-by-hermes-regression-test-2026-09-14

# Second incident -- a fourth-bundle review trace
# -------------------------------------------------
# During this fourth-bundle review, I ran the install script against
# /opt/dewata.online paths without DEWATA_TEST_MODE=1 set explicitly
# (it was unset in the manual invocation).  The install took the
# production restart branch and called `systemctl restart dewata-caddy`
# while the candidate Caddyfile content (4f06ce6f...) differed from
# the production baseline (adf3990c...).  This restarted the live
# production caddy with the new candidate config, even though the
# DNS cutover had not happened yet.  The candidate did not break
# anything functionally, but it is a live configuration drift
# against the reviewer-confirmed baseline.
#
# I noticed the drift on the NEXT iteration of the test (when checking
# MainPID).  The Caddyfile content was still in the candidate state
# (sha 4f06ce6f...).  I restored the production Caddyfile from the
# worktree runtime snapshot and restarted dewata-caddy to make the
# restore take effect.
#
# After this incident, I added the production-path guard to both
# install-apex-candidate.sh and rollback-apex.sh: a run against
# /opt/dewata.online, /etc/caddy, or /var/lib/dewata paths WITHOUT
# DEWATA_TEST_MODE=1 set fails with rc=4 before any destructive
# operation.  This is the closed-default behavior we want: a missed
# env var fails closed rather than drifting the production caddy.

# Hardening that was added in response to these incidents
# ------------------------------------------------------
#   1. install-apex-candidate.sh and rollback-apex.sh now REFUSE to
#      run if their DEWATA_PROD_CADDY (or equivalent) points at a
#      known production path AND DEWATA_TEST_MODE is not set to "1".
#   2. The G6 restart branch in the install script now ONLY fires
#      when DEWATA_TEST_MODE != 1 AND $PROD is a known production
#      path.  For disposable installs the restart is skipped (no-op
#      for the host's service).
#   3. The G7 HTTP probe block in the install script now ONLY fires
#      when DEWATA_TEST_MODE != 1 AND $PROD is a known production
#      path.  For disposable installs the lifecycle test owns the
#      probes.
#   4. The lifecycle test driver (run-lifecycle-test.sh) now uses a
#      require_disposable() wrapper that records a SUITE_FAILED if
#      launch_disposable_caddy fails, so a failed disposable startup
#      fails the test rather than producing silent bogus probe results.

# Current state (verified 2026-09-14)
# -----------------------------------
# /opt/dewata.online/deploy/caddy/Caddyfile.dewata:
#     sha256 = adf3990ccd4efaab427f71167799c99a3ddebcfc23ed468f95925c4adf11016a
#     size   = 1972 bytes
#     mtime  = 2026-09-14T10:04:42Z (unchanged since earlier restore)
#
# dewata-caddy.service:
#     MainPID  = 2143310 (started after recovery restart)
#     ActiveState = active
#
# /opt/dewata.online/deploy/caddy/ contents:
#     Caddyfile.dewata   (production Caddyfile, reviewer baseline)
#     dewata.vhost        (untouched)
#     pki/                (untouched)
#
# No sentinels, no CORRUPTED files, no .counters files anywhere in
# /opt/dewata.online.  No /opt/dewata.online/deploy/www/dewata-org/
# subdirectory exists (we never published a release tree to production).
#
# https://api.dewata.org/health: HTTP 200
# https://dewata.org/:          HTTP 522 (expected; apex tunnel not yet routed)
