#!/usr/bin/env bash
# =============================================================================
# run-lifecycle-test.sh -- positive + negative disposable tree tests
# =============================================================================
#
# Six surface inputs the harness brings up:
#   - A disposable tree under /tmp/dewata-lifecycle/<timestamp>/
#   - A disposable caddyfile at /tmp/dewata-lifecycle/<timestamp>/caddy/
#   - A disposable www tree at /tmp/dewata-lifecycle/<timestamp>/www/
#   - A disposable manifest at /tmp/dewata-lifecycle/<timestamp>/RELEASES/
#   - A disposable systemctl shim at /opt/dw-phase2/tests/disposable-systemctl.sh
#   - A snapshot parent at /tmp/dewata-lifecycle/<timestamp>/atomic/
#
# What it does:
#   1. POSITIVE: invoke install + caddy + rollback against the
#      disposable tree.  Verify (a) install succeeds and reports
#      actual_snapshot_path, (b) caddyfile matches the candidate,
#      (c) release tree exactly matches the manifest, (d) the
#      rollback restores the Caddyfile byte-for-byte, (e) the
#      systemctl shim log shows the expected call sequence.
#   2. NEGATIVE-1 ... NEGATIVE-N: inject failures and verify the
#      installer's recovery behavior.
#   3. Production state is checked BEFORE THE FIRST TEST RUN and
#      AFTER EVERY TEST RUN.  Production state changes -> suite FAIL.
#
# No production-side operations are invoked.
# =============================================================================

set -Eeuo pipefail
# inherit_errexit is OFF so that a child like `env -i ... bash installer`
# can return non-zero from inside a function without killing the script.
shopt -u inherit_errexit 2>/dev/null || true

# --------------------------------------------------------------------
# Suite status tracking
# --------------------------------------------------------------------
TOTAL=0; PASSED=0; FAILED=0
SUITE_FAILED=0

# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------
sha256_of_file() { sha256sum "$1" | cut -d' ' -f1; }
record() {
    local name="$1" status="$2" extra="${3:-}"
    TOTAL=$((TOTAL+1))
    if [[ "$status" == "PASS" ]]; then
        PASSED=$((PASSED+1))
        printf "  [PASS] %-30s %s\\n" "$name" "$extra"
    else
        FAILED=$((FAILED+1))
        SUITE_FAILED=1
        printf "  [FAIL] %-30s %s\\n" "$name" "$extra"
    fi
}

# --------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------
WT="${DEWATA_WORKTREE:-/opt/dw-phase2}"
SHIM_DIR="$WT/tests"
INSTALLER="$WT/deploy/atomic/install-apex-candidate.sh"
ROLLBACK="$WT/deploy/atomic/rollback-apex.sh"
DISPOSABLE_SYSTEMCTL="$SHIM_DIR/disposable-systemctl.sh"

# --------------------------------------------------------------------
# Production state capture (BEFORE)
# --------------------------------------------------------------------
PROD_CADDY="/opt/dewata.online/deploy/caddy/Caddyfile.dewata"
PROD_LISTENER_PORT="8443"

record_prod_state() {
    PROD_CADDY_SHA=$(sha256_of_file "$PROD_CADDY")
    PROD_PID=$(systemctl show dewata-caddy -p MainPID --value)
}

# --------------------------------------------------------------------
# Disposable setup
# --------------------------------------------------------------------
SHIM_LOG_DIR="/tmp/dewata-lifecycle"
DISP_SYSTEMCTL="$SHIM_DIR/disposable-systemctl.sh"
DISP_VALIDATE="$SHIM_DIR/disposable-validate.sh"
# DISP_SYSTEMCTL_PATH is the directory of the disposable shims (used
# by NEG-10 to point DEWATA_VALIDATE_CMD at $DISP_SYSTEMCTL_PATH/disposable-validate.sh).
DISP_SYSTEMCTL_PATH="$SHIM_DIR"
# Look it up; the installer's adapter validation requires the file to
# exist on disk.
[[ -f "$DISP_VALIDATE" ]] || { echo "FATAL: $DISP_VALIDATE missing" >&2; exit 1; }
mkdir -p "$SHIM_LOG_DIR"
SHIM_LOG="/tmp/dewata-lifecycle-systemctl.log"
mkdir -p "$SHIM_LOG_DIR/caddy"
mkdir -p "$SHIM_LOG_DIR/www"
mkdir -p "$SHIM_LOG_DIR/atomic"
mkdir -p "$SHIM_LOG_DIR/review/caddy"
mkdir -p "$SHIM_LOG_DIR/review/www"
mkdir -p "$SHIM_LOG_DIR/RELEASES"

# Initialize disposable Caddyfile = production Caddyfile (so the install
# has the actual runtime to base the snapshot on).
cp "$PROD_CADDY" "$SHIM_LOG_DIR/caddy/Caddyfile.dewata.runtime"
cp "$PROD_CADDY" "$SHIM_LOG_DIR/caddy/Caddyfile.dewata"

# Initialize disposable candidate Caddyfile
cp "$WT/deploy/caddy/Caddyfile.dewata.proposed" "$SHIM_LOG_DIR/review/caddy/Caddyfile.dewata.proposed"
CAND_SHA=$(sha256_of_file "$SHIM_LOG_DIR/review/caddy/Caddyfile.dewata.proposed")
echo "candidate sha256 = $CAND_SHA"

# Initialize reviewed release source = bundle's pre1 release tree.
cp -r "$WT/deploy/www/dewata-org/v0.1.0-pre1/." "$SHIM_LOG_DIR/review/www/"
MANIFEST_PRE1="$WT/deploy/atomic/RELEASES/v0.1.0-pre1.MANIFEST.txt"
[[ -f "$MANIFEST_PRE1" ]] || { echo "FATAL: $MANIFEST_PRE1 missing" >&2; exit 1; }

# Generate a disposable MANIFEST that matches the disposable release source.
disp_manifest="$SHIM_LOG_DIR/RELEASES/v0.1.0-pre1.MANIFEST.txt"
: > "$disp_manifest"
( cd "$SHIM_LOG_DIR/review/www" && find . -type f | sed "s|^\\./||" | sort ) | while IFS= read -r rel; do
    [[ -z "$rel" ]] && continue
    sum=$(sha256_of_file "$SHIM_LOG_DIR/review/www/$rel")
    printf "%s  %s\\n" "$sum" "$rel" >> "$disp_manifest"
done
# the caddyfile entry has its own sha
printf "%s  Caddyfile.dewata.proposed\\n" "$CAND_SHA" >> "$disp_manifest"

# Disposable shim PID files
SHIM_PIDFILE="$SHIM_LOG_DIR/caddy.pid"
SHIM_ACTIVEFILE="$SHIM_LOG_DIR/caddy.active"
printf "0\\n" > "$SHIM_PIDFILE"
printf "0\\n" > "$SHIM_ACTIVEFILE"

# Disposable baseline sha = current disposable caddyfile
DISP_BASELINE_SHA=$(sha256_of_file "$SHIM_LOG_DIR/caddy/Caddyfile.dewata")
DISP_CANDIDATE="$SHIM_LOG_DIR/review/caddy/Caddyfile.dewata.proposed"
DISP_RELEASE_SRC="$SHIM_LOG_DIR/review/www"
DISP_RELEASE_DST="$SHIM_LOG_DIR/www/dewata-org/v0.1.0-pre1"
DISP_PROD_CADDY="$SHIM_LOG_DIR/caddy/Caddyfile.dewata"

# Disposable isolation check: pin adapter hashes, restrict test paths
# to the disposable root, refuse to run if the real systemctl is
# reachable.  This guards against the "shell-script/shebang check does
# not prove an adapter cannot call real systemctl" objection.
export DEWATA_TEST_ROOT="$SHIM_LOG_DIR"
export DEWATA_DISPOSABLE_MODE=1
export DEWATA_SYSTEMCTL_CMD="$DISP_SYSTEMCTL"
export DEWATA_USE_DISPOSABLE_VALIDATE=1
export DEWATA_VALIDATE_CMD="$DISP_VALIDATE"
export DEWATA_PROD_CADDY="$DISP_PROD_CADDY"
export DEWATA_RELEASE_SRC="$DISP_RELEASE_SRC"
export DEWATA_RELEASE_DST="$DISP_RELEASE_DST"
export DEWATA_CANDIDATE="$DISP_CANDIDATE"
export DEWATA_REVIEWED_MANIFEST="$disp_manifest"
export DEWATA_SNAPSHOT_PARENT="$SHIM_LOG_DIR/atomic"
# shellcheck disable=SC1091
source "$WT/tests/disposable-isolation.sh"
if ! disposable_isolation_check; then
    exit 9
fi
DISP_SNAPSHOT_PARENT="$SHIM_LOG_DIR/atomic"
DISP_LISTENER_PORT="18443"

# Shim's state files (so the installer's restart calls advance the shim's
# fake PID across multiple NEGATIVE-9 / T2 runs).  The shim logs to
# /tmp/dewata-lifecycle-systemctl.log explicitly.
DISP_SYSTEMCTL_LOG="/tmp/dewata-lifecycle-systemctl.log"
DISP_SYSTEMCTL_PIDFILE="$SHIM_LOG_DIR/caddy.pid"
DISP_SYSTEMCTL_ACTIVE="$SHIM_LOG_DIR/caddy.active"

run_install() {
    # $1 = optional extra env vars to set before invoking the installer
    # sets up:
    #   /tmp/dewata-lifecycle.install.out.NNN <- install stdout for this call
    #   /tmp/dewata-lifecycle.install.err.NNN <- install stderr for this call
    #   /tmp/dewata-lifecycle.install.out       <- symlink to latest
    local extra_env="${1:-}"
    local rc
    # DO NOT wipe $SHIM_LOG: each install writes to it (the shim appends).
    # The records of every install's shim calls must survive to the end
    # of the suite so the assertion checks (T2.shim-log-non-empty,
    # NEG9.shim-call-order-restart, etc.) can read the full timeline.
    # The installer returns non-zero on every negative scenario;
    # disable -e around the call so the caller can capture rc itself.
    set +e
    local idx=$((INSTALL_CALL_IDX++))
    local out_file="/tmp/dewata-lifecycle.install.out.$idx"
    local err_file="/tmp/dewata-lifecycle.install.err.$idx"
    LAST_INSTALL_OUT="$out_file"
    LAST_INSTALL_ERR="$err_file"
    if [[ -n "$extra_env" ]]; then
        env -i \
            PATH="$SHIM_DIR:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
            DEWATA_DISPOSABLE_MODE=1 \
            DEWATA_DISPOSABLE_SERVICE_MODE=restart \
            DEWATA_DISPOSABLE_SYSTEMCTL_LOG="$DISP_SYSTEMCTL_LOG" \
            DEWATA_DISPOSABLE_SYSTEMCTL_PIDFILE="$DISP_SYSTEMCTL_PIDFILE" \
            DEWATA_DISPOSABLE_SYSTEMCTL_ACTIVE="$DISP_SYSTEMCTL_ACTIVE" \
            DEWATA_PROBE_LISTENER=0 \
            DEWATA_USE_DISPOSABLE_VALIDATE=1 \
            DEWATA_VALIDATE_CMD=$DISP_SYSTEMCTL_PATH/disposable-validate.sh \
            DEWATA_VALIDATE_LOG=$SHIM_LOG_DIR/validate.log \
                        DEWATA_PROD_CADDY="$DISP_PROD_CADDY" \
            DEWATA_PROD_WWW="$SHIM_LOG_DIR/www" \
            DEWATA_RELEASE_SRC="$DISP_RELEASE_SRC" \
            DEWATA_RELEASE_DST="$DISP_RELEASE_DST" \
            DEWATA_CANDIDATE="$DISP_CANDIDATE" \
            DEWATA_REVIEWED_MANIFEST="$disp_manifest" \
            DEWATA_PROD_BASELINE_SHA="$DISP_BASELINE_SHA" \
            DEWATA_LISTENER_PORT="$DISP_LISTENER_PORT" \
            DEWATA_WORKTREE="$WT" \
            DEWATA_SNAPSHOT_PARENT="$DISP_SNAPSHOT_PARENT" \
            DEWATA_CADDY_SERVICE=dewata-caddy \
            DEWATA_SYSTEMCTL_CMD="$DISP_SYSTEMCTL" \
            $extra_env \
            bash "$INSTALLER" \
            > "$out_file" 2> "$err_file"
    else
        env -i \
            PATH="$SHIM_DIR:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
            DEWATA_DISPOSABLE_MODE=1 \
            DEWATA_DISPOSABLE_SERVICE_MODE=restart \
            DEWATA_DISPOSABLE_SYSTEMCTL_LOG="$DISP_SYSTEMCTL_LOG" \
            DEWATA_DISPOSABLE_SYSTEMCTL_PIDFILE="$DISP_SYSTEMCTL_PIDFILE" \
            DEWATA_DISPOSABLE_SYSTEMCTL_ACTIVE="$DISP_SYSTEMCTL_ACTIVE" \
            DEWATA_PROBE_LISTENER=0 \
            DEWATA_USE_DISPOSABLE_VALIDATE=1 \
            DEWATA_VALIDATE_CMD=$DISP_SYSTEMCTL_PATH/disposable-validate.sh \
            DEWATA_VALIDATE_LOG=$SHIM_LOG_DIR/validate.log \
                        DEWATA_PROD_CADDY="$DISP_PROD_CADDY" \
            DEWATA_PROD_WWW="$SHIM_LOG_DIR/www" \
            DEWATA_RELEASE_SRC="$DISP_RELEASE_SRC" \
            DEWATA_RELEASE_DST="$DISP_RELEASE_DST" \
            DEWATA_CANDIDATE="$DISP_CANDIDATE" \
            DEWATA_REVIEWED_MANIFEST="$disp_manifest" \
            DEWATA_PROD_BASELINE_SHA="$DISP_BASELINE_SHA" \
            DEWATA_LISTENER_PORT="$DISP_LISTENER_PORT" \
            DEWATA_WORKTREE="$WT" \
            DEWATA_SNAPSHOT_PARENT="$DISP_SNAPSHOT_PARENT" \
            DEWATA_CADDY_SERVICE=dewata-caddy \
            DEWATA_SYSTEMCTL_CMD="$DISP_SYSTEMCTL" \
            bash "$INSTALLER" \
            > "$out_file" 2> "$err_file"
    fi
    rc=$?
    set -e
    # Also keep a copy at the canonical path so legacy assertions still work.
    cp "$out_file" /tmp/dewata-lifecycle.install.out
    cp "$err_file" /tmp/dewata-lifecycle.install.err
    return "$rc"
}
INSTALL_CALL_IDX=0
LAST_INSTALL_OUT=""
LAST_INSTALL_ERR=""

run_rollback() {
    local snap_dir="${1:-}"
    if [[ -z "$snap_dir" ]]; then
        echo "ERROR: run_rollback requires a snapshot dir argument" >&2
        return 1
    fi
    env -i \
        PATH="$SHIM_DIR:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
        DEWATA_DISPOSABLE_MODE=1 \
        DEWATA_DISPOSABLE_SERVICE_MODE=restart \
        DEWATA_PROD_CADDY="$DISP_PROD_CADDY" \
        DEWATA_RELEASE_DST="$DISP_RELEASE_DST" \
        DEWATA_LISTENER_PORT="$DISP_LISTENER_PORT" \
        DEWATA_WORKTREE="$WT" \
        DEWATA_SNAPSHOT_DIR="$snap_dir" \
        DEWATA_SYSTEMCTL_CMD="$DISP_SYSTEMCTL" \
        DEWATA_DISPOSABLE_SYSTEMCTL_LOG="$DISP_SYSTEMCTL_LOG" \
        DEWATA_DISPOSABLE_SYSTEMCTL_PIDFILE="$DISP_SYSTEMCTL_PIDFILE" \
        DEWATA_DISPOSABLE_SYSTEMCTL_ACTIVE="$DISP_SYSTEMCTL_ACTIVE" \
        DEWATA_PROBE_LISTENER=0 \
            DEWATA_USE_DISPOSABLE_VALIDATE=1 \
            DEWATA_VALIDATE_CMD=$DISP_SYSTEMCTL_PATH/disposable-validate.sh \
            DEWATA_VALIDATE_LOG=$SHIM_LOG_DIR/validate.log \
                    DEWATA_CADDY_SERVICE=dewata-caddy \
        bash "$ROLLBACK" "$snap_dir" \
        > /tmp/dewata-lifecycle.rollback.out 2> /tmp/dewata-lifecycle.rollback.err
    return $?
}

reset_disposable_caddyfile() {
    cp "$SHIM_LOG_DIR/caddy/Caddyfile.dewata.runtime" "$SHIM_LOG_DIR/caddy/Caddyfile.dewata"
}

# Verify production state (BEFORE the suite).
record_prod_state
PROD_BEFORE_SHA="$PROD_CADDY_SHA"
PROD_BEFORE_PID="$PROD_PID"

echo "================================================================"
echo "[lifecycle] suite starts at $(date -u +%Y%m%dT%H%M%SZ)"
echo "[lifecycle] production Caddyfile sha256 = $PROD_BEFORE_SHA"
echo "[lifecycle] production dewata-caddy MainPID = $PROD_BEFORE_PID"
echo "================================================================"

# ====================================================================
# T1: confirm production was untouched before we even ran install.
# ====================================================================
record "T1.prod-untouched-before-suite" PASS "prod_sha=$PROD_BEFORE_SHA prod_pid=$PROD_BEFORE_PID"

# ====================================================================
# T2: positive install -- candidate != runtime, install succeeds.
# ====================================================================
echo
echo "================================================================"
echo "[lifecycle] T2: positive install"
echo "================================================================"
# the candidate differs from the runtime: drop the candidate in
cp "$SHIM_LOG_DIR/caddy/Caddyfile.dewata.runtime" "$SHIM_LOG_DIR/caddy/Caddyfile.dewata"
# Actual candidate from bundle goes through 02-candidate-Caddyfile
# (already in DISP_CANDIDATE).

rc=0
run_install || rc=$?
record "T2.install.rc-zero"           "$([[ $rc -eq 0 ]] && echo PASS || echo FAIL)" "rc=$rc"

if [[ $rc -eq 0 ]]; then
    actual_snap=$(grep -E '^[[:space:]]*actual_snapshot_path=' /tmp/dewata-lifecycle.install.out | head -1 | cut -d= -f2-)
    if [[ -n "$actual_snap" && -d "$actual_snap" ]]; then
        record "T2.install.actual-snapshot-printed" PASS "$actual_snap"
    else
        record "T2.install.actual-snapshot-printed" FAIL "no actual_snapshot_path= line"
    fi

    # caddyfile at DISP_PROD_CADDY must equal the candidate sha now
    actual_caddy_sha=$(sha256_of_file "$DISP_PROD_CADDY")
    if [[ "$actual_caddy_sha" == "$CAND_SHA" ]]; then
        record "T2.caddyfile-match-candidate" PASS "$actual_caddy_sha"
    else
        record "T2.caddyfile-match-candidate" FAIL "got $actual_caddy_sha, want $CAND_SHA"
    fi

    # release tree at DISP_RELEASE_DST must exist and match manifest
    if [[ -d "$DISP_RELEASE_DST" ]]; then
        record "T2.release-dst-exists" PASS
        n_published=$(find "$DISP_RELEASE_DST" -type f -not -name ".counters" | wc -l)
        n_manifest=$(awk '/^[a-f0-9]/{print $2}' "$disp_manifest" | grep -v "^Caddyfile.dewata.proposed$" | wc -l)
        if [[ "$n_published" -eq "$n_manifest" ]]; then
            record "T2.release-dst-file-count-matches-manifest" PASS "$n_published files"
        else
            record "T2.release-dst-file-count-matches-manifest" FAIL "published=$n_published manifest=$n_manifest"
        fi
    else
        record "T2.release-dst-exists" FAIL "$DISP_RELEASE_DST missing"
    fi

    # the shim log must exist (asserts the install called systemctl, and
    # that the script's PATH resolved the shim first)
    if [[ -f "$SHIM_LOG" ]] && [[ -s "$SHIM_LOG" ]]; then
        record "T2.shim-log-non-empty" PASS
    else
        record "T2.shim-log-non-empty" FAIL "shim log $SHIM_LOG is missing or empty"
    fi
    # the shim log must NOT show any passthrough to the real systemctl
    if [[ -f "$SHIM_LOG" ]] && ! grep -q "passthrough" "$SHIM_LOG"; then
        record "T2.no-systemctl-passthrough" PASS
    else
        record "T2.no-systemctl-passthrough" FAIL "shim fell through to real systemctl:"
        grep "passthrough" "$SHIM_LOG" 2>/dev/null | sed "s|^|      |" | head -5
    fi
    # the shim log must show a `show dewata-caddy -p MainPID` entry (G6
    # captures pre-restart MainPID) -- this proves the install path went
    # through the shim and did NOT reach the real systemctl.  In
    # disposable mode the install skips the actual `restart` call (the
    # driver launches caddy as a child process) so we don't expect a
    # `restart` line.  In production mode, the install calls
    # `systemctl restart` and we would expect that; the production
    # bundle asserts the same shim log shape.
    if [[ -f "$SHIM_LOG" ]] && grep -q "show dewata-caddy -p MainPID" "$SHIM_LOG"; then
        record "T2.shim-captures-MainPID" PASS
    else
        record "T2.shim-captures-MainPID" FAIL "shim log lacks 'show dewata-caddy -p MainPID' line"
    fi

    # Save the actual snap for T3
    SAVE_SNAP="$actual_snap"
fi

# ====================================================================
# T3: rollback restores the caddyfile byte-for-byte.
# ====================================================================
echo
echo "================================================================"
echo "[lifecycle] T3: rollback from positive install"
echo "================================================================"
if [[ -z "$SAVE_SNAP" ]]; then
    record "T3.skip-no-snapshot" FAIL "no SAVE_SNAP from T2"
else
    PRE_ROLLBACK_SHA=$(sha256_of_file "$DISP_PROD_CADDY")
    # snapshot the runtime sha (NOT the live disposable caddyfile -- the live
    # disposable caddyfile is the candidate post-install).
    EXPECTED_POST_ROLLBACK_SHA=$(sha256_of_file "$SHIM_LOG_DIR/caddy/Caddyfile.dewata.runtime")

    run_rollback "$SAVE_SNAP" || rc=$?
    rc=$?
    record "T3.rollback.rc-zero"                  "$([[ $rc -eq 0 ]] && echo PASS || echo FAIL)" "rc=$rc"

    POST_ROLLBACK_SHA=$(sha256_of_file "$DISP_PROD_CADDY")
    if [[ "$POST_ROLLBACK_SHA" == "$EXPECTED_POST_ROLLBACK_SHA" ]]; then
        record "T3.caddyfile-match-runtime"  PASS "restored to $EXPECTED_POST_ROLLBACK_SHA"
    else
        record "T3.caddyfile-match-runtime"  FAIL "got $POST_ROLLBACK_SHA, want $EXPECTED_POST_ROLLBACK_SHA"
    fi
    # restore the snapshot's runtime file to its "before-rollback" state
    # so subsequent tests have a clean baseline.
    cp "$SHIM_LOG_DIR/caddy/Caddyfile.dewata.runtime" "$DISP_PROD_CADDY"
fi

# ====================================================================
# Re-check production is unchanged.
# ====================================================================
record_prod_state
if [[ "$PROD_CADDY_SHA" == "$PROD_BEFORE_SHA" && "$PROD_PID" == "$PROD_BEFORE_PID" ]]; then
    record "T4.prod-untouched-after-positive" PASS
else
    record "T4.prod-untouched-after-positive" FAIL "prod_sha changed $PROD_BEFORE_SHA -> $PROD_CADDY_SHA or pid changed $PROD_BEFORE_PID -> $PROD_PID"
fi

# ====================================================================
# NEGATIVE-1: manifest-lists-file-but-file-missing-in-RELEASE_SRC
# ====================================================================
echo
echo "================================================================"
echo "[lifecycle] NEGATIVE-1: missing file in RELEASE_SRC"
echo "================================================================"
reset_disposable_caddyfile

# Make a disposable release source that is missing one manifest-listed file.
rm -f "$DISP_RELEASE_SRC/index.html"

rc=0
run_install || rc=$?
if [[ $rc -ne 0 ]]; then
    record "NEG1.install-rejected" PASS "rc=$rc"
else
    record "NEG1.install-rejected" FAIL "install accepted a release source with a missing file, rc=0"
fi
# restore the missing file
cp "$WT/deploy/www/dewata-org/v0.1.0-pre1/index.html" "$DISP_RELEASE_SRC/index.html"

record_prod_state
if [[ "$PROD_CADDY_SHA" == "$PROD_BEFORE_SHA" && "$PROD_PID" == "$PROD_BEFORE_PID" ]]; then
    record "NEG1.prod-untouched" PASS
else
    record "NEG1.prod-untouched" FAIL
fi

# ====================================================================
# NEGATIVE-2: extra file in RELEASE_SRC (not listed in manifest)
# ====================================================================
echo
echo "================================================================"
echo "[lifecycle] NEGATIVE-2: extra file in RELEASE_SRC"
echo "================================================================"
reset_disposable_caddyfile
echo "extra-file-content" > "$DISP_RELEASE_SRC/extra-unlisted.html"

rc=0
run_install || rc=$?
if [[ $rc -ne 0 ]]; then
    record "NEG2.install-rejected" PASS "rc=$rc"
else
    record "NEG2.install-rejected" FAIL "install accepted a release source with an extra file, rc=0"
fi
rm -f "$DISP_RELEASE_SRC/extra-unlisted.html"

# ====================================================================
# NEGATIVE-3: symlink in RELEASE_SRC
# ====================================================================
echo
echo "================================================================"
echo "[lifecycle] NEGATIVE-3: symlink in RELEASE_SRC"
echo "================================================================"
reset_disposable_caddyfile
ln -s /etc/passwd "$DISP_RELEASE_SRC/passwd-symlink"

rc=0
run_install || rc=$?
if [[ $rc -ne 0 ]]; then
    record "NEG3.install-rejected" PASS "rc=$rc"
else
    record "NEG3.install-rejected" FAIL "install accepted a release source with a symlink, rc=0"
fi
rm -f "$DISP_RELEASE_SRC/passwd-symlink"

# ====================================================================
# NEGATIVE-4: baseline drift
# ====================================================================
echo
echo "================================================================"
echo "[lifecycle] NEGATIVE-4: baseline drift"
echo "================================================================"
reset_disposable_caddyfile
# Override the baseline sha to a wrong value
rc=0
run_install DEWATA_PROD_BASELINE_SHA_OVERRIDE="0000000000000000000000000000000000000000000000000000000000000000" EXTRA_TEST_HOLD="1" || rc=$?
# The installer doesn't read this var; we need to actually override the
# env var it reads.  Use a sub-shell env wrapper.
(env -i \
    PATH="$SHIM_DIR:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    DEWATA_DISPOSABLE_MODE=1 \
    DEWATA_PROD_CADDY="$DISP_PROD_CADDY" \
    DEWATA_PROD_WWW="$SHIM_LOG_DIR/www" \
    DEWATA_RELEASE_SRC="$DISP_RELEASE_SRC" \
    DEWATA_RELEASE_DST="$DISP_RELEASE_DST" \
    DEWATA_CANDIDATE="$DISP_CANDIDATE" \
    DEWATA_REVIEWED_MANIFEST="$disp_manifest" \
    DEWATA_PROD_BASELINE_SHA="0000000000000000000000000000000000000000000000000000000000000000" \
    DEWATA_LISTENER_PORT="$DISP_LISTENER_PORT" \
    DEWATA_WORKTREE="$WT" \
    DEWATA_SNAPSHOT_PARENT="$DISP_SNAPSHOT_PARENT" \
    DEWATA_CADDY_SERVICE=dewata-caddy \
    DEWATA_SYSTEMCTL_CMD="$DISP_SYSTEMCTL" \
    bash "$INSTALLER" > /tmp/dewata-lifecycle.install.out 2>&1) || rc=$?
# Override the rc above
if [[ $rc -eq 3 ]]; then
    record "NEG4.install-rejected-drift" PASS "rc=$rc (drift-detected)"
elif [[ $rc -ne 0 ]]; then
    record "NEG4.install-rejected"      PASS "rc=$rc (non-zero)"
else
    record "NEG4.install-rejected-drift" FAIL "install ran with a wrong baseline, rc=0"
fi

# ====================================================================
# NEGATIVE-5: missing required env var
# ====================================================================
echo
echo "================================================================"
echo "[lifecycle] NEGATIVE-5: missing required env var"
echo "================================================================"
reset_disposable_caddyfile
(env -i \
    PATH="$SHIM_DIR:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    DEWATA_DISPOSABLE_MODE=1 \
    DEWATA_PROD_CADDY="$DISP_PROD_CADDY" \
    DEWATA_PROD_WWW="$SHIM_LOG_DIR/www" \
    DEWATA_RELEASE_SRC="$DISP_RELEASE_SRC" \
    DEWATA_RELEASE_DST="$DISP_RELEASE_DST" \
    DEWATA_CANDIDATE="$DISP_CANDIDATE" \
    DEWATA_REVIEWED_MANIFEST="$disp_manifest" \
    DEWATA_PROD_BASELINE_SHA="$DISP_BASELINE_SHA" \
    DEWATA_LISTENER_PORT="$DISP_LISTENER_PORT" \
    DEWATA_WORKTREE="$WT" \
    DEWATA_CADDY_SERVICE=dewata-caddy \
    DEWATA_SYSTEMCTL_CMD="$DISP_SYSTEMCTL" \
    bash "$INSTALLER" > /tmp/dewata-lifecycle.install.out 2>&1) || rc=$?
if [[ $rc -ne 0 ]]; then
    record "NEG5.install-rejected-missing-env" PASS "rc=$rc"
else
    record "NEG5.install-rejected-missing-env" FAIL "install ran with missing DEWATA_SNAPSHOT_PARENT, rc=0"
fi

# ====================================================================
# NEGATIVE-6: post-publish failure (g3-post-publish)
# ====================================================================
echo
echo "================================================================"
echo "[lifecycle] NEGATIVE-6: post-publish failure (FIRST-INSTALL end-to-end)"
echo "================================================================"
reset_disposable_caddyfile
# Ensure FIRST-INSTALL: release tree must NOT exist before this run.
if [[ -d "$DISP_RELEASE_DST" ]]; then
    rm -rf "$DISP_RELEASE_DST"
fi
first_install_pre_release_existed=0
rc=0
run_install "DEWATA_FAKE_FAIL_AT_GATE=g3-post-publish" || rc=$?
if [[ $rc -ne 0 ]]; then
    record "NEG6.install-rejected" PASS "rc=$rc"
else
    record "NEG6.install-rejected" FAIL "rc=0"
fi
# verify the installer's auto-restore restored the disposable caddyfile
post_run_sha=$(sha256_of_file "$DISP_PROD_CADDY")
if [[ "$post_run_sha" == "$DISP_BASELINE_SHA" ]]; then
    record "NEG6.caddyfile-restored" PASS "$post_run_sha"
else
    record "NEG6.caddyfile-restored" FAIL "got $post_run_sha want $DISP_BASELINE_SHA"
fi
# FIRST-INSTALL end-state check: $DISP_RELEASE_DST must NOT exist.
if [[ ! -e "$DISP_RELEASE_DST" ]]; then
    record "NEG6.release-tree-removed" PASS "first-install end state: $DISP_RELEASE_DST absent"
else
    record "NEG6.release-tree-removed" FAIL "first-install end state: $DISP_RELEASE_DST still exists"
fi
# Log must show "FIRST-INSTALL mode" as the path do_restore took
if grep -q "FIRST-INSTALL mode" "$LAST_INSTALL_OUT"; then
    record "NEG6.do-restore-took-FIRST-INSTALL-mode" PASS
else
    record "NEG6.do-restore-took-FIRST-INSTALL-mode" FAIL
fi

# ====================================================================
# NEGATIVE-7: post-G4 failure (caddyfile installed but G5 not started)
# ====================================================================
echo
echo "================================================================"
echo "[lifecycle] NEGATIVE-7: post-G4 failure (REPLACEMENT end-to-end)"
echo "================================================================"
reset_disposable_caddyfile
# Set up REPLACEMENT scenario: a prior release must exist at $DISP_RELEASE_DST.
# We seed it with a sentinel file whose sha we know, then verify it survives
# do_restore byte-for-byte.
SENTINEL_REL="sentinel-prior-release.html"
SENTINEL_CONTENT="<html><body>prior release sentinel</body></html>"
SENTINEL_SHA=$(printf "%s" "$SENTINEL_CONTENT" | sha256sum | cut -d' ' -f1)
mkdir -p "$DISP_RELEASE_DST"
printf "%s" "$SENTINEL_CONTENT" > "$DISP_RELEASE_DST/$SENTINEL_REL"
SENTINEL_BACKUP_SHA=$(sha256_of_file "$DISP_RELEASE_DST/$SENTINEL_REL")
# Reset the disposable caddyfile so install picks up the (different) candidate.
reset_disposable_caddyfile
# Override production baseline to match the caddyfile as it is now.
NEW_BASELINE=$(sha256_of_file "$DISP_PROD_CADDY")

# Wrapper that lets us pass DEWATA_PROD_BASELINE_SHA without a run_install refactor.
run_install_with_overrides() {
    local extra="$1"
    local rc
    set +e
    local idx=$((INSTALL_CALL_IDX++))
    LAST_INSTALL_OUT="/tmp/dewata-lifecycle.install.out.$idx"
    LAST_INSTALL_ERR="/tmp/dewata-lifecycle.install.err.$idx"
    (env -i \
        PATH="$SHIM_DIR:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
        DEWATA_DISPOSABLE_MODE=1 \
        DEWATA_DISPOSABLE_SERVICE_MODE=restart \
        DEWATA_PROD_CADDY="$DISP_PROD_CADDY" \
        DEWATA_PROD_WWW="$SHIM_LOG_DIR/www" \
        DEWATA_RELEASE_SRC="$DISP_RELEASE_SRC" \
        DEWATA_RELEASE_DST="$DISP_RELEASE_DST" \
        DEWATA_CANDIDATE="$DISP_CANDIDATE" \
        DEWATA_REVIEWED_MANIFEST="$disp_manifest" \
        DEWATA_PROD_BASELINE_SHA="$NEW_BASELINE" \
        DEWATA_LISTENER_PORT="$DISP_LISTENER_PORT" \
        DEWATA_WORKTREE="$WT" \
        DEWATA_SNAPSHOT_PARENT="$DISP_SNAPSHOT_PARENT" \
        DEWATA_CADDY_SERVICE=dewata-caddy \
        DEWATA_SYSTEMCTL_CMD="$DISP_SYSTEMCTL" \
        DEWATA_DISPOSABLE_SYSTEMCTL_LOG="$DISP_SYSTEMCTL_LOG" \
        DEWATA_DISPOSABLE_SYSTEMCTL_PIDFILE="$DISP_SYSTEMCTL_PIDFILE" \
        DEWATA_DISPOSABLE_SYSTEMCTL_ACTIVE="$DISP_SYSTEMCTL_ACTIVE" \
        DEWATA_PROBE_LISTENER=0 \
            DEWATA_USE_DISPOSABLE_VALIDATE=1 \
            DEWATA_VALIDATE_CMD=$DISP_SYSTEMCTL_PATH/disposable-validate.sh \
            DEWATA_VALIDATE_LOG=$SHIM_LOG_DIR/validate.log \
                    $extra \
        bash "$INSTALLER" \
        > "$LAST_INSTALL_OUT" 2> "$LAST_INSTALL_ERR")
    rc=$?
    set -e
    return "$rc"
}

run_install_with_overrides "DEWATA_FAKE_FAIL_AT_GATE=g4" || rc=$?
if [[ $rc -ne 0 ]]; then
    record "NEG7.install-rejected" PASS "rc=$rc"
else
    record "NEG7.install-rejected" FAIL "rc=0"
fi
post_run_sha=$(sha256_of_file "$DISP_PROD_CADDY")
if [[ "$post_run_sha" == "$NEW_BASELINE" ]]; then
    record "NEG7.caddyfile-restored" PASS "$post_run_sha"
else
    record "NEG7.caddyfile-restored" FAIL "got $post_run_sha want $NEW_BASELINE"
fi
# REPLACEMENT end-state: the prior release (the one with our sentinel) must
# be restored byte-for-byte.
SENTINEL_AFTER_SHA=$(sha256_of_file "$DISP_RELEASE_DST/$SENTINEL_REL" 2>/dev/null || echo MISSING)
if [[ "$SENTINEL_AFTER_SHA" == "$SENTINEL_BACKUP_SHA" ]]; then
    record "NEG7.prior-release-sentinel-restored-byte-for-byte" PASS "sentinel sha matches ($SENTINEL_SHA)"
else
    record "NEG7.prior-release-sentinel-restored-byte-for-byte" FAIL "got $SENTINEL_AFTER_SHA want $SENTINEL_BACKUP_SHA"
fi
# The installer log must show "REPLACEMENT mode" do_restore step 2
if grep -q "REPLACEMENT mode: restoring prior release" "$LAST_INSTALL_OUT"; then
    record "NEG7.do-restore-took-REPLACEMENT-mode" PASS
else
    record "NEG7.do-restore-took-REPLACEMENT-mode" FAIL
fi
# Cleanup sentinel from the restored release
rm -f "$DISP_RELEASE_DST/$SENTINEL_REL"

# ====================================================================
# NEGATIVE-8: post-G5 failure (caddyfile installed and validated, G6 not started)
# ====================================================================
echo
echo "================================================================"
echo "[lifecycle] NEGATIVE-8: post-G5 failure"
echo "================================================================"
reset_disposable_caddyfile
rc=0
run_install "DEWATA_FAKE_FAIL_AT_GATE=g5" || rc=$?
if [[ $rc -ne 0 ]]; then
    record "NEG8.install-rejected" PASS "rc=$rc"
else
    record "NEG8.install-rejected" FAIL "rc=0"
fi
post_run_sha=$(sha256_of_file "$DISP_PROD_CADDY")
if [[ "$post_run_sha" == "$DISP_BASELINE_SHA" ]]; then
    record "NEG8.caddyfile-restored" PASS "$post_run_sha"
else
    record "NEG8.caddyfile-restored" FAIL "got $post_run_sha want $DISP_BASELINE_SHA"
fi

# ====================================================================
# NEGATIVE-9: post-G6 failure (after restart)
# ====================================================================
echo
echo "================================================================"
echo "[lifecycle] NEGATIVE-9: post-G6 restart failure (real restart through shim)"
echo "================================================================"
reset_disposable_caddyfile
# Ensure FIRST-INSTALL end-state so do_restore's FIRST-INSTALL branch runs.
if [[ -d "$DISP_RELEASE_DST" ]]; then
    rm -rf "$DISP_RELEASE_DST"
fi
PRE_SHIM_PID=$( (cat "$DISP_SYSTEMCTL_PIDFILE" 2>/dev/null || echo 0) )
PRE_SHIM_ACTIVE=$( (cat "$DISP_SYSTEMCTL_ACTIVE" 2>/dev/null || echo 0) )
rc=0
run_install "DEWATA_FAKE_RESTART_FAILURE=1 DEWATA_FAKE_FAIL_AT_GATE=g6" || rc=$?
if [[ $rc -ne 0 ]]; then
    record "NEG9.install-rejected" PASS "rc=$rc"
else
    record "NEG9.install-rejected" FAIL "rc=0"
fi
# Verify the shim log shows the install ACTUALLY issued a restart before
# the failure (NOT just a MainPID lookup).
if grep -q "restart dewata-caddy" "$SHIM_LOG"; then
    record "NEG9.shim-executed-restart" PASS "shim log shows 'restart dewata-caddy' line"
else
    record "NEG9.shim-executed-restart" FAIL "shim log lacks restart call"
fi
# Verify the shim log shows the FAKE_FAILURE is the result of the restart, NOT
# the result of skipping the restart.
if grep -q "FAKE_FAILURE" "$SHIM_LOG"; then
    record "NEG9.shim-injected-restart-failure" PASS "shim log shows FAKE_FAILURE during restart"
else
    record "NEG9.shim-injected-restart-failure" FAIL "shim log lacks FAKE_FAILURE"
fi
# Verify the shim call ORDER (correction 3):
#   For NEG-9 (post-restart-failure), the LAST 3 entries in the log
#   corresponding to NEG-9's restart must show:
#     1. show -p MainPID (pre-restart MainPID lookup)
#     2. restart (the restart call, which logged FAKE_FAILURE)
#     3. show -p MainPID (post-restart MainPID lookup)
# Since NEG-9b may run after NEG-9, the last 3 FAKE_FAILURE restart
# patterns may be from NEG-9 OR NEG-9b.  We isolate the LAST
# FAKE_FAILURE line and the surrounding show patterns.
FAKE_FAILURE_LINES=$(grep -nE "restart.*FAKE_FAILURE" "$SHIM_LOG" | tail -1 | cut -d: -f1)
if [[ -z "$FAKE_FAILURE_LINES" ]]; then
    record "NEG9.shim-call-order-restart" FAIL "no FAKE_FAILURE line in shim log"
else
    # Window: from 2 lines before FAKE_FAILURE to 2 lines after.
    win_lo=$((FAKE_FAILURE_LINES - 2))
    win_hi=$((FAKE_FAILURE_LINES + 2))
    window=$(awk -v lo="$win_lo" -v hi="$win_hi" 'NR>=lo && NR<=hi' "$SHIM_LOG")
    show_before=$(echo "$window" | head -3 | grep -c "show.*-p MainPID")
    show_after=$(echo "$window" | tail -3 | grep -c "show.*-p MainPID")
    if (( show_before >= 1 )) && (( show_after >= 1 )); then
        record "NEG9.shim-call-order-restart" PASS "show appears before and after the FAKE_FAILURE restart"
    else
        record "NEG9.shim-call-order-restart" FAIL "show order off around FAKE_FAILURE (before=$show_before after=$show_after)"
    fi
fi
# Verify the do_restore path also runs (real recovery after a real restart
# failure).  In disposable+restart mode the FIRST-INSTALL end state after
# do_restore is: $DISP_RELEASE_DST does NOT exist (do_restore removed the
# freshly-published release).  The caddyfile IS restored to baseline.
if [[ ! -e "$DISP_RELEASE_DST" ]]; then
    record "NEG9.first-install-end-state" PASS "DISP_RELEASE_DST removed (FIRST-INSTALL end state)"
else
    record "NEG9.first-install-end-state" FAIL "DISP_RELEASE_DST still present; expected FIRST-INSTALL removal"
fi
# Verify caddyfile is restored to baseline
post_run_sha=$(sha256_of_file "$DISP_PROD_CADDY")
if [[ "$post_run_sha" == "$DISP_BASELINE_SHA" ]]; then
    record "NEG9.caddyfile-restored-after-failed-restart" PASS "$post_run_sha"
else
    record "NEG9.caddyfile-restored-after-failed-restart" FAIL
fi

# ====================================================================
# NEGATIVE-9b: post-G6 restart failure (REPLACEMENT mode end-to-end)
#   Same restart-failure scenario as NEG-9, but seeded with a prior release
#   so REPLACEMENT mode is exercised.
# ====================================================================
echo
echo "================================================================"
echo "[lifecycle] NEGATIVE-9b: post-G6 restart failure (REPLACEMENT mode)"
echo "================================================================"
reset_disposable_caddyfile
mkdir -p "$DISP_RELEASE_DST"
# Sentinel for the prior release
printf "%s" "prior-release-9b" > "$DISP_RELEASE_DST/sentinel.html"
SENTINEL_BACKUP_SHA=$(sha256_of_file "$DISP_RELEASE_DST/sentinel.html")
reset_disposable_caddyfile

NEW_BASELINE2=$(sha256_of_file "$DISP_PROD_CADDY")

run_install_with_overrides() {
    local extra="$1"
    local rc
    set +e
    local idx=$((INSTALL_CALL_IDX++))
    LAST_INSTALL_OUT="/tmp/dewata-lifecycle.install.out.$idx"
    LAST_INSTALL_ERR="/tmp/dewata-lifecycle.install.err.$idx"
    (env -i \
        PATH="$SHIM_DIR:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
        DEWATA_DISPOSABLE_MODE=1 \
        DEWATA_DISPOSABLE_SERVICE_MODE=restart \
        DEWATA_PROD_CADDY="$DISP_PROD_CADDY" \
        DEWATA_PROD_WWW="$SHIM_LOG_DIR/www" \
        DEWATA_RELEASE_SRC="$DISP_RELEASE_SRC" \
        DEWATA_RELEASE_DST="$DISP_RELEASE_DST" \
        DEWATA_CANDIDATE="$DISP_CANDIDATE" \
        DEWATA_REVIEWED_MANIFEST="$disp_manifest" \
        DEWATA_PROD_BASELINE_SHA="$NEW_BASELINE2" \
        DEWATA_LISTENER_PORT="$DISP_LISTENER_PORT" \
        DEWATA_WORKTREE="$WT" \
        DEWATA_SNAPSHOT_PARENT="$DISP_SNAPSHOT_PARENT" \
        DEWATA_CADDY_SERVICE=dewata-caddy \
        DEWATA_SYSTEMCTL_CMD="$DISP_SYSTEMCTL" \
        DEWATA_DISPOSABLE_SYSTEMCTL_LOG="$DISP_SYSTEMCTL_LOG" \
        DEWATA_DISPOSABLE_SYSTEMCTL_PIDFILE="$DISP_SYSTEMCTL_PIDFILE" \
        DEWATA_DISPOSABLE_SYSTEMCTL_ACTIVE="$DISP_SYSTEMCTL_ACTIVE" \
        DEWATA_PROBE_LISTENER=0 \
            DEWATA_USE_DISPOSABLE_VALIDATE=1 \
            DEWATA_VALIDATE_CMD=$DISP_SYSTEMCTL_PATH/disposable-validate.sh \
            DEWATA_VALIDATE_LOG=$SHIM_LOG_DIR/validate.log \
                    $extra \
        bash "$INSTALLER" \
        > "$LAST_INSTALL_OUT" 2> "$LAST_INSTALL_ERR")
    rc=$?
    set -e
    return "$rc"
}

run_install_with_overrides "DEWATA_FAKE_RESTART_FAILURE=1 DEWATA_FAKE_FAIL_AT_GATE=g6" || rc=$?
if [[ $rc -ne 0 ]]; then
    record "NEG9b.install-rejected" PASS "rc=$rc"
else
    record "NEG9b.install-rejected" FAIL "rc=0"
fi
SENTINEL_AFTER=$(sha256_of_file "$DISP_RELEASE_DST/sentinel.html" 2>/dev/null || echo MISSING)
if [[ "$SENTINEL_AFTER" == "$SENTINEL_BACKUP_SHA" ]]; then
    record "NEG9b.prior-release-sentinel-restored" PASS
else
    record "NEG9b.prior-release-sentinel-restored" FAIL
fi
if grep -q "REPLACEMENT mode: restoring prior release" "$LAST_INSTALL_OUT"; then
    record "NEG9b.do-restore-took-REPLACEMENT-mode" PASS
else
    record "NEG9b.do-restore-took-REPLACEMENT-mode" FAIL
fi
rm -f "$DISP_RELEASE_DST/sentinel.html"

# ====================================================================
# NEGATIVE-10: recovery-validation failure.
#
# We intentionally do NOT corrupt the snapshot file (which would
# simulate a wrong-sha only after restore; the user explicitly
# directed "Do not corrupt the recovery snapshot").  Instead we
# inject the failure into the disposable validation adapter via
# DEWATA_FAKE_VALIDATE_FAILURE=1.
#
# Assertions (per the reviewer's instruction that "any nonzero
# exit is insufficient"):
#   - installer exits rc=2 (AUTO-RESTORE INCOMPLETE)
#   - installer output contains "AUTO-RESTORE INCOMPLETE"
#   - installer output contains "RESTORE FAILED" on the validation step
#   - **installer output does NOT contain "service restarted:"** because
#     do_restore's step 5 (restart) is GATED on restore_failed=0.
#   - **the snapshot file at $SNAPSHOT_DIR/Caddyfile.dewata.runtime is
#     INTACT** (sha unchanged from before NEG-10 ran).
#   - the Caddyfile on disk at $DISP_PROD_CADDY matches the baseline
#     (do_restore's step 1 put it back).
#   - the disposable validate adapter's log shows the FAKE_FAILURE line.
# ====================================================================
echo
echo "================================================================"
echo "[lifecycle] NEGATIVE-10: failure during recovery (FAKE_VALIDATE)"
echo "================================================================"
reset_disposable_caddyfile

# Find an existing snapshot dir to use as the "before NEG-10" reference.
# (T2 has populated at least one snapshot.)
DISP_SNAPSHOT_PARENT_PRE_NEG10_DIR=$(ls -td "$DISP_SNAPSHOT_PARENT"/*-pre-apex 2>/dev/null | head -1)
if [[ -z "$DISP_SNAPSHOT_PARENT_PRE_NEG10_DIR" ]] || [[ ! -f "$DISP_SNAPSHOT_PARENT_PRE_NEG10_DIR/Caddyfile.dewata.runtime" ]]; then
    echo "FATAL: NEG-10 cannot find a pre-existing snapshot to use as the intact-snapshot reference" >&2
    exit 2
fi
PRE_NEG10_SNAPSHOT_SHA=$(sha256_of_file "$DISP_SNAPSHOT_PARENT_PRE_NEG10_DIR/Caddyfile.dewata.runtime")
echo "[lifecycle] NEG10 PRE_SNAPSHOT_SHA=$PRE_NEG10_SNAPSHOT_SHA ($DISP_SNAPSHOT_PARENT_PRE_NEG10_DIR/Caddyfile.dewata.runtime)"

# Seed REPLACEMENT mode: NEG-9b's setup left the release tree empty
# after its rm cleanup.  Re-create the prior-release sentinel so the
# install's G3 sees a non-empty prior and exercises the
# REPLACEMENT-mode snapshot capture path.
mkdir -p "$DISP_RELEASE_DST"
printf "%s" "prior-release-10" > "$DISP_RELEASE_DST/sentinel.html"
NEG10_SENTINEL_SHA=$(sha256_of_file "$DISP_RELEASE_DST/sentinel.html")
echo "[lifecycle] NEG10 seeded prior-release sentinel sha=$NEG10_SENTINEL_SHA"

rc=0

# Run install with: g5-failure (after snapshot + after candidate install
# + after do_validate at G5).  We pass DEWATA_FAKE_FAIL_AT_GATE=g5 so
# the install's do_restore is invoked from INSIDE G5, where the
# snapshot exists.
#
# DEWATA_FAKE_VALIDATE_FAILURE_GATES=g5 -- restrict the FAKE validate
# failure to ONLY the G5 call site (not G1).  G1 must succeed so
# the snapshot is captured.
#
# NOTE: env -i inside run_install clears the env, so any hooks must
# be passed via the extra_env arg so they reach the installer process.
run_install "DEWATA_FAKE_FAIL_AT_GATE=g5 DEWATA_USE_DISPOSABLE_VALIDATE=1 DEWATA_FAKE_VALIDATE_FAILURE=1 DEWATA_FAKE_VALIDATE_FAILURE_GATES=g5,restore DEWATA_VALIDATE_CMD=$DISP_SYSTEMCTL_PATH/disposable-validate.sh DEWATA_VALIDATE_LOG=$SHIM_LOG_DIR/validate.log" || rc=$?

# Assertion 1: rc=2 (not just "any nonzero") -- AUTO-RESTORE INCOMPLETE
if [[ $rc -eq 2 ]]; then
    record "NEG10.install-rc-is-2" PASS "rc=$rc exactly (AUTO-RESTORE INCOMPLETE)"
else
    record "NEG10.install-rc-is-2" FAIL "got rc=$rc expected rc=2"
fi

# NEG-10 assertions inspect BOTH stdout and stderr (do_restore prints
# INCOMPLETE / RESTORE FAILED to stderr; installer info to stdout).
NEG10_COMBINED_LOG="$LAST_INSTALL_OUT"
if [[ -s "$LAST_INSTALL_ERR" ]]; then
    NEG10_COMBINED_LOG="/tmp/dewata-lifecycle.NEG10.combined"
    cat "$LAST_INSTALL_OUT" "$LAST_INSTALL_ERR" > "$NEG10_COMBINED_LOG"
fi

# Assertion 2: AUTO-RESTORE INCOMPLETE printed (stderr, but check combined)
if grep -q "AUTO-RESTORE INCOMPLETE" "$NEG10_COMBINED_LOG"; then
    record "NEG10.AUTO-RESTORE-INCOMPLETE-printed" PASS
else
    record "NEG10.AUTO-RESTORE-INCOMPLETE-printed" FAIL "AUTO-RESTORE INCOMPLETE missing"
fi

# Assertion 3: RESTORE FAILED printed on the validate step
if grep -qE "RESTORE FAILED.*does not validate|FAKE_VALIDATE_FAILURE|validation failed|validate failed|Invalid Caddyfile" "$NEG10_COMBINED_LOG"; then
    record "NEG10.VALIDATE-FAILED-printed" PASS
else
    record "NEG10.VALIDATE-FAILED-printed" FAIL "no validation-failure log line"
fi

# Assertion 4: NO "service restarted:" line in the post-restore output
# (this proves do_restore did NOT call systemctl restart since
# restore_failed=1)
if ! grep -q "service restarted:" "$NEG10_COMBINED_LOG"; then
    record "NEG10.no-post-restore-restart" PASS "no 'service restarted:' in installer output"
else
    record "NEG10.no-post-restore-restart" FAIL "step 5 ran despite restore_failed=1"
fi

# Assertion 5: the snapshot file is INTACT (proves we did not corrupt it)
if [[ -n "$DISP_SNAPSHOT_PARENT_PRE_NEG10_DIR" ]] && [[ -f "$DISP_SNAPSHOT_PARENT_PRE_NEG10_DIR/Caddyfile.dewata.runtime" ]]; then
    POST_NEG10_SNAPSHOT_SHA=$(sha256_of_file "$DISP_SNAPSHOT_PARENT_PRE_NEG10_DIR/Caddyfile.dewata.runtime")
    if [[ "$POST_NEG10_SNAPSHOT_SHA" == "$PRE_NEG10_SNAPSHOT_SHA" ]]; then
        record "NEG10.snapshot-file-intact" PASS "snapshot sha unchanged: $POST_NEG10_SNAPSHOT_SHA"
    else
        record "NEG10.snapshot-file-intact" FAIL "sha changed: $PRE_NEG10_SNAPSHOT_SHA -> $POST_NEG10_SNAPSHOT_SHA"
    fi
else
    record "NEG10.snapshot-file-intact" FAIL "could not locate snapshot before/after"
fi

# Assertion 6: the FAKE_VALIDATE_FAILURE was logged by the disposable adapter
if grep -q "FAKE_VALIDATE_FAILURE" "$SHIM_LOG_DIR/validate.log" 2>/dev/null; then
    record "NEG10.disposable-adapter-failure-fired" PASS "adapter logged FAKE_VALIDATE_FAILURE"
else
    record "NEG10.disposable-adapter-failure-fired" FAIL "adapter did not log FAKE_VALIDATE_FAILURE"
fi

# Assertion 7: the Caddyfile on disk is back to baseline (do_restore step 1 ran)
post_run_sha=$(sha256_of_file "$DISP_PROD_CADDY")
if [[ "$post_run_sha" == "$DISP_BASELINE_SHA" ]]; then
    record "NEG10.caddyfile-restored-to-baseline" PASS "$post_run_sha"
else
    record "NEG10.caddyfile-restored-to-baseline" FAIL "got $post_run_sha want $DISP_BASELINE_SHA"
fi

# Assertion 8: the prior-release sentinel survives do_restore (REPLACEMENT
# mode restoration correctly moved the .bak back into $DISP_RELEASE_DST).
post_restore_sentinel=$(sha256_of_file "$DISP_RELEASE_DST/sentinel.html" 2>/dev/null || echo MISSING)
if [[ "$post_restore_sentinel" == "$NEG10_SENTINEL_SHA" ]]; then
    record "NEG10.prior-release-sentinel-restored" PASS "sha=$post_restore_sentinel"
else
    record "NEG10.prior-release-sentinel-restored" FAIL "got $post_restore_sentinel want $NEG10_SENTINEL_SHA"
fi

# ====================================================================
# NEGATIVE-11: rollback must not consume the snapshot's release backup.
#
# Per the user's review: "Restore releases by copying from the preserved
# snapshot into a separate staging directory, verifying the copy, then
# publishing it.  Never move the only backup out of the snapshot.
# Verify repeated rollback."
#
# Procedure:
#   1. Reset release tree + caddyfile to baseline.
#   2. Run a successful REPLACEMENT install with the prior containing a
#      sentinel file.  Capture the snapshot directory + the snapshot's
#      RELEASE_TREE_BACKUP/ + RELEASE_TREE_BACKUP.MANIFEST.txt sha256.
#   3. Run rollback TWICE against the SAME snapshot.
#   4. Assert after rollback-1:
#      - $DISP_RELEASE_DST contains the prior (sentinel)
#      - $SNAPSHOT/RELEASE_TREE_BACKUP/ + manifest sha256 unchanged
#   5. Assert after rollback-2:
#      - $DISP_RELEASE_DST still contains the prior (sentinel)
#      - $SNAPSHOT/RELEASE_TREE_BACKUP/ + manifest sha256 still unchanged
#      - (proves the snapshot was not consumed)
# ====================================================================
echo
echo "================================================================"
echo "[lifecycle] NEGATIVE-11: repeated rollback preserves snapshot"
echo "================================================================"
reset_disposable_caddyfile
rm -rf "$DISP_RELEASE_DST" "$DISP_SNAPSHOT_PARENT"/*-pre-apex
mkdir -p "$DISP_RELEASE_DST"
NEG11_SENTINEL_CONTENT="prior-release-for-rollback-test-11"
printf "%s" "$NEG11_SENTINEL_CONTENT" > "$DISP_RELEASE_DST/sentinel.html"
NEG11_PRIOR_SHA=$(sha256_of_file "$DISP_RELEASE_DST/sentinel.html")
echo "[lifecycle] NEG11 seeded sentinel sha=$NEG11_PRIOR_SHA"

# Run a successful REPLACEMENT install (no fake gate).
rc=0
run_install "DEWATA_USE_DISPOSABLE_VALIDATE=1 DEWATA_VALIDATE_CMD=$DISP_SYSTEMCTL_PATH/disposable-validate.sh DEWATA_VALIDATE_LOG=$SHIM_LOG_DIR/validate.log" || rc=$?

# Find the snapshot directory created by the install.
NEG11_SNAPSHOT_DIR=$(ls -td "$DISP_SNAPSHOT_PARENT"/*-pre-apex 2>/dev/null | head -1)
if [[ -z "$NEG11_SNAPSHOT_DIR" ]]; then
    record "NEG11.snapshot-exists" FAIL "no snapshot directory created by successful install"
else
    record "NEG11.snapshot-exists" PASS "snapshot=$NEG11_SNAPSHOT_DIR"

    # Capture sha256 of snapshot's RELEASE_TREE_BACKUP/ and MANIFEST.
    NEG11_BACKUP_BEFORE_SHA=$( (cd "$NEG11_SNAPSHOT_DIR/RELEASE_TREE_BACKUP" && find . -type f -exec sha256sum {} \; | sort -k2 | sha256sum) | cut -d' ' -f1)
    NEG11_MANIFEST_BEFORE_SHA=$(sha256_of_file "$NEG11_SNAPSHOT_DIR/RELEASE_TREE_BACKUP.MANIFEST.txt")
    echo "[lifecycle] NEG11 snapshot RELEASE_TREE_BACKUP/ sha BEFORE rollback=$NEG11_BACKUP_BEFORE_SHA"
    echo "[lifecycle] NEG11 snapshot MANIFEST sha BEFORE rollback=$NEG11_MANIFEST_BEFORE_SHA"

    # Run rollback (1st time).
    echo "[lifecycle] NEG11 running rollback (1st time)..."
    DEWATA_DISPOSABLE_MODE=1 \
    DEWATA_PROD_CADDY="$DISP_PROD_CADDY" \
    DEWATA_PROD_WWW="$SHIM_LOG_DIR/www" \
    DEWATA_RELEASE_SRC="$DISP_RELEASE_SRC" \
    DEWATA_RELEASE_DST="$DISP_RELEASE_DST" \
    DEWATA_CANDIDATE="$DISP_CANDIDATE" \
    DEWATA_REVIEWED_MANIFEST="$disp_manifest" \
    DEWATA_PROD_BASELINE_SHA="$DISP_BASELINE_SHA" \
    DEWATA_LISTENER_PORT="$DISP_LISTENER_PORT" \
    DEWATA_WORKTREE="$WT" \
    DEWATA_SNAPSHOT_PARENT="$DISP_SNAPSHOT_PARENT" \
    DEWATA_CADDY_SERVICE=dewata-caddy \
    DEWATA_SYSTEMCTL_CMD="$DISP_SYSTEMCTL" \
    DEWATA_DISPOSABLE_SYSTEMCTL_LOG="$DISP_SYSTEMCTL_LOG" \
    DEWATA_DISPOSABLE_SYSTEMCTL_PIDFILE="$DISP_SYSTEMCTL_PIDFILE" \
    DEWATA_DISPOSABLE_SYSTEMCTL_ACTIVE="$DISP_SYSTEMCTL_ACTIVE" \
    DEWATA_DISPOSABLE_SERVICE_MODE=restart \
    DEWATA_PROBE_LISTENER=0 \
    DEWATA_USE_DISPOSABLE_VALIDATE=1 \
    DEWATA_VALIDATE_CMD=$DISP_SYSTEMCTL_PATH/disposable-validate.sh \
    DEWATA_VALIDATE_LOG=$SHIM_LOG_DIR/validate.log \
        bash "$ROLLBACK" "$NEG11_SNAPSHOT_DIR" > "/tmp/dewata-lifecycle.rollback1.out" 2>&1
    neg11_rb1_rc=$?
    echo "[lifecycle] NEG11 rollback-1 rc=$neg11_rb1_rc"

    # Capture sha256 AFTER rollback-1.
    NEG11_BACKUP_AFTER_RB1_SHA=$( (cd "$NEG11_SNAPSHOT_DIR/RELEASE_TREE_BACKUP" && find . -type f -exec sha256sum {} \; | sort -k2 | sha256sum) | cut -d' ' -f1)
    NEG11_MANIFEST_AFTER_RB1_SHA=$(sha256_of_file "$NEG11_SNAPSHOT_DIR/RELEASE_TREE_BACKUP.MANIFEST.txt")
    echo "[lifecycle] NEG11 snapshot RELEASE_TREE_BACKUP/ sha AFTER rb1=$NEG11_BACKUP_AFTER_RB1_SHA"
    echo "[lifecycle] NEG11 snapshot MANIFEST sha AFTER rb1=$NEG11_MANIFEST_AFTER_RB1_SHA"

    if [[ "$NEG11_BACKUP_AFTER_RB1_SHA" == "$NEG11_BACKUP_BEFORE_SHA" ]]; then
        record "NEG11.snapshot-backup-unchanged-after-rb1" PASS "sha unchanged"
    else
        record "NEG11.snapshot-backup-unchanged-after-rb1" FAIL "before=$NEG11_BACKUP_BEFORE_SHA after-rb1=$NEG11_BACKUP_AFTER_RB1_SHA"
    fi
    if [[ "$NEG11_MANIFEST_AFTER_RB1_SHA" == "$NEG11_MANIFEST_BEFORE_SHA" ]]; then
        record "NEG11.snapshot-manifest-unchanged-after-rb1" PASS "sha unchanged"
    else
        record "NEG11.snapshot-manifest-unchanged-after-rb1" FAIL "before=$NEG11_MANIFEST_BEFORE_SHA after-rb1=$NEG11_MANIFEST_AFTER_RB1_SHA"
    fi

    # Run rollback (2nd time).
    echo "[lifecycle] NEG11 running rollback (2nd time)..."
    DEWATA_DISPOSABLE_MODE=1 \
    DEWATA_PROD_CADDY="$DISP_PROD_CADDY" \
    DEWATA_PROD_WWW="$SHIM_LOG_DIR/www" \
    DEWATA_RELEASE_SRC="$DISP_RELEASE_SRC" \
    DEWATA_RELEASE_DST="$DISP_RELEASE_DST" \
    DEWATA_CANDIDATE="$DISP_CANDIDATE" \
    DEWATA_REVIEWED_MANIFEST="$disp_manifest" \
    DEWATA_PROD_BASELINE_SHA="$DISP_BASELINE_SHA" \
    DEWATA_LISTENER_PORT="$DISP_LISTENER_PORT" \
    DEWATA_WORKTREE="$WT" \
    DEWATA_SNAPSHOT_PARENT="$DISP_SNAPSHOT_PARENT" \
    DEWATA_CADDY_SERVICE=dewata-caddy \
    DEWATA_SYSTEMCTL_CMD="$DISP_SYSTEMCTL" \
    DEWATA_DISPOSABLE_SYSTEMCTL_LOG="$DISP_SYSTEMCTL_LOG" \
    DEWATA_DISPOSABLE_SYSTEMCTL_PIDFILE="$DISP_SYSTEMCTL_PIDFILE" \
    DEWATA_DISPOSABLE_SYSTEMCTL_ACTIVE="$DISP_SYSTEMCTL_ACTIVE" \
    DEWATA_DISPOSABLE_SERVICE_MODE=restart \
    DEWATA_PROBE_LISTENER=0 \
    DEWATA_USE_DISPOSABLE_VALIDATE=1 \
    DEWATA_VALIDATE_CMD=$DISP_SYSTEMCTL_PATH/disposable-validate.sh \
    DEWATA_VALIDATE_LOG=$SHIM_LOG_DIR/validate.log \
        bash "$ROLLBACK" "$NEG11_SNAPSHOT_DIR" > "/tmp/dewata-lifecycle.rollback2.out" 2>&1
    neg11_rb2_rc=$?
    echo "[lifecycle] NEG11 rollback-2 rc=$neg11_rb2_rc"

    # Capture sha256 AFTER rollback-2.
    NEG11_BACKUP_AFTER_RB2_SHA=$( (cd "$NEG11_SNAPSHOT_DIR/RELEASE_TREE_BACKUP" && find . -type f -exec sha256sum {} \; | sort -k2 | sha256sum) | cut -d' ' -f1)
    NEG11_MANIFEST_AFTER_RB2_SHA=$(sha256_of_file "$NEG11_SNAPSHOT_DIR/RELEASE_TREE_BACKUP.MANIFEST.txt")
    echo "[lifecycle] NEG11 snapshot RELEASE_TREE_BACKUP/ sha AFTER rb2=$NEG11_BACKUP_AFTER_RB2_SHA"
    echo "[lifecycle] NEG11 snapshot MANIFEST sha AFTER rb2=$NEG11_MANIFEST_AFTER_RB2_SHA"

    if [[ "$NEG11_BACKUP_AFTER_RB2_SHA" == "$NEG11_BACKUP_BEFORE_SHA" ]]; then
        record "NEG11.snapshot-backup-unchanged-after-rb2" PASS "sha unchanged across 2 rollbacks"
    else
        record "NEG11.snapshot-backup-unchanged-after-rb2" FAIL "before=$NEG11_BACKUP_BEFORE_SHA after-rb2=$NEG11_BACKUP_AFTER_RB2_SHA"
    fi
    if [[ "$NEG11_MANIFEST_AFTER_RB2_SHA" == "$NEG11_MANIFEST_BEFORE_SHA" ]]; then
        record "NEG11.snapshot-manifest-unchanged-after-rb2" PASS "sha unchanged across 2 rollbacks"
    else
        record "NEG11.snapshot-manifest-unchanged-after-rb2" FAIL "before=$NEG11_MANIFEST_BEFORE_SHA after-rb2=$NEG11_MANIFEST_AFTER_RB2_SHA"
    fi

    # Also assert rollback-2 rc is 0 (it succeeded).
    if [[ "$neg11_rb2_rc" == "0" ]]; then
        record "NEG11.repeated-rollback-succeeds" PASS "rollback-2 rc=0"
    else
        record "NEG11.repeated-rollback-succeeds" FAIL "rollback-2 rc=$neg11_rb2_rc"
    fi

    # And the prior-release sentinel is present in RELEASE_DST after rb2.
    rb2_sentinel_sha=$(sha256_of_file "$DISP_RELEASE_DST/sentinel.html" 2>/dev/null || echo MISSING)
    if [[ "$rb2_sentinel_sha" == "$NEG11_PRIOR_SHA" ]]; then
        record "NEG11.prior-release-restored-by-rb2" PASS "sha=$rb2_sentinel_sha"
    else
        record "NEG11.prior-release-restored-by-rb2" FAIL "got $rb2_sentinel_sha want $NEG11_PRIOR_SHA"
    fi
fi

# ====================================================================
# Final production check
# ====================================================================
record_prod_state
if [[ "$PROD_CADDY_SHA" == "$PROD_BEFORE_SHA" && "$PROD_PID" == "$PROD_BEFORE_PID" ]]; then
    record "FINAL.prod-untouched-across-suite" PASS "prod_sha=$PROD_CADDY_SHA prod_pid=$PROD_PID"
else
    record "FINAL.prod-untouched-across-suite" FAIL "prod_sha $PROD_BEFORE_SHA -> $PROD_CADDY_SHA or pid $PROD_BEFORE_PID -> $PROD_PID"
fi

# ====================================================================
# Results
# ====================================================================
echo
echo "================================================================"
echo "[lifecycle] suite done at $(date -u +%Y%m%dT%H%M%SZ)"
echo "[lifecycle] total=$TOTAL pass=$PASSED fail=$FAILED"
echo "================================================================"

# Dump install logs for the failure cases
if (( SUITE_FAILED )); then
    echo
    echo "----------------------------------------------------------------"
    echo "DISPOSABLE INSTALL/ROLLBACK LOG TAILS"
    echo "----------------------------------------------------------------"
    for f in /tmp/dewata-lifecycle.install.out /tmp/dewata-lifecycle.install.err /tmp/dewata-lifecycle.rollback.out /tmp/dewata-lifecycle.rollback.err; do
        if [[ -f "$f" ]]; then
            echo "  --- $f ---"
            tail -50 "$f" | sed "s|^|    |"
        fi
    done
fi

if (( SUITE_FAILED )); then
    exit 2
fi
exit 0
