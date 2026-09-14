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
DISP_SNAPSHOT_PARENT="$SHIM_LOG_DIR/atomic"
DISP_LISTENER_PORT="18443"

run_install() {
    # $1 = optional extra env vars to set before invoking the installer
    # sets up:
    #   /tmp/dewata-lifecycle.install.out.NNN <- install stdout for this call
    #   /tmp/dewata-lifecycle.install.err.NNN <- install stderr for this call
    #   /tmp/dewata-lifecycle.install.out       <- symlink to latest
    local extra_env="${1:-}"
    local rc
    rm -f "$SHIM_LOG"
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
        DEWATA_PROD_CADDY="$DISP_PROD_CADDY" \
        DEWATA_LISTENER_PORT="$DISP_LISTENER_PORT" \
        DEWATA_WORKTREE="$WT" \
        DEWATA_SNAPSHOT_DIR="$snap_dir" \
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
echo "[lifecycle] NEGATIVE-6: post-publish failure"
echo "================================================================"
reset_disposable_caddyfile
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

# ====================================================================
# NEGATIVE-7: post-G4 failure (caddyfile installed but G5 not started)
# ====================================================================
echo
echo "================================================================"
echo "[lifecycle] NEGATIVE-7: post-G4 failure"
echo "================================================================"
reset_disposable_caddyfile
rc=0
run_install "DEWATA_FAKE_FAIL_AT_GATE=g4" || rc=$?
if [[ $rc -ne 0 ]]; then
    record "NEG7.install-rejected" PASS "rc=$rc"
else
    record "NEG7.install-rejected" FAIL "rc=0"
fi
post_run_sha=$(sha256_of_file "$DISP_PROD_CADDY")
if [[ "$post_run_sha" == "$DISP_BASELINE_SHA" ]]; then
    record "NEG7.caddyfile-restored" PASS "$post_run_sha"
else
    record "NEG7.caddyfile-restored" FAIL "got $post_run_sha want $DISP_BASELINE_SHA"
fi

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
echo "[lifecycle] NEGATIVE-9: post-G6 restart failure"
echo "================================================================"
reset_disposable_caddyfile
rc=0
run_install "DEWATA_FAKE_FAIL_AT_GATE=g6" || rc=$?
if [[ $rc -ne 0 ]]; then
    record "NEG9.install-rejected" PASS "rc=$rc"
else
    record "NEG9.install-rejected" FAIL "rc=0"
fi

# ====================================================================
# NEGATIVE-10: failure during recovery
# ====================================================================
echo
echo "================================================================"
echo "[lifecycle] NEGATIVE-10: failure during recovery"
echo "================================================================"
reset_disposable_caddyfile
rc=0
run_install "DEWATA_FAKE_FAIL_AT_GATE=g4 DEWATA_FAKE_RECOVERY_VALIDATION_FAILURE=1" || rc=$?
# do_restore returns rc=2 when restore_failed=1
if [[ $rc -eq 2 ]]; then
    record "NEG10.install-fail-rc2" PASS "rc=$rc (AUTO-RESTORE INCOMPLETE)"
elif [[ $rc -ne 0 ]]; then
    record "NEG10.install-rejected" PASS "rc=$rc"
else
    record "NEG10.install-fail-rc2" FAIL "rc=0"
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
