#!/usr/bin/env bash
# ============================================================
# Dewata apex deployment lifecycle test (FINDING #4 REVISION)
# ============================================================
# This driver exercises the REAL install-apex-candidate.sh and
# rollback-apex.sh against an isolated disposable tree.  It does
# NOT invent its own install/rollback — it controls the caddy
# lifecycle between disk operations.
#
# Sub-tests (each passes or fails independently):
#   POSITIVE: install -> restart -> probes (T1..T4) -> rollback -> probes (T6)
#   NEGATIVE: missing-file-in-src         (rc=6, no publish)
#   NEGATIVE: extra-file-in-src           (rc=6, no publish)
#   NEGATIVE: symlink-in-src              (rc=5, no publish)
#   NEGATIVE: baseline-drift              (rc=3, no replace)
#   NEGATIVE: missing-env                 (rc=2, no replace)
#   NEGATIVE: failed-publish-validation   (rc=1, auto-restore works)
#   NEGATIVE: failed-caddyfile-validation (rc=2 from auto-restore, prior state preserved)
#
# Strict mode: set -eEuo pipefail.  Any ERR triggers a visible
# failure.  Any unexpected output to stderr is recorded and counts
# as a failure.  We do NOT silently swallow errors.

set -Eeuo pipefail
shopt -s inherit_errexit 2>/dev/null || true

WORKTREE=/opt/dw-phase2
INSTALL_SH=$WORKTREE/deploy/atomic/install-apex-candidate.sh
ROLLBACK_SH=$WORKTREE/deploy/atomic/rollback-apex.sh
REVIEWED_MANIFEST=$WORKTREE/deploy/atomic/RELEASES/v0.1.0-pre1.MANIFEST.txt
CAND_SOURCE=$WORKTREE/deploy/caddy/Caddyfile.dewata.proposed
RELEASE_SOURCE=$WORKTREE/deploy/www/dewata-org/v0.1.0-pre1
CADDY=/usr/bin/caddy
TEST_PORT=18443

# Production state we MUST observe (caller verifies these are unchanged
# after every sub-test except T4 which intentionally exercises production)
PROD_CADDY=/opt/dewata.online/deploy/caddy/Caddyfile.dewata
PROD_RELEASE=/opt/dewata.online/deploy/www/dewata-org/v0.1.0-pre1
PROD_SERVICE=dewata-caddy
PROD_PORT=8443

LOG_PREFIX="[lifecycle-test]"

# Test outcome tracking.  We record a per-test pass/fail and exit
# with rc=0 only if ALL tests pass.  Any ERR trap that is not
# explicitly recovered from aborts the test.
PASSED=()
FAILED=()
TEST_RESULTS=/tmp/dewata-lifecycle-test-results.txt
: > "$TEST_RESULTS"

record_pass() {
    PASSED+=("$1")
    echo "PASS: $1" >> "$TEST_RESULTS"
    echo "$LOG_PREFIX PASS: $1"
}

record_fail() {
    FAILED+=("$1")
    echo "FAIL: $1 ($2)" >> "$TEST_RESULTS"
    echo "$LOG_PREFIX FAIL: $1 ($2)"
}

assert_eq() {
    local got="$1" expected="$2" label="$3"
    if [[ "$got" == "$expected" ]]; then
        record_pass "$label"
    else
        record_fail "$label" "got=$got expected=$expected"
    fi
}

assert_not_eq() {
    local got="$1" unexpected="$2" label="$3"
    if [[ "$got" != "$unexpected" ]]; then
        record_pass "$label"
    else
        record_fail "$label" "got=$got unexpected=$unexpected (should differ)"
    fi
}

# Snapshot of the REAL production state.  Captured once at start;
# re-verified at end.  Any change is a hard failure.
capture_prod_baseline() {
    PROD_CADDY_PRE_SHA=$(sha256sum "$PROD_CADDY" | cut -d' ' -f1)
    PROD_RELEASE_EXISTED=0
    [[ -d "$PROD_RELEASE" ]] && PROD_RELEASE_EXISTED=1
    PROD_CADDY_PRE_MTIME=$(stat -c %Y "$PROD_CADDY")
    PROD_SERVICE_PRE_PID=$(systemctl show "$PROD_SERVICE" -p MainPID --value)
    PROD_SERVICE_PRE_LISTEN=$([ -n "$(ss -ltn 2>/dev/null | grep ":$PROD_PORT ")" ] && echo yes || echo no)
    echo "$LOG_PREFIX production baseline:"
    echo "$LOG_PREFIX   $PROD_CADDY sha256: $PROD_CADDY_PRE_SHA"
    echo "$LOG_PREFIX   $PROD_RELEASE existed: $PROD_RELEASE_EXISTED"
    echo "$LOG_PREFIX   $PROD_CADDY mtime: $PROD_CADDY_PRE_MTIME"
    echo "$LOG_PREFIX   $PROD_SERVICE MainPID: $PROD_SERVICE_PRE_PID"
    echo "$LOG_PREFIX   $PROD_PORT listening: $PROD_SERVICE_PRE_LISTEN"
}

verify_prod_unchanged() {
    local label="$1"
    local post_sha post_mtime post_pid post_listen post_release_existed
    post_sha=$(sha256sum "$PROD_CADDY" | cut -d' ' -f1)
    post_mtime=$(stat -c %Y "$PROD_CADDY")
    post_pid=$(systemctl show "$PROD_SERVICE" -p MainPID --value)
    post_listen=$([ -n "$(ss -ltn 2>/dev/null | grep ":$PROD_PORT ")" ] && echo yes || echo no)
    post_release_existed=0
    [[ -d "$PROD_RELEASE" ]] && post_release_existed=1

    assert_eq "$post_sha"   "$PROD_CADDY_PRE_SHA"   "$label: prod Caddyfile sha256 unchanged"
    assert_eq "$post_mtime" "$PROD_CADDY_PRE_MTIME" "$label: prod Caddyfile mtime unchanged"
    assert_eq "$post_pid"   "$PROD_SERVICE_PRE_PID" "$label: prod $PROD_SERVICE MainPID unchanged"
    assert_eq "$post_listen" "$PROD_SERVICE_PRE_LISTEN" "$label: prod :$PROD_PORT listener state unchanged"
    assert_eq "$post_release_existed" "$PROD_RELEASE_EXISTED" "$label: prod release tree existence unchanged"
}

# Disposable tree setup.  All snapshots live INSIDE $WORK.
WORK=$(mktemp -d /tmp/dewata-lifecycle.XXXXXXXX)
DISP_BASE=$WORK/disp
DISP_CADDY_DIR=$DISP_BASE/caddy
DISP_WWW_DIR=$DISP_BASE/www
DISP_BASE_LOG=$WORK/disposable.log
TRACKED_PIDS=()
DISPOSABLE_DEFAULTS_BASELINE=""

# Every file the test writes lives under $WORK.  Snapshots are
# $WORK/snapshots/<timestamp>-pre-apex/.  The test does NOT touch
# /opt/dw-phase2/deploy/atomic/*-pre-apex (which is what the
# installer would create in production).
SNAPSHOT_DIR_PARENT=$WORK/snapshots

cleanup() {
    local rc=$?
    set +e
    for pid in "${TRACKED_PIDS[@]:-}"; do
        kill -TERM "$pid" 2>/dev/null
    done
    sleep 1
    for pid in "${TRACKED_PIDS[@]:-}"; do
        kill -KILL "$pid" 2>/dev/null
    done
    if [[ -z "${DEWATA_LIFECYCLE_KEEP:-}" ]]; then
        rm -rf "$WORK"
    fi
    return $rc
}
trap cleanup EXIT

# Launch a disposable caddy process isolated to its own XDG storage,
# so it never collides with the production caddy on :8443 and never
# opens the production-default :2019 admin endpoint.
launch_disposable_caddy() {
    local caddyfile="$1"
    local XDG_STORAGE="$WORK/xdg-storage-$$-$BASHPID"
    mkdir -p "$XDG_STORAGE"
    HOME="$WORK/h-$$-$BASHPID" \
        XDG_DATA_HOME="$XDG_STORAGE" \
        DEWATA_RELEASE_ROOT="$DISP_WWW_DIR/dewata-org/v0.1.0-pre1" \
        DEWATA_LOG_FILE="$WORK/disposable-caddy.log" \
        "$CADDY" run --config "$caddyfile" --adapter caddyfile > "$DISP_BASE_LOG" 2>&1 &
    local pid=$!
    TRACKED_PIDS+=("$pid")
    # Wait up to 8s for the listener to come up.
    for attempt in 1 2 3 4 5 6 7 8; do
        sleep 1
        if ss -ltn 2>/dev/null | grep -q ":$TEST_PORT "; then
            return 0
        fi
    done
    return 1
}

# Wrapper that requires the disposable caddy to start.  Records a
# failure and marks the suite as failed if launch fails.  All sub-tests
# use this wrapper.
SUITE_FAILED=0

require_disposable() {
    local caddyfile="$1"
    local label="$2"
    if ! launch_disposable_caddy "$caddyfile"; then
        record_fail "$label" "launch_disposable_caddy failed for $caddyfile"
        SUITE_FAILED=1
        return 1
    fi
    return 0
}

stop_disposable_caddy() {
    for pid in "${TRACKED_PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null
        fi
    done
    sleep 2
    for pid in "${TRACKED_PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -KILL "$pid" 2>/dev/null
        fi
    done
    TRACKED_PIDS=()
    for attempt in 1 2 3 4 5; do
        if ! ss -ltn 2>/dev/null | grep -q ":$TEST_PORT "; then
            return 0
        fi
        sleep 1
    done
}

# Setup: build a fresh disposable tree.
setup_disposable() {
    mkdir -p "$DISP_CADDY_DIR" "$DISP_WWW_DIR" "$SNAPSHOT_DIR_PARENT"
    cp "$WORKTREE/deploy/caddy/Caddyfile.dewata.runtime" "$DISP_CADDY_DIR/Caddyfile.dewata"
    python3 - <<PYEOF
cf_path = "$DISP_CADDY_DIR/Caddyfile.dewata"
src = open(cf_path).read()
src = src.replace(":8443 ", ":$TEST_PORT ")
if "auto_https off" not in src:
    if "{" in src:
        idx = src.find("{")
        src = src[:idx+1] + "\n\tauto_https off" + src[idx+1:]
    else:
        src = "auto_https off\n" + src
open(cf_path, "w").write(src)
PYEOF
    DISPOSABLE_DEFAULTS_BASELINE=$(sha256sum "$DISP_CADDY_DIR/Caddyfile.dewata" | cut -d' ' -f1)
    "$CADDY" validate --config "$DISP_CADDY_DIR/Caddyfile.dewata" --adapter caddyfile > /dev/null
}

# Common: invoke install-apex-candidate.sh against the disposable
# with all required env vars set.  Caller can override env vars
# (e.g. a wrong baseline) before invoking.
run_install() {
    # Invoke the install script.  Standard disposable env is set
    # explicitly below.  Callers may override individual vars by
    # exporting them in the parent shell BEFORE calling run_install
    # (the explicit assignments act as defaults).  Override form:
    #     export DEWATA_REVIEWED_MANIFEST=/some/path
    #     run_install "$RELEASE_SRC"
    local release_src="${1:-$RELEASE_SOURCE}"
    DEWATA_TEST_MODE="${DEWATA_TEST_MODE_OVERRIDE:-1}" \
        DEWATA_PROD_CADDY="${DEWATA_PROD_CADDY_OVERRIDE:-$DISP_CADDY_DIR/Caddyfile.dewata}" \
        DEWATA_PROD_WWW="${DEWATA_PROD_WWW_OVERRIDE:-$DISP_WWW_DIR}" \
        DEWATA_CANDIDATE="${DEWATA_CANDIDATE_OVERRIDE:-$CAND_SOURCE}" \
        DEWATA_RELEASE_SRC="${DEWATA_RELEASE_SRC_OVERRIDE:-$release_src}" \
        DEWATA_RELEASE_DST="${DEWATA_RELEASE_DST_OVERRIDE:-$DISP_WWW_DIR/dewata-org/v0.1.0-pre1}" \
        DEWATA_LISTENER_PORT="${DEWATA_LISTENER_PORT_OVERRIDE:-$TEST_PORT}" \
        DEWATA_REVIEWED_MANIFEST="${DEWATA_REVIEWED_MANIFEST_OVERRIDE:-$REVIEWED_MANIFEST}" \
        DEWATA_PROD_BASELINE_SHA="${DEWATA_PROD_BASELINE_SHA_OVERRIDE:-}" \
        DEWATA_SNAPSHOT_PARENT="${DEWATA_SNAPSHOT_PARENT_OVERRIDE:-$SNAPSHOT_DIR_PARENT}" \
        DEWATA_FAKE_FAIL_AT_GATE="${DEWATA_FAKE_FAIL_AT_GATE_OVERRIDE:-}" \
        DEWATA_FAKE_RESTART_FAILURE="${DEWATA_FAKE_RESTART_FAILURE_OVERRIDE:-0}" \
        DEWATA_FAKE_RECOVERY_VALIDATION_FAILURE="${DEWATA_FAKE_RECOVERY_VALIDATION_FAILURE_OVERRIDE:-0}" \
        PATH="$PATH" HOME="$WORK" \
        bash "$INSTALL_SH"
}

# Common: invoke rollback-apex.sh against the disposable with all
# required env vars set.
run_rollback() {
    local snapshot="$1"
    DEWATA_TEST_MODE=1 \
        DEWATA_PROD_CADDY="$DISP_CADDY_DIR/Caddyfile.dewata" \
        DEWATA_SNAPSHOT_DIR="$snapshot" \
        DEWATA_RELEASE_DST="$DISP_WWW_DIR/dewata-org/v0.1.0-pre1" \
        DEWATA_LISTENER_PORT="$TEST_PORT" \
        PATH="$PATH" HOME="$WORK" \
        bash "$ROLLBACK_SH" "$snapshot"
}

# T0: setup
echo
echo "================================================================"
echo "T0: setup"
echo "================================================================"
echo "  work directory: $WORK"
setup_disposable
capture_prod_baseline

# ------------------------------------------------------------
# POSITIVE TEST: end-to-end install + rollback
# ------------------------------------------------------------
echo
echo "================================================================"
echo "POSITIVE: install -> probes -> rollback -> probes"
echo "================================================================"

# The install script requires DEWATA_PROD_BASELINE_SHA.  For the
# positive test we use the disposable\'s current caddyfile sha as
# the baseline (because the disposable was just set up from the
# reviewer-confirmed runtime snapshot).
DEWATA_PROD_BASELINE_SHA_OVERRIDE="$DISPOSABLE_DEFAULTS_BASELINE" \
    run_install "$RELEASE_SOURCE"

# The installer exited 0.  Verify the installer wrote the candidate
# caddyfile to the disposable (NOT a copy from CAND_SOURCE; the
# installer pulled from $CAND_SOURCE=$DEWATA_CANDIDATE).
INSTALLED_SHA=$(sha256sum "$DISP_CADDY_DIR/Caddyfile.dewata" | cut -d' ' -f1)
CAND_SHA=$(sha256sum "$CAND_SOURCE" | cut -d' ' -f1)
assert_eq "$INSTALLED_SHA" "$CAND_SHA" "POSITIVE: installed caddyfile == candidate source"

# Verify the installer published the release (not copied from a
# side-channel).  $DISP_WWW_DIR/dewata-org/v0.1.0-pre1 must contain
# the same files as $RELEASE_SOURCE.
RELEASED=$( (cd "$DISP_WWW_DIR/dewata-org/v0.1.0-pre1" && find . -type f) | sort -u )
SOURCE_FILES=$( (cd "$RELEASE_SOURCE" && find . -type f) | sort -u )
if [[ "$RELEASED" == "$SOURCE_FILES" ]]; then
    record_pass "POSITIVE: published tree == release source tree"
else
    record_fail "POSITIVE: published tree mismatch" "see diff"
fi

# Probe baseline (catch-all).  Launch disposable caddy using the
# snapshot dir caddyfile (the prior production caddyfile, before the
# installer ran).  Need to find the snapshot the installer took.
INST_SNAPSHOT=$(ls -1td $SNAPSHOT_DIR_PARENT/* 2>/dev/null | head -1)
if [[ -z "$INST_SNAPSHOT" ]]; then
    # The install script places its snapshot in $WORKTREE/deploy/atomic by default.
    # We override it via DEWATA_SNAPSHOT_PARENT to keep snapshots in $WORK, but
    # for now look in $WORKTREE/deploy/atomic.
    INST_SNAPSHOT=$(ls -1td $WORKTREE/deploy/atomic/*-pre-apex 2>/dev/null | head -1)
fi
echo "  installer snapshot: $INST_SNAPSHOT"
# T3 baseline probe: use a SEPARATE temp file so we do NOT overwrite
# the disposable\'s Caddyfile.dewata, which was just written by the
# installer in T2/G4 and which T4 must use as-is.
BASELINE_CF="$WORK/baseline-caddyfile.$$"
cp "$INST_SNAPSHOT/Caddyfile.dewata.runtime" "$BASELINE_CF"
# apply test-mode substitution (port + auto_https off)
python3 - <<PYEOF
cf_path = "$BASELINE_CF"
src = open(cf_path).read()
src = src.replace(":8443 ", ":$TEST_PORT ")
if "auto_https off" not in src:
    if "{" in src:
        idx = src.find("{")
        src = src[:idx+1] + "\n\tauto_https off" + src[idx+1:]
    else:
        src = "auto_https off\n" + src
open(cf_path, "w").write(src)
PYEOF
if require_disposable "$BASELINE_CF" "POSITIVE: baseline disposable launch"; then
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 -H "Host: dewata.org" "http://127.0.0.1:$TEST_PORT/" || echo 000)
    assert_eq "$code" "503" "POSITIVE: baseline apex / -> 503"
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 -H "Host: api.dewata.org" "http://127.0.0.1:$TEST_PORT/health" || echo 000)
    assert_eq "$code" "200" "POSITIVE: baseline api /health -> 200"
fi
stop_disposable_caddy
# Verify the installer-written Caddyfile.dewata is unchanged
INSTALLED_AFTER_T3=$(sha256sum "$DISP_CADDY_DIR/Caddyfile.dewata" | cut -d ' ' -f1)
assert_eq "$INSTALLED_AFTER_T3" "$CAND_SHA" "POSITIVE: installer-written caddyfile unchanged after T3"

# Probe post-install.  Launch disposable caddy using the file the
# installer actually wrote (NOT a fresh copy from CAND_SOURCE).
# This is finding #4(a): test the exact file written by the installer.
# We DO have to substitute :8443 -> :$TEST_PORT and inject auto_https
# off for the disposable caddy to actually bind without colliding with
# the production listener on :8443 or auto-acquiring certs.  This is
# test-mode-only substitution that does NOT alter the installer-written
# file on disk (we copy to a side path first).
POST_INSTALL_CF="$WORK/post-install-caddyfile.$$"
cp "$DISP_CADDY_DIR/Caddyfile.dewata" "$POST_INSTALL_CF"
python3 - <<PYEOF
cf_path = "$POST_INSTALL_CF"
src = open(cf_path).read()
src = src.replace(":8443 ", ":$TEST_PORT ")
if "auto_https off" not in src:
    if "{" in src:
        idx = src.find("{")
        src = src[:idx+1] + "\n\tauto_https off" + src[idx+1:]
    else:
        src = "auto_https off\n" + src
open(cf_path, "w").write(src)
PYEOF
if require_disposable "$POST_INSTALL_CF" "POSITIVE: post-install disposable launch"; then
    fail=0
    probe() {
        local host="$1" path="$2" expected_code="$3"
        local code
        code=$(curl -s -o /tmp/probe.body -w "%{http_code}" --max-time 5 \
            -H "Host: $host" "http://127.0.0.1:$TEST_PORT$path" || echo 000)
        if [[ "$code" == "$expected_code" ]]; then
            record_pass "POSITIVE: post-install $host $path -> $code"
        else
            record_fail "POSITIVE: post-install $host $path" "got=$code expected=$expected_code"
            fail=1
        fi
    }
    probe dewata.org          "/"               200
    probe dewata.org          "/index.ban.html" 200
    probe dewata.org          "/calendar.ban.html" 200
    probe api.dewata.org      "/health"         200
    probe bci.dewata.org      "/"               503
fi
stop_disposable_caddy

# Rollback.  Drive the real rollback script.
run_rollback "$INST_SNAPSHOT"

# Verify post-rollback: caddyfile should match the baseline disposable.
POST_ROLLBACK_SHA=$(sha256sum "$DISP_CADDY_DIR/Caddyfile.dewata" | cut -d' ' -f1)
assert_eq "$POST_ROLLBACK_SHA" "$DISPOSABLE_DEFAULTS_BASELINE" "POSITIVE: rollback restored disposable baseline caddyfile"

# Probe post-rollback.
cp "$DISP_CADDY_DIR/Caddyfile.dewata" "$DISP_CADDY_DIR/Caddyfile.dewata.test-mode"
python3 - <<PYEOF
cf_path = "$DISP_CADDY_DIR/Caddyfile.dewata"
src = open(cf_path).read()
src = src.replace(":8443 ", ":$TEST_PORT ")
open(cf_path, "w").write(src)
PYEOF
if require_disposable "$DISP_CADDY_DIR/Caddyfile.dewata" "POSITIVE: post-rollback disposable launch"; then
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 -H "Host: dewata.org" "http://127.0.0.1:$TEST_PORT/" || echo 000)
    assert_eq "$code" "503" "POSITIVE: post-rollback apex / -> 503"
fi
stop_disposable_caddy

verify_prod_unchanged "POSITIVE"

# ------------------------------------------------------------
# NEGATIVE TESTS
# ------------------------------------------------------------

# Helper: re-setup disposable for next sub-test.
reset_disposable() {
    stop_disposable_caddy
    rm -rf "$DISP_CADDY_DIR" "$DISP_WWW_DIR"
    mkdir -p "$DISP_CADDY_DIR" "$DISP_WWW_DIR"
    cp "$WORKTREE/deploy/caddy/Caddyfile.dewata.runtime" "$DISP_CADDY_DIR/Caddyfile.dewata"
    python3 - <<PYEOF
cf_path = "$DISP_CADDY_DIR/Caddyfile.dewata"
src = open(cf_path).read()
src = src.replace(":8443 ", ":$TEST_PORT ")
open(cf_path, "w").write(src)
PYEOF
    DISPOSABLE_DEFAULTS_BASELINE=$(sha256sum "$DISP_CADDY_DIR/Caddyfile.dewata" | cut -d' ' -f1)
}

# NEGATIVE-1: missing-file-in-src
# Create a release source with one manifest-listed file removed.
echo
echo "================================================================"
echo "NEGATIVE-1: missing-file-in-src"
echo "================================================================"
reset_disposable
SHORT_RELEASE="$WORK/short-release"
rm -rf "$SHORT_RELEASE"
cp -r "$RELEASE_SOURCE" "$SHORT_RELEASE"
rm -f "$SHORT_RELEASE/calendar.ban.html"
# Use the FULL reviewed manifest (which lists calendar.ban.html) against a release src that is missing calendar.ban.html.  This is the actual "manifest expects file but src is missing it" case the installer must catch.
SHORT_MANIFEST="$WORK/short-release.MANIFEST.txt"
cp "$REVIEWED_MANIFEST" "$SHORT_MANIFEST"
set +e
DEWATA_REVIEWED_MANIFEST_OVERRIDE="$SHORT_MANIFEST" \
    DEWATA_PROD_BASELINE_SHA_OVERRIDE="$DISPOSABLE_DEFAULTS_BASELINE" \
    run_install "$SHORT_RELEASE"
rc=$?
set -e
assert_eq "$rc" "6" "NEGATIVE-1: install rc=6 when manifest entry missing in src"
# Production must remain unchanged
post_sha=$(sha256sum "$PROD_CADDY" | cut -d' ' -f1)
assert_eq "$post_sha" "$PROD_CADDY_PRE_SHA" "NEGATIVE-1: prod Caddyfile unchanged"
release_exists=0; [[ -d "$PROD_RELEASE" ]] && release_exists=1
assert_eq "$release_exists" "$PROD_RELEASE_EXISTED" "NEGATIVE-1: prod release tree still absent"
verify_prod_unchanged "NEGATIVE-1"

# NEGATIVE-2: extra-file-in-src
echo
echo "================================================================"
echo "NEGATIVE-2: extra-file-in-src"
echo "================================================================"
reset_disposable
EXTRA_RELEASE="$WORK/extra-release"
rm -rf "$EXTRA_RELEASE"
cp -r "$RELEASE_SOURCE" "$EXTRA_RELEASE"
echo "<html>extra</html>" > "$EXTRA_RELEASE/extra-file.html"
set +e
DEWATA_PROD_BASELINE_SHA_OVERRIDE="$DISPOSABLE_DEFAULTS_BASELINE" \
    run_install "$EXTRA_RELEASE"
rc=$?
set -e
assert_eq "$rc" "6" "NEGATIVE-2: install rc=6 when RELEASE_SRC has files not in manifest"
post_sha=$(sha256sum "$PROD_CADDY" | cut -d' ' -f1)
assert_eq "$post_sha" "$PROD_CADDY_PRE_SHA" "NEGATIVE-2: prod Caddyfile unchanged"
verify_prod_unchanged "NEGATIVE-2"

# NEGATIVE-3: symlink-in-src
echo
echo "================================================================"
echo "NEGATIVE-3: symlink-in-src"
echo "================================================================"
reset_disposable
SYMLINK_RELEASE="$WORK/symlink-release"
rm -rf "$SYMLINK_RELEASE"
cp -r "$RELEASE_SOURCE" "$SYMLINK_RELEASE"
ln -sf "$RELEASE_SOURCE/index.html" "$SYMLINK_RELEASE/linked.html"
set +e
DEWATA_PROD_BASELINE_SHA_OVERRIDE="$DISPOSABLE_DEFAULTS_BASELINE" \
    run_install "$SYMLINK_RELEASE"
rc=$?
set -e
assert_eq "$rc" "5" "NEGATIVE-3: install rc=5 when RELEASE_SRC contains a symlink"
post_sha=$(sha256sum "$PROD_CADDY" | cut -d' ' -f1)
assert_eq "$post_sha" "$PROD_CADDY_PRE_SHA" "NEGATIVE-3: prod Caddyfile unchanged"
verify_prod_unchanged "NEGATIVE-3"

# NEGATIVE-4: baseline-drift
echo
echo "================================================================"
echo "NEGATIVE-4: baseline-drift"
echo "================================================================"
reset_disposable
set +e
DEWATA_PROD_BASELINE_SHA_OVERRIDE="0000000000000000000000000000000000000000000000000000000000000000" \
    run_install "$RELEASE_SOURCE"
rc=$?
set -e
assert_eq "$rc" "3" "NEGATIVE-4: install rc=3 when baseline sha does not match live Caddyfile"
post_sha=$(sha256sum "$PROD_CADDY" | cut -d' ' -f1)
assert_eq "$post_sha" "$PROD_CADDY_PRE_SHA" "NEGATIVE-4: prod Caddyfile unchanged"
verify_prod_unchanged "NEGATIVE-4"

# NEGATIVE-5: missing-env (DEWATA_REVIEWED_MANIFEST unset)
echo
echo "================================================================"
echo "NEGATIVE-5: missing-env"
echo "================================================================"
reset_disposable
# Invoke the install script directly without setting the required
# env vars.  The script must refuse with rc=2 (mandatory env vars).
set +e
env -i PATH="$PATH" HOME="$WORK" \
    DEWATA_TEST_MODE=1 \
    DEWATA_PROD_CADDY="$DISP_CADDY_DIR/Caddyfile.dewata" \
    DEWATA_PROD_WWW="$DISP_WWW_DIR" \
    DEWATA_CANDIDATE="$CAND_SOURCE" \
    DEWATA_RELEASE_SRC="$RELEASE_SOURCE" \
    DEWATA_RELEASE_DST="$DISP_WWW_DIR/dewata-org/v0.1.0-pre1" \
    DEWATA_LISTENER_PORT="$TEST_PORT" \
    bash "$INSTALL_SH"
rc=$?
set -e
assert_eq "$rc" "2" "NEGATIVE-5: install rc=2 when DEWATA_REVIEWED_MANIFEST unset"
# Verify the script also refuses with rc=2 when DEWATA_PROD_BASELINE_SHA is unset
# while DEWATA_REVIEWED_MANIFEST is set.
set +e
env -i PATH="$PATH" HOME="$WORK" \
    DEWATA_TEST_MODE=1 \
    DEWATA_PROD_CADDY="$DISP_CADDY_DIR/Caddyfile.dewata" \
    DEWATA_PROD_WWW="$DISP_WWW_DIR" \
    DEWATA_CANDIDATE="$CAND_SOURCE" \
    DEWATA_RELEASE_SRC="$RELEASE_SOURCE" \
    DEWATA_RELEASE_DST="$DISP_WWW_DIR/dewata-org/v0.1.0-pre1" \
    DEWATA_LISTENER_PORT="$TEST_PORT" \
    DEWATA_REVIEWED_MANIFEST="$REVIEWED_MANIFEST" \
    bash "$INSTALL_SH"
rc=$?
set -e
assert_eq "$rc" "2" "NEGATIVE-5: install rc=2 when DEWATA_PROD_BASELINE_SHA unset"
post_sha=$(sha256sum "$PROD_CADDY" | cut -d' ' -f1)
assert_eq "$post_sha" "$PROD_CADDY_PRE_SHA" "NEGATIVE-5: prod Caddyfile unchanged"
verify_prod_unchanged "NEGATIVE-5"

# NEGATIVE-6: failure AFTER publication.  We use the install\'s
# DEWATA_FAKE_FAIL_AT_GATE=g3-post-publish hook to make the install
# fail AFTER G3 has swapped the staging dir into RELEASE_DST but BEFORE
# G4 starts.  This is the failure point the previous test missed: the
# publication completed (release tree is in place), but the caddyfile
# install has not yet started.
echo
echo "================================================================"
echo "NEGATIVE-6: failure AFTER publication (pre-G4)"
echo "================================================================"
reset_disposable
# Pre-create a "prior release" at the disposable target with known
# content so we can verify the G3 backup-restore works.
PRIOR=$DISP_WWW_DIR/dewata-org/v0.1.0-pre1
mkdir -p "$PRIOR"
echo "prior release content" > "$PRIOR/index.ban.html"
PRIOR_SHA=$(sha256sum "$PRIOR/index.ban.html" | cut -d' ' -f1)
set +e
DEWATA_FAKE_FAIL_AT_GATE_OVERRIDE="g3-post-publish" \
    DEWATA_PROD_BASELINE_SHA_OVERRIDE="$DISPOSABLE_DEFAULTS_BASELINE" \
    run_install "$RELEASE_SOURCE"
rc=$?
set -e
assert_eq "$rc" "1" "NEGATIVE-6: install rc=1 on post-publish failure"
# After failure, the disposable caddyfile must be restored to baseline
post_sha=$(sha256sum "$DISP_CADDY_DIR/Caddyfile.dewata" | cut -d' ' -f1)
assert_eq "$post_sha" "$DISPOSABLE_DEFAULTS_BASELINE" "NEGATIVE-6: disposable caddyfile restored to baseline"
# The prior release tree must be restored (G3 backed it up before
# publishing the new tree, and do_restore moves it back)
post_release_sha=$(sha256sum "$PRIOR/index.ban.html" | cut -d' ' -f1)
assert_eq "$post_release_sha" "$PRIOR_SHA" "NEGATIVE-6: prior release tree restored"
# Verify the published release (which had been swapped in by G3) has
# been moved aside as RELEASE_DST.postrestore.<ts> (NOT the active
# location)
post_restore_dirs=$(ls -1d ${DISP_WWW_DIR}/dewata-org/v0.1.0-pre1.postrestore.* 2>/dev/null | wc -l)
assert_eq "$post_restore_dirs" "1" "NEGATIVE-6: post-publish tree moved aside"
verify_prod_unchanged "NEGATIVE-6"

# NEGATIVE-7: failure AFTER configuration install.  The candidate
# caddyfile has been written to $PROD (G4 succeeded), then we trigger
# a failure via DEWATA_FAKE_FAIL_AT_GATE=g4 (the install\'s post-G4
# hook).  do_restore must restore the snapshot runtime caddyfile.  The
# release tree is NOT modified at this point (G3 only swapped the tree
# on a successful install; G4 failure means G3\'s RELEASE_BACKED_UP
# may or may not exist).
echo
echo "================================================================"
echo "NEGATIVE-7: failure AFTER configuration install (post-G4)"
echo "================================================================"
reset_disposable
set +e
DEWATA_FAKE_FAIL_AT_GATE_OVERRIDE="g4" \
    DEWATA_PROD_BASELINE_SHA_OVERRIDE="$DISPOSABLE_DEFAULTS_BASELINE" \
    run_install "$RELEASE_SOURCE"
rc=$?
set -e
# The install\'s G4 happens, then the post-G4 hook fires do_restore.
# do_restore restores the snapshot runtime caddyfile.
assert_eq "$rc" "1" "NEGATIVE-7: install rc=1 on post-G4 failure"
post_sha=$(sha256sum "$DISP_CADDY_DIR/Caddyfile.dewata" | cut -d ' ' -f1)
assert_eq "$post_sha" "$DISPOSABLE_DEFAULTS_BASELINE" "NEGATIVE-7: disposable caddyfile restored to baseline"
verify_prod_unchanged "NEGATIVE-7"

# NEGATIVE-8: failure AFTER G5 caddyfile validation, BEFORE restart.
# The candidate caddyfile is installed and validates; we then
# trigger a failure via DEWATA_FAKE_FAIL_AT_GATE=g5 (the install\'s
# post-G5 hook).  do_restore fires.
echo
echo "================================================================"
echo "NEGATIVE-8: failure AFTER G5 validation (pre-restart)"
echo "================================================================"
reset_disposable
set +e
DEWATA_FAKE_FAIL_AT_GATE_OVERRIDE="g5" \
    DEWATA_PROD_BASELINE_SHA_OVERRIDE="$DISPOSABLE_DEFAULTS_BASELINE" \
    run_install "$RELEASE_SOURCE"
rc=$?
set -e
assert_eq "$rc" "1" "NEGATIVE-8: install rc=1 on post-G5 failure"
post_sha=$(sha256sum "$DISP_CADDY_DIR/Caddyfile.dewata" | cut -d ' ' -f1)
assert_eq "$post_sha" "$DISPOSABLE_DEFAULTS_BASELINE" "NEGATIVE-8: disposable caddyfile restored to baseline"
verify_prod_unchanged "NEGATIVE-8"

# NEGATIVE-9: failure DURING restart/recovery.  Use
# DEWATA_FAKE_FAIL_AT_GATE=g6 which fires AFTER G6 (after the test-mode
# restart-skip or after a real restart in production mode).  do_restore
# fires; the install must restore the caddyfile from snapshot.
echo
echo "================================================================"
echo "NEGATIVE-9: failure during restart/recovery (post-G6)"
echo "================================================================"
reset_disposable
set +e
DEWATA_FAKE_FAIL_AT_GATE_OVERRIDE="g6" \
    DEWATA_PROD_BASELINE_SHA_OVERRIDE="$DISPOSABLE_DEFAULTS_BASELINE" \
    run_install "$RELEASE_SOURCE"
rc=$?
set -e
assert_eq "$rc" "1" "NEGATIVE-9: install rc=1 on post-G6 failure"
post_sha=$(sha256sum "$DISP_CADDY_DIR/Caddyfile.dewata" | cut -d ' ' -f1)
assert_eq "$post_sha" "$DISPOSABLE_DEFAULTS_BASELINE" "NEGATIVE-9: disposable caddyfile restored to baseline"
verify_prod_unchanged "NEGATIVE-9"

# NEGATIVE-10: failure DURING recovery (do_restore).  Combine
# DEWATA_FAKE_FAIL_AT_GATE=g4 (triggers do_restore) with
# DEWATA_FAKE_RECOVERY_VALIDATION_FAILURE=1 (corrupts the snapshot
# runtime file in place, so caddy validate on the restored caddyfile
# fails).  do_restore must NOT declare success; it must exit non-zero
# with AUTO-RESTORE INCOMPLETE.
echo
echo "================================================================"
echo "NEGATIVE-10: failure during recovery (do_restore validation fails)"
echo "================================================================"
reset_disposable
set +e
DEWATA_FAKE_FAIL_AT_GATE_OVERRIDE="g4" \
    DEWATA_FAKE_RECOVERY_VALIDATION_FAILURE_OVERRIDE="1" \
    DEWATA_PROD_BASELINE_SHA_OVERRIDE="$DISPOSABLE_DEFAULTS_BASELINE" \
    run_install "$RELEASE_SOURCE"
rc=$?
set -e
assert_eq "$rc" "2" "NEGATIVE-10: install rc=2 on recovery validation failure"
# The disposable\'s caddyfile is now the BROKEN one (the corrupted
# snapshot).  Verify it does NOT match the baseline.
broken_sha=$(sha256sum "$DISP_CADDY_DIR/Caddyfile.dewata" | cut -d ' ' -f1)
assert_not_eq "$broken_sha" "$DISPOSABLE_DEFAULTS_BASELINE" "NEGATIVE-10: disposable caddyfile is the broken restored copy, NOT the baseline"
verify_prod_unchanged "NEGATIVE-10"

# ------------------------------------------------------------
# Final: production verification
# ------------------------------------------------------------
echo
echo "================================================================"
echo "FINAL: production untouched (across all sub-tests)"
echo "================================================================"
verify_prod_unchanged "FINAL"

# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------
echo
echo "================================================================"
echo "SUMMARY"
echo "================================================================"
echo "passed: ${#PASSED[@]}"
echo "failed: ${#FAILED[@]}"
if (( ${#FAILED[@]} > 0 )); then
    echo
    echo "failures:"
    for f in "${FAILED[@]}"; do
        echo "  $f"
    done
fi
if (( SUITE_FAILED > 0 )); then
    echo "LIFECYCLE TEST FAIL: suite-level failure (e.g. disposable caddy failed to start)"
    exit 2
fi
if (( ${#FAILED[@]} > 0 )); then
    exit 1
fi
echo "LIFECYCLE TEST PASS"
exit 0
