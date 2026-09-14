#!/usr/bin/env bash
# Wrapper end-to-end disposable mirror test -- evidence for the bundle
#
# Run from /opt/dw-phase2 with the wrapper, installer, shim, manifest
# all under that worktree.  Bypasses /opt/dewata.online entirely.
#
# Two scenarios:
#   A. Successful install: run an actual disposable caddy listener on
#      :18443 so the installer's G7 probes succeed.  Wrapper rc=0,
#      caddyfile sha changes to 4f06ce6f..., release tree published.
#   B. Intentional failure: skip the listener.  Wrapper exits with the
#      installer's actual non-zero rc.  Assertions check rc != 0,
#      do_restore ran (caddyfile restored to baseline), and we report
#      the wrapper's real exit code without a trailing `echo` masking it.
#
# In both scenarios we explicitly capture the wrapper's exit code in a
# file (not via $?) so the script cannot mask it with a trailing echo
# (the prior iteration had this bug).

set -eu

WORKTREE="/opt/dw-phase2"
SHIM="${WORKTREE}/tests/disposable-systemctl.sh"

# Disposable mirror setup
rm -rf /tmp/deploy-mirror
for d in caddy www atomic RELEASES; do
    mkdir -p /tmp/deploy-mirror/$d
done

# Reviewed tree (mirror of the worktree's reviewed source)
rm -rf /tmp/deploy-mirror/review
for d in caddy www; do mkdir -p /tmp/deploy-mirror/review/$d; done
cp "${WORKTREE}/deploy/caddy/Caddyfile.dewata.proposed" /tmp/deploy-mirror/review/caddy/Caddyfile.dewata.proposed
cp -r "${WORKTREE}/deploy/www/dewata-org/v0.1.0-pre1/." /tmp/deploy-mirror/review/www/

# Reviewed manifest for the disposable release tree
disp_manifest=/tmp/deploy-mirror/RELEASES/v0.1.0-pre1.MANIFEST.txt
: > "$disp_manifest"
( cd /tmp/deploy-mirror/review/www && find . -type f | sed 's|^./||' | sort ) | while IFS= read -r rel; do
    [ -z "$rel" ] && continue
    sum=$(sha256sum "/tmp/deploy-mirror/review/www/$rel" | cut -d' ' -f1)
    printf "%s  %s\n" "$sum" "$rel" >> "$disp_manifest"
done
cand_sha=$(sha256sum /tmp/deploy-mirror/review/caddy/Caddyfile.dewata.proposed | cut -d' ' -f1)
printf "%s  Caddyfile.dewata.proposed\n" "$cand_sha" >> "$disp_manifest"

# Initial Caddyfile = production baseline (operator "captures" this before running)
cp /opt/dewata.online/deploy/caddy/Caddyfile.dewata /tmp/deploy-mirror/caddy/Caddyfile.dewata
disp_baseline=$(sha256sum /tmp/deploy-mirror/caddy/Caddyfile.dewata | cut -d' ' -f1)

run_wrapper() {
    local scenario="$1"
    local out_file=/tmp/deploy-mirror/wrapper.${scenario}.out
    local rc_file=/tmp/deploy-mirror/wrapper.${scenario}.rc
    : > "$out_file"
    # DON'T redirect - capture rc explicitly via $? in a SINGLE command
    # chain.
    set +e
    env -i \
        PATH="${WORKTREE}/tests:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
        DEWATA_APPLY_PRODUCTION=1 \
        DEPLOY_INSTALLER="${WORKTREE}/deploy/atomic/install-apex-candidate.sh" \
        DEPLOY_ROLLBACK="${WORKTREE}/deploy/atomic/rollback-apex.sh" \
        DEPLOY_REVIEWED_MANIFEST="${WORKTREE}/deploy/atomic/RELEASES/v0.1.0-pre1.MANIFEST.txt" \
        DEPLOY_REVIEWED_RELEASE_SRC=/tmp/deploy-mirror/review/www \
        DEPLOY_REVIEWED_CANDIDATE=/tmp/deploy-mirror/review/caddy/Caddyfile.dewata.proposed \
        DEPLOY_PROD_CADDY=/tmp/deploy-mirror/caddy/Caddyfile.dewata \
        DEPLOY_PROD_RELEASE_DST=/tmp/deploy-mirror/www/dewata-org/v0.1.0-pre1 \
        DEPLOY_SNAPSHOT_PARENT=/tmp/deploy-mirror/atomic \
        DEPLOY_LISTENER_PORT=18443 \
        DEPLOY_SERVICE=dewata-caddy-dummy \
        DEWATA_FORCE_REINSTALL=1 \
        DEWATA_DEPLOYER_TEST_MODE=1 \
        DEWATA_SYSTEMCTL_CMD="$SHIM" \
        DEWATA_DISPOSABLE_SYSTEMCTL_LOG=/tmp/deploy-mirror/shim.log \
        DEWATA_DISPOSABLE_SYSTEMCTL_PIDFILE=/tmp/deploy-mirror/caddy.pid \
        DEWATA_DISPOSABLE_SYSTEMCTL_ACTIVE=/tmp/deploy-mirror/caddy.active \
        bash "${WORKTREE}/deploy/apex-deploy.sh" > "$out_file" 2>&1
    local rc=$?
    set -e
    echo "$rc" > "$rc_file"
    return 0   # intentionally don't propagate rc so set -e doesn't exit early
}

# ============================================================
echo "================================================================"
echo "SCENARIO A: successful install (listener up on :18443)"
echo "================================================================"

# Start a real disposable caddy listener on :18443.  This caddy is a
# child process launched by us (NOT by systemd, NOT by the wrapper).
# The wrapper's installer invokes the shim's systemctl show/restart
# commands, which record but do not touch the real systemd.
disposable_caddy_conf=/tmp/deploy-mirror/disposable-caddy.conf
mkdir -p /tmp/deploy-mirror/release-files
cat > "$disposable_caddy_conf" <<'CADDYEOF'
{
    admin off
    auto_https off
    log {
        level ERROR
    }
    # Use a single-host fallback so all dewata.org paths return 200
    # and the installer's probes succeed.
    :18443 {
        bind 127.0.0.1
        @bci host bci.dewata.org
        handle @bci {
            respond "service unavailable" 503
        }
        @protocol host protocol.dewata.org
        handle @protocol {
            respond "service unavailable" 503
        }
        respond "ok" 200
    }
}
CADDYEOF

/usr/bin/caddy run --config "$disposable_caddy_conf" --adapter caddyfile \
    > /tmp/deploy-mirror/disposable-caddy.log 2>&1 &
disposable_caddy_pid=$!
echo $disposable_caddy_pid > /tmp/deploy-mirror/disposable-caddy.pid
# Wait up to 10s for :18443 to be ready
ready=0
for _ in $(seq 1 30); do
    if ss -ltn 2>/dev/null | grep -q ":18443 "; then
        ready=1
        break
    fi
    sleep 0.3
done
if (( ready == 0 )); then
    echo "Scenario A: WARNING - could not confirm :18443 is listening; tests may fail"
fi

# Reset the Caddyfile to baseline BEFORE each wrapper run
cp /opt/dewata.online/deploy/caddy/Caddyfile.dewata /tmp/deploy-mirror/caddy/Caddyfile.dewata
rm -rf /tmp/deploy-mirror/www/dewata-org/v0.1.0-pre1 /tmp/deploy-mirror/atomic/*-pre-apex

# Run the wrapper.  Capture real exit code via the rc file.
run_wrapper A
wrapper_A_rc=$(cat /tmp/deploy-mirror/wrapper.A.rc)
if (( wrapper_A_rc == 0 )); then
    echo "  Scenario A: wrapper rc=$wrapper_A_rc (PASS)"
else
    echo "  Scenario A: wrapper rc=$wrapper_A_rc (FAIL)"
fi

# Assert: caddyfile sha changed to the candidate's sha (4f06ce6f...)
candidate_sha=$(sha256sum /opt/dw-phase2/deploy/caddy/Caddyfile.dewata.proposed | cut -d' ' -f1)
caddy_sha_A=$(sha256sum /tmp/deploy-mirror/caddy/Caddyfile.dewata | cut -d' ' -f1)
scenario_A_passed=1
if [[ "$caddy_sha_A" == "$candidate_sha" ]]; then
    echo "  Scenario A: caddyfile sha matches candidate: PASS"
else
    echo "  Scenario A: caddyfile sha FAIL (got $caddy_sha_A want $candidate_sha)"
    scenario_A_passed=0
fi

# Assert: release tree has 50 files (matches manifest)
if [[ -d /tmp/deploy-mirror/www/dewata-org/v0.1.0-pre1 ]]; then
    n_files=$(find /tmp/deploy-mirror/www/dewata-org/v0.1.0-pre1 -type f | wc -l)
    if (( n_files == 50 )); then
        echo "  Scenario A: release tree published with 50 files: PASS"
    else
        echo "  Scenario A: release tree published with $n_files files (expected 50): FAIL"
        scenario_A_passed=0
    fi
else
    echo "  Scenario A: release tree MISSING: FAIL"
    scenario_A_passed=0
fi

actual_snapshot_A=$(grep -o 'actual_snapshot_path=[^[:space:]]*' /tmp/deploy-mirror/wrapper.A.out | tail -1)
if [[ -n "$actual_snapshot_A" ]]; then
    echo "  Scenario A: actual_snapshot_path=${actual_snapshot_A#actual_snapshot_path=}"
fi

# Stop disposable caddy
kill "$disposable_caddy_pid" 2>/dev/null || true
sleep 1
disposable_caddy_pid=

# ============================================================
echo
echo "================================================================"
echo "SCENARIO B: intentional failure (DEWATA_FAKE_FAIL_AT_GATE=g6 fires post-restart)"
echo "================================================================"

# Reset Caddyfile to baseline + clear release tree
cp /opt/dewata.online/deploy/caddy/Caddyfile.dewata /tmp/deploy-mirror/caddy/Caddyfile.dewata
rm -rf /tmp/deploy-mirror/www/dewata-org/v0.1.0-pre1 /tmp/deploy-mirror/atomic/*-pre-apex

# Inject a synthetic failure at G6 (post-restart).  The install will
# fail at the restart step (which never actually happens because the
# disposable shim records the call but the test mode skips the real
# listener probe).  do_restore runs because of the ERR trap.  This is
# the user's evidence that the wrapper propagates the installer's real
# exit code without masking it with a trailing echo.
run_wrapper_with_failure() {
    local out_file=/tmp/deploy-mirror/wrapper.B.out
    local rc_file=/tmp/deploy-mirror/wrapper.B.rc
    : > "$out_file"
    set +e
    # Scenario B: wrapper self-test under DEPLOYER_TEST_MODE=1 with
    # DEWATA_FAKE_FAIL_AT_GATE=g5 injected via the wrapper's test-var
    # pass-through.  G5 is BEFORE the restart, so the install fails at
    # G5 and do_restore runs.  DEWATA_FAKE_VALIDATE_FAILURE=1 fires at
    # G5 AND at the do_restore's step 3 (validate restored Caddyfile),
    # producing AUTO-RESTORE INCOMPLETE.
    env -i \
        PATH="${WORKTREE}/tests:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
        DEPLOY_INSTALLER="${WORKTREE}/deploy/atomic/install-apex-candidate.sh" \
        DEPLOY_ROLLBACK="${WORKTREE}/deploy/atomic/rollback-apex.sh" \
        DEPLOY_REVIEWED_MANIFEST="${WORKTREE}/deploy/atomic/RELEASES/v0.1.0-pre1.MANIFEST.txt" \
        DEPLOY_REVIEWED_RELEASE_SRC=/tmp/deploy-mirror/review/www \
        DEPLOY_REVIEWED_CANDIDATE=/tmp/deploy-mirror/review/caddy/Caddyfile.dewata.proposed \
        DEPLOY_PROD_CADDY=/tmp/deploy-mirror/caddy/Caddyfile.dewata \
        DEPLOY_PROD_RELEASE_DST=/tmp/deploy-mirror/www/dewata-org/v0.1.0-pre1 \
        DEPLOY_SNAPSHOT_PARENT=/tmp/deploy-mirror/atomic \
        DEPLOY_LISTENER_PORT=18443 \
        DEPLOY_SERVICE=dewata-caddy-dummy \
        DEWATA_FORCE_REINSTALL=1 \
        DEWATA_DEPLOYER_TEST_MODE=1 \
        DEWATA_FAKE_FAIL_AT_GATE=g5 \
        DEWATA_FAKE_VALIDATE_FAILURE=1 \
        DEWATA_FAKE_VALIDATE_FAILURE_GATES=g5,restore \
        DEWATA_USE_DISPOSABLE_VALIDATE=1 \
        DEWATA_VALIDATE_CMD="${WORKTREE}/tests/disposable-validate.sh" \
        DEWATA_VALIDATE_LOG=/tmp/deploy-mirror/validate.log \
        DEWATA_SYSTEMCTL_CMD="$SHIM" \
        DEWATA_DISPOSABLE_SYSTEMCTL_LOG=/tmp/deploy-mirror/shim.log \
        DEWATA_DISPOSABLE_SYSTEMCTL_PIDFILE=/tmp/deploy-mirror/caddy.pid \
        DEWATA_DISPOSABLE_SYSTEMCTL_ACTIVE=/tmp/deploy-mirror/caddy.active \
        DEWATA_DISPOSABLE_SERVICE_MODE=restart \
        bash "${WORKTREE}/deploy/apex-deploy.sh" > "$out_file" 2>&1
    local rc=$?
    set -e
    echo "$rc" > "$rc_file"
    return 0
}

run_wrapper_with_failure
wrapper_B_rc=$(cat /tmp/deploy-mirror/wrapper.B.rc)
if (( wrapper_B_rc != 0 )); then
    echo "  Scenario B: wrapper rc=$wrapper_B_rc (PASS - failed closed as expected)"
else
    echo "  Scenario B: wrapper rc=$wrapper_B_rc (FAIL - expected non-zero)"
fi

# Assert: caddyfile restored to baseline (do_restore ran)
caddy_sha_B=$(sha256sum /tmp/deploy-mirror/caddy/Caddyfile.dewata | cut -d' ' -f1)
scenario_B_passed=1
if [[ "$caddy_sha_B" == "$disp_baseline" ]]; then
    echo "  Scenario B: caddyfile restored to baseline: PASS"
else
    echo "  Scenario B: caddyfile NOT restored (got $caddy_sha_B want $disp_baseline): FAIL"
    scenario_B_passed=0
fi

# Assert: do_restore ran with INCOMPLETE (validator failed during
# recovery AND during restore-validation).
if grep -E "AUTO-RESTORE INCOMPLETE" /tmp/deploy-mirror/wrapper.B.out > /dev/null; then
    echo "  Scenario B: installer logged AUTO-RESTORE INCOMPLETE: PASS"
else
    echo "  Scenario B: AUTO-RESTORE INCOMPLETE missing: FAIL"
    scenario_B_passed=0
fi

# Composite summary
echo
echo "================================================================"
echo "Composite test summary"
echo "================================================================"
echo "  Scenario A (install succeeds): wrapper_rc=$wrapper_A_rc (expect 0)"
echo "    caddyfile sha: $caddy_sha_A (expect $candidate_sha)"
echo "  Scenario B (install fails closed): wrapper_rc=$wrapper_B_rc (expect non-zero)"
echo "    caddyfile sha: $caddy_sha_B (expect $disp_baseline)"

# Final verdict
if (( wrapper_A_rc == 0 )) && (( wrapper_B_rc != 0 )) && \
   (( scenario_A_passed == 1 )) && (( scenario_B_passed == 1 )); then
    echo "TEST RESULT: PASS"
    exit 0
else
    echo "TEST RESULT: FAIL"
    exit 1
fi
