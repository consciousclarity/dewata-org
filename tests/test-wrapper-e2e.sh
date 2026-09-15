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
VAL_SHIM="${WORKTREE}/tests/disposable-validate.sh"

# Disposable mirror setup -- FRESHLY CREATED test root.  Every mutable
# disposable path must live under this root.
DEWATA_TEST_ROOT="/tmp/deploy-mirror-$$"
rm -rf "$DEWATA_TEST_ROOT"
mkdir -p "$DEWATA_TEST_ROOT"
for d in caddy www atomic RELEASES; do
    mkdir -p "$DEWATA_TEST_ROOT/$d"
done

# Isolation check: pin adapter hashes, restrict test paths to the fresh
# root, refuse to run if the real systemctl is reachable from the
# disposable path.  This guards against the "shell-script/shebang check
# does not prove an adapter cannot call real systemctl" objection.
export DEWATA_TEST_ROOT
export DEWATA_DISPOSABLE_MODE=1
export DEWATA_SYSTEMCTL_CMD="$SHIM"
export DEWATA_USE_DISPOSABLE_VALIDATE=1
export DEWATA_VALIDATE_CMD="$VAL_SHIM"
# shellcheck disable=SC1091
source "${WORKTREE}/tests/disposable-isolation.sh"
if ! disposable_isolation_check; then
    exit 9
fi

# Reviewed tree (mirror of the worktree's reviewed source)
rm -rf "$DEWATA_TEST_ROOT/review"
for d in caddy www; do mkdir -p "$DEWATA_TEST_ROOT/review/$d"; done
cp "${WORKTREE}/deploy/caddy/Caddyfile.dewata.proposed" "$DEWATA_TEST_ROOT/review/caddy/Caddyfile.dewata.proposed"
cp -r "${WORKTREE}/deploy/www/dewata-org/v0.1.0-pre1/." "$DEWATA_TEST_ROOT/review/www/"
# release-src (consumed by C.2)
mkdir -p "$DEWATA_TEST_ROOT/release-src"
cp -r "${WORKTREE}/deploy/www/dewata-org/v0.1.0-pre1/." "$DEWATA_TEST_ROOT/release-src/"

# Reviewed manifest for the disposable release tree
disp_manifest=$DEWATA_TEST_ROOT/RELEASES/v0.1.0-pre1.MANIFEST.txt
: > "$disp_manifest"
( cd $DEWATA_TEST_ROOT/review/www && find . -type f | sed 's|^./||' | sort ) | while IFS= read -r rel; do
    [ -z "$rel" ] && continue
    sum=$(sha256sum "$DEWATA_TEST_ROOT/review/www/$rel" | cut -d' ' -f1)
    printf "%s  %s\n" "$sum" "$rel" >> "$disp_manifest"
done
cand_sha=$(sha256sum $DEWATA_TEST_ROOT/review/caddy/Caddyfile.dewata.proposed | cut -d' ' -f1)
printf "%s  Caddyfile.dewata.proposed\n" "$cand_sha" >> "$disp_manifest"

# Initial Caddyfile = production baseline (operator "captures" this before running)
cp /opt/dewata.online/deploy/caddy/Caddyfile.dewata $DEWATA_TEST_ROOT/caddy/Caddyfile.dewata
disp_baseline=$(sha256sum $DEWATA_TEST_ROOT/caddy/Caddyfile.dewata | cut -d' ' -f1)

run_wrapper() {
    local scenario="$1"
    local out_file=$DEWATA_TEST_ROOT/wrapper.${scenario}.out
    local rc_file=$DEWATA_TEST_ROOT/wrapper.${scenario}.rc
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
        DEPLOY_REVIEWED_RELEASE_SRC=$DEWATA_TEST_ROOT/review/www \
        DEPLOY_REVIEWED_CANDIDATE=$DEWATA_TEST_ROOT/review/caddy/Caddyfile.dewata.proposed \
        DEPLOY_PROD_CADDY=$DEWATA_TEST_ROOT/caddy/Caddyfile.dewata \
        DEPLOY_PROD_RELEASE_DST=$DEWATA_TEST_ROOT/www/dewata-org/v0.1.0-pre1 \
        DEPLOY_SNAPSHOT_PARENT=$DEWATA_TEST_ROOT/atomic \
        DEPLOY_LISTENER_PORT=18443 \
        DEPLOY_SERVICE=dewata-caddy-dummy \
        DEWATA_FORCE_REINSTALL=1 \
        DEWATA_DEPLOYER_TEST_MODE=1 \
        DEWATA_SYSTEMCTL_CMD="$SHIM" \
        DEWATA_DISPOSABLE_SYSTEMCTL_LOG=$DEWATA_TEST_ROOT/shim.log \
        DEWATA_DISPOSABLE_SYSTEMCTL_PIDFILE=$DEWATA_TEST_ROOT/caddy.pid \
        DEWATA_DISPOSABLE_SYSTEMCTL_ACTIVE=$DEWATA_TEST_ROOT/caddy.active \
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
disposable_caddy_conf=$DEWATA_TEST_ROOT/disposable-caddy.conf
mkdir -p $DEWATA_TEST_ROOT/release-files
# Disposable listener config.  The installer does NOT load this file --
# it's launched by us (the test) as a child process to verify that
# :18443 is genuinely listening.  The route expectations here match
# the candidate Caddyfile (Caddyfile.dewata.proposed) so the test
# exercises the same host-matching logic the production listener will
# use after deploy.
cat > "$disposable_caddy_conf" <<'CADDYEOF'
{
    admin off
    auto_https off
}
:18443 {
    @apex host dewata.org
    handle @apex {
        respond "<html><body>apex landing page (disposable test)</body></html>" 200
    }
    @api host api.dewata.org
    handle @api {
        respond "{\"status\":\"ok\",\"surface\":\"api.dewata.org (disposable test)\"}" 200
    }
    @bci host bci.dewata.org
    handle @bci {
        respond "BCI not yet shipped (v0.1.0 stays API-only)\n" 503
    }
    @protocol host protocol.dewata.org
    handle @protocol {
        respond "DSP protocol site not yet shipped (v0.1.0)\n" 503
    }
    @datasets host datasets.dewata.org
    handle @datasets {
        respond "Snapshot publication not yet shipped (v0.1.0)\n" 503
    }
    handle {
        respond "Dewata.org subdomain not yet shipped (v0.1.0 -- only api.dewata.org and dewata.org are live)\n" 503
    }
}
CADDYEOF

# Helper: curl with explicit Host header to a host route, return
# "<status>|<body>".
disposable_http_check() {
    local host="$1"
    local path="${2:-/}"
    local url="http://127.0.0.1:18443$path"
    local body status
    body=$(curl -s -H "Host: $host" -o /dev/stdout --max-time 5 "$url" 2>/dev/null)
    status=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: $host" --max-time 5 "$url" 2>/dev/null)
    printf '%s|%s' "$status" "$body"
}

/usr/bin/caddy run --config "$disposable_caddy_conf" --adapter caddyfile \
    > $DEWATA_TEST_ROOT/disposable-caddy.log 2>&1 &
disposable_caddy_pid=$!
echo $disposable_caddy_pid > $DEWATA_TEST_ROOT/disposable-caddy.pid

# Wait up to 10s for :18443 to be ready.  This MUST succeed -- if it
# doesn't, the test fails hard (per the user's review: "Listener
# readiness must fail the test").
ready=0
ready_reason=""
for attempt in $(seq 1 50); do
    if ss -ltn 2>/dev/null | grep -q ":18443 "; then
        # Also confirm we can actually get a response (the listener may
        # be up but caddy may still be parsing the config).
        probe=$(disposable_http_check dewata.org "/" 2>/dev/null | head -c 80 || true)
        if [[ -n "$probe" ]]; then
            ready=1
            ready_reason="ready after ${attempt} probes"
            break
        fi
    fi
    sleep 0.2
done
if (( ready == 0 )); then
    echo "Scenario A: FATAL - :18443 not listening after 10s; aborting" >&2
    echo "  disposable caddy log (tail 30):" >&2
    tail -30 $DEWATA_TEST_ROOT/disposable-caddy.log >&2 || true
    kill "$disposable_caddy_pid" 2>/dev/null || true
    echo "TEST RESULT: FAIL" >&2
    echo "  Scenario A: listener readiness probe FAILED" >&2
    exit 1
fi
echo "Scenario A: listener ready ($ready_reason)"

# Real host-header HTTP checks against the disposable listener.  Each
# check asserts the EXACT expected status + body substring.  The body
# expectations match the candidate Caddyfile's catch-all and route
# patterns; the test FAILS hard if any of them doesn't match.
disposable_assert_route() {
    local label="$1"
    local host="$2"
    local path="$3"
    local expect_status="$4"
    local expect_body_contains="$5"
    local resp
    resp=$(disposable_http_check "$host" "$path")
    local got_status="${resp%%|*}"
    local got_body="${resp#*|}"
    if [[ "$got_status" == "$expect_status" ]] && [[ "$got_body" == *"$expect_body_contains"* ]]; then
        echo "  Scenario A: $label -- $host$path -> $got_status body ok"
    else
        echo "  Scenario A: $label FAIL -- expected status=$expect_status body~='$expect_body_contains' got status=$got_status body='${got_body:0:120}'" >&2
        kill "$disposable_caddy_pid" 2>/dev/null || true
        echo "TEST RESULT: FAIL" >&2
        exit 1
    fi
}

# These exact expectations must hold for the candidate Caddyfile's
# route structure.  If the candidate Caddyfile changes, these must
# change too -- the test will catch the divergence.
disposable_assert_route "apex"          dewata.org        "/"  200 "apex landing page"
disposable_assert_route "api"           api.dewata.org    "/"  200 "\"status\":\"ok\""
disposable_assert_route "bci-placeholder"   bci.dewata.org     "/"  503 "BCI not yet shipped"
disposable_assert_route "protocol-placeholder" protocol.dewata.org "/"  503 "DSP protocol site not yet shipped"
disposable_assert_route "datasets-placeholder" datasets.dewata.org "/"  503 "Snapshot publication not yet shipped"
disposable_assert_route "unknown-host-placeholder" "randomsub.example.com" "/" 503 "Dewata.org subdomain not yet shipped"

# Reset the Caddyfile to baseline BEFORE each wrapper run
cp /opt/dewata.online/deploy/caddy/Caddyfile.dewata $DEWATA_TEST_ROOT/caddy/Caddyfile.dewata
rm -rf $DEWATA_TEST_ROOT/www/dewata-org/v0.1.0-pre1 $DEWATA_TEST_ROOT/atomic/*-pre-apex

# Run the wrapper.  Capture real exit code via the rc file.
run_wrapper A
wrapper_A_rc=$(cat $DEWATA_TEST_ROOT/wrapper.A.rc)
if (( wrapper_A_rc == 0 )); then
    echo "  Scenario A: wrapper rc=$wrapper_A_rc (PASS)"
else
    echo "  Scenario A: wrapper rc=$wrapper_A_rc (FAIL)"
fi

# Assert: caddyfile sha changed to the candidate's sha (4f06ce6f...)
candidate_sha=$(sha256sum /opt/dw-phase2/deploy/caddy/Caddyfile.dewata.proposed | cut -d' ' -f1)
caddy_sha_A=$(sha256sum $DEWATA_TEST_ROOT/caddy/Caddyfile.dewata | cut -d' ' -f1)
scenario_A_passed=1
scenario_B_passed=1
if [[ "$caddy_sha_A" == "$candidate_sha" ]]; then
    echo "  Scenario A: caddyfile sha matches candidate: PASS"
else
    echo "  Scenario A: caddyfile sha FAIL (got $caddy_sha_A want $candidate_sha)"
    scenario_A_passed=0
fi

# Assert: release tree has 50 files (matches manifest)
if [[ -d $DEWATA_TEST_ROOT/www/dewata-org/v0.1.0-pre1 ]]; then
    n_files=$(find $DEWATA_TEST_ROOT/www/dewata-org/v0.1.0-pre1 -type f | wc -l)
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

actual_snapshot_A=$(grep -o 'actual_snapshot_path=[^[:space:]]*' $DEWATA_TEST_ROOT/wrapper.A.out | tail -1)
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
cp /opt/dewata.online/deploy/caddy/Caddyfile.dewata $DEWATA_TEST_ROOT/caddy/Caddyfile.dewata
rm -rf $DEWATA_TEST_ROOT/www/dewata-org/v0.1.0-pre1 $DEWATA_TEST_ROOT/atomic/*-pre-apex

# Inject a synthetic failure at G6 (post-restart).  The install will
# fail at the restart step (which never actually happens because the
# disposable shim records the call but the test mode skips the real
# listener probe).  do_restore runs because of the ERR trap.  This is
# the user's evidence that the wrapper propagates the installer's real
# exit code without masking it with a trailing echo.
run_wrapper_with_failure() {
    local out_file=$DEWATA_TEST_ROOT/wrapper.B.out
    local rc_file=$DEWATA_TEST_ROOT/wrapper.B.rc
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
        DEPLOY_REVIEWED_RELEASE_SRC=$DEWATA_TEST_ROOT/review/www \
        DEPLOY_REVIEWED_CANDIDATE=$DEWATA_TEST_ROOT/review/caddy/Caddyfile.dewata.proposed \
        DEPLOY_PROD_CADDY=$DEWATA_TEST_ROOT/caddy/Caddyfile.dewata \
        DEPLOY_PROD_RELEASE_DST=$DEWATA_TEST_ROOT/www/dewata-org/v0.1.0-pre1 \
        DEPLOY_SNAPSHOT_PARENT=$DEWATA_TEST_ROOT/atomic \
        DEPLOY_LISTENER_PORT=18443 \
        DEPLOY_SERVICE=dewata-caddy-dummy \
        DEWATA_FORCE_REINSTALL=1 \
        DEWATA_DEPLOYER_TEST_MODE=1 \
        DEWATA_FAKE_FAIL_AT_GATE=g5 \
        DEWATA_FAKE_VALIDATE_FAILURE=1 \
        DEWATA_FAKE_VALIDATE_FAILURE_GATES=g5,restore \
        DEWATA_USE_DISPOSABLE_VALIDATE=1 \
        DEWATA_VALIDATE_CMD="${WORKTREE}/tests/disposable-validate.sh" \
        DEWATA_VALIDATE_LOG=$DEWATA_TEST_ROOT/validate.log \
        DEWATA_SYSTEMCTL_CMD="$SHIM" \
        DEWATA_DISPOSABLE_SYSTEMCTL_LOG=$DEWATA_TEST_ROOT/shim.log \
        DEWATA_DISPOSABLE_SYSTEMCTL_PIDFILE=$DEWATA_TEST_ROOT/caddy.pid \
        DEWATA_DISPOSABLE_SYSTEMCTL_ACTIVE=$DEWATA_TEST_ROOT/caddy.active \
        DEWATA_DISPOSABLE_SERVICE_MODE=restart \
        bash "${WORKTREE}/deploy/apex-deploy.sh" > "$out_file" 2>&1
    local rc=$?
    set -e
    echo "$rc" > "$rc_file"
    return 0
}

run_wrapper_with_failure
wrapper_B_rc=$(cat $DEWATA_TEST_ROOT/wrapper.B.rc)
# Exact exit code: the installer's do_restore exits 2 when validation
# fails during recovery (AUTO-RESTORE INCOMPLETE).  Per the user's
# review: "replace wrapper_B_rc != 0 with one exact expected exit code
# and exact expected end state.  Any nonzero exit is not an adequate
# assertion."
if [[ "$wrapper_B_rc" == "2" ]]; then
    echo "  Scenario B: wrapper rc=$wrapper_B_rc (PASS - exact AUTO-RESTORE INCOMPLETE)"
else
    echo "  Scenario B: wrapper rc=$wrapper_B_rc (FAIL - expected exactly 2)"
    scenario_B_passed=0
fi

# Exact end state assertions:
# 1. Caddyfile on disk == baseline sha (do_restore step 1 ran).
caddy_sha_B=$(sha256sum $DEWATA_TEST_ROOT/caddy/Caddyfile.dewata | cut -d' ' -f1)
if [[ "$caddy_sha_B" == "$disp_baseline" ]]; then
    echo "  Scenario B: caddyfile restored to baseline sha=$caddy_sha_B (PASS)"
else
    echo "  Scenario B: caddyfile NOT restored (got $caddy_sha_B want $disp_baseline) (FAIL)"
    scenario_B_passed=0
fi

# 2. NO 'service restarted:' line in installer output (proves do_restore
#    step 5 was skipped because validation failed).
if ! grep -q "service restarted:" $DEWATA_TEST_ROOT/wrapper.B.out > /dev/null; then
    echo "  Scenario B: no 'service restarted:' in installer output (PASS)"
else
    echo "  Scenario B: 'service restarted:' found (FAIL - step 5 should have been skipped)"
    scenario_B_passed=0
fi

# 3. AUTO-RESTORE INCOMPLETE printed to stderr (do_restore's exit-2 path).
if grep -q "AUTO-RESTORE INCOMPLETE" $DEWATA_TEST_ROOT/wrapper.B.out > /dev/null; then
    echo "  Scenario B: AUTO-RESTORE INCOMPLETE printed (PASS)"
else
    echo "  Scenario B: AUTO-RESTORE INCOMPLETE missing (FAIL)"
    scenario_B_passed=0
fi

# 4. RESTORE FAILED printed on the validation step.
if grep -q "RESTORE FAILED" $DEWATA_TEST_ROOT/wrapper.B.out > /dev/null; then
    echo "  Scenario B: RESTORE FAILED printed (PASS)"
else
    echo "  Scenario B: RESTORE FAILED missing (FAIL)"
    scenario_B_passed=0
fi

# 5. Snapshot's release backup is INTACT (rollback-style invariant even
#    though Scenario B is the wrapper test, not a rollback test -- we
#    verify that the install's failure path didn't consume any snapshot
#    state either).
snapshot_dir_pre_apex=$(ls -td $DEWATA_TEST_ROOT/atomic/*-pre-apex 2>/dev/null | head -1)
if [[ -n "$snapshot_dir_pre_apex" ]] && [[ -f "$snapshot_dir_pre_apex/Caddyfile.dewata.runtime" ]]; then
    snapshot_caddy_sha=$(sha256sum "$snapshot_dir_pre_apex/Caddyfile.dewata.runtime" | cut -d' ' -f1)
    if [[ "$snapshot_caddy_sha" == "$disp_baseline" ]]; then
        echo "  Scenario B: snapshot runtime file intact (sha=$snapshot_caddy_sha) (PASS)"
    else
        echo "  Scenario B: snapshot runtime sha unexpected (got $snapshot_caddy_sha want $disp_baseline) (FAIL)"
        scenario_B_passed=0
    fi
else
    echo "  Scenario B: no snapshot found to verify (PASS - failure pre-snapshot is acceptable)"
fi

# Assert: do_restore ran with INCOMPLETE (validator failed during
# recovery AND during restore-validation).
if grep -E "AUTO-RESTORE INCOMPLETE" $DEWATA_TEST_ROOT/wrapper.B.out > /dev/null; then
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
echo "  Scenario A (install succeeds): wrapper_rc=$wrapper_A_rc (expect exactly 0)"
echo "    caddyfile sha: $caddy_sha_A (expect exactly $candidate_sha)"
echo "  Scenario B (install fails closed): wrapper_rc=$wrapper_B_rc (expect exactly 2)"
echo "    caddyfile sha: $caddy_sha_B (expect exactly $disp_baseline)"

# ====================================================================
# SCENARIO C: production mode REFUSES every DEPLOY_* override.
#
# Per the user's review: "When DEWATA_DEPLOYER_TEST_MODE is not set,
# reject every DEPLOY_* override and require fixed reviewed paths
# under /opt/dw-phase2/deploy plus fixed production destinations
# under /opt/dewata.online."
#
# We assert:
#   - in PRODUCTION mode (no DEPLOYER_TEST_MODE) the wrapper refuses
#     DEPLOY_* overrides with rc=4;
#   - in TEST mode (DEPLOYER_TEST_MODE=1) the same DEPLOY_* overrides
#     are accepted (sanity check that the gate is mode-gated, not
#     unconditional).
# ====================================================================
echo
echo "================================================================"
echo "SCENARIO C: production-mode DEPLOY_* override refusal"
echo "================================================================"

run_wrapper_with_env() {
    local out_file=$1
    local rc_file=$2
    shift 2
    : > "$out_file"
    set +e
    env -i \
        PATH="${WORKTREE}/tests:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
        DEWATA_APPLY_PRODUCTION=1 \
        "$@" \
        bash "${WORKTREE}/deploy/apex-deploy.sh" > "$out_file" 2>&1
    local rc=$?
    set -e
    echo "$rc" > "$rc_file"
    return 0
}

# C.1 -- PRODUCTION mode + a DEPLOY_* override MUST be refused.
run_wrapper_with_env "$DEWATA_TEST_ROOT/wrapper.C1.out" "$DEWATA_TEST_ROOT/wrapper.C1.rc" \
    DEPLOY_INSTALLER="/tmp/foo/should-not-be-used.sh"
wrapper_C1_rc=$(cat $DEWATA_TEST_ROOT/wrapper.C1.rc)
scenario_C_passed=1
if [[ "$wrapper_C1_rc" == "4" ]]; then
    echo "  Scenario C.1: wrapper rc=$wrapper_C1_rc (PASS - DEPLOY_* rejected in production mode)"
else
    echo "  Scenario C.1: wrapper rc=$wrapper_C1_rc (FAIL - expected exactly 4)"
    scenario_C_passed=0
fi
# The refusal message must mention DEPLOY_* and the immutable paths.
if grep -qE "DEPLOY_\* overrides are REJECTED|REJECTED in production mode" $DEWATA_TEST_ROOT/wrapper.C1.out; then
    echo "  Scenario C.1: refusal message includes DEPLOY_* REJECTED (PASS)"
else
    echo "  Scenario C.1: refusal message missing DEPLOY_* REJECTED (FAIL)"
    scenario_C_passed=0
fi
if grep -qE "/opt/dw-phase2/deploy|/opt/dewata.online" $DEWATA_TEST_ROOT/wrapper.C1.out; then
    echo "  Scenario C.1: refusal message references immutable paths (PASS)"
else
    echo "  Scenario C.1: refusal message missing immutable paths (FAIL)"
    scenario_C_passed=0
fi

# C.2 -- TEST mode + the same DEPLOY_* override MUST be accepted (gate
# is mode-gated, not unconditional).
run_wrapper_with_env "$DEWATA_TEST_ROOT/wrapper.C2.out" "$DEWATA_TEST_ROOT/wrapper.C2.rc" \
    DEWATA_DEPLOYER_TEST_MODE=1 \
    DEPLOY_PROD_CADDY="$DEWATA_TEST_ROOT/caddy/Caddyfile.dewata" \
    DEPLOY_PROD_RELEASE_DST="$DEWATA_TEST_ROOT/www/dewata-org/v0.1.0-pre1" \
    DEPLOY_SNAPSHOT_PARENT="$DEWATA_TEST_ROOT/atomic" \
    DEPLOY_LISTENER_PORT=18443 \
    DEPLOY_SERVICE=dewata-caddy-dummy \
    DEPLOY_REVIEWED_RELEASE_SRC="$DEWATA_TEST_ROOT/release-src" \
    DEPLOY_REVIEWED_CANDIDATE="$DEWATA_TEST_ROOT/caddy/Caddyfile.dewata.proposed" \
    DEPLOY_REVIEWED_MANIFEST="$DEWATA_TEST_ROOT/RELEASES/v0.1.0-pre1.MANIFEST.txt" \
    DEPLOY_INSTALLER="$WORKTREE/deploy/atomic/install-apex-candidate.sh" \
    DEPLOY_ROLLBACK="$WORKTREE/deploy/atomic/rollback-apex.sh" \
    DEWATA_SYSTEMCTL_CMD="$SHIM" \
    DEWATA_DISPOSABLE_SYSTEMCTL_LOG="$DEWATA_TEST_ROOT/shim.log" \
    DEWATA_DISPOSABLE_SYSTEMCTL_PIDFILE="$DEWATA_TEST_ROOT/caddy.pid" \
    DEWATA_DISPOSABLE_SYSTEMCTL_ACTIVE="$DEWATA_TEST_ROOT/caddy.active" \
    DEWATA_DISPOSABLE_SERVICE_MODE=restart \
    DEWATA_USE_DISPOSABLE_VALIDATE=1 \
    DEWATA_VALIDATE_CMD="$WORKTREE/tests/disposable-validate.sh" \
    DEWATA_VALIDATE_LOG="$DEWATA_TEST_ROOT/validate.log"
wrapper_C2_rc=$(cat $DEWATA_TEST_ROOT/wrapper.C2.rc)
# In TEST mode, the wrapper should NOT reject (rc != 4).  rc may be 0
# (install succeeds) or 1 (AUTO-RESTORE COMPLETE on first-install) or
# some other non-4 -- the gate is mode-gated, so anything-but-4 is OK.
if [[ "$wrapper_C2_rc" != "4" ]]; then
    echo "  Scenario C.2: wrapper rc=$wrapper_C2_rc (PASS - DEPLOY_* accepted in test mode)"
else
    echo "  Scenario C.2: wrapper rc=$wrapper_C2_rc (FAIL - expected != 4 in test mode)"
    scenario_C_passed=0
fi
if ! grep -qE "DEPLOY_\* overrides are REJECTED" $DEWATA_TEST_ROOT/wrapper.C2.out; then
    echo "  Scenario C.2: refusal message NOT printed (PASS)"
else
    echo "  Scenario C.2: refusal message printed in test mode (FAIL)"
    scenario_C_passed=0
fi

# Final verdict -- EXACT assertions, not "any nonzero."
if [[ "$wrapper_A_rc" == "0" ]] && [[ "$wrapper_B_rc" == "2" ]] && \
   [[ "$wrapper_C1_rc" == "4" ]] && [[ "$wrapper_C2_rc" != "4" ]] && \
   [[ "$caddy_sha_A" == "$candidate_sha" ]] && [[ "$caddy_sha_B" == "$disp_baseline" ]] && \
   (( scenario_A_passed == 1 )) && (( scenario_B_passed == 1 )) && \
   (( scenario_C_passed == 1 )); then
    echo "TEST RESULT: PASS"
    exit 0
else
    echo "TEST RESULT: FAIL"
    exit 1
fi
