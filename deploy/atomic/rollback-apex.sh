#!/usr/bin/env bash
# =============================================================================
# dewata-caddy apex rollback -- control: RESTART, not reload
# =============================================================================
#
# Restores the previous Caddyfile.dewata from the snapshot directory
# and RESTARTS the caddy service.  Returns the dewata.org apex to its
# previous broken state (catch-all 503), pending operator dashboard work.
#
# Path and service parameters are env-overridable for the lifecycle test:
#   DEWATA_PROD_CADDY    -> production Caddyfile path (default: prod)
#   DEWATA_TEST_MODE=1   -> skip the real systemctl call; the lifecycle
#                          driver will kill and relaunch the disposable
#                          after this script returns successfully
#
# DNS rollback order (operator-driven, see end of script):
#   1. Cloudflare -> dewata-vps -> Public Hostnames -> remove dewata.org
#   2. (Optional, see warning below) restore the two known-broken A records
#
# =============================================================================

set -euo pipefail

WORKTREE=/opt/dw-phase2
SNAPSHOT_DIR="${1:-}"

if [[ -z "$SNAPSHOT_DIR" ]]; then
    echo "usage: $0 <SNAPSHOT_DIR>"
    echo "  snapshots are at: $WORKTREE/deploy/atomic/<utc-timestamp>-pre-apex/"
    echo "  the latest snapshot is the most recent one"
    ls -1 "$WORKTREE/deploy/atomic" 2>/dev/null | tail -1 || true
    exit 1
fi

# --------------------------------------------------------------------
# path config -- production by default; override via env to test.
# --------------------------------------------------------------------
# Production-path guard: refuse to run against /opt/dewata.online
# unless DEWATA_TEST_MODE=1 is explicit.
if [[ "${DEWATA_TEST_MODE:-}" != "1" ]]; then
    case "${DEWATA_PROD_CADDY:-}" in
        /opt/dewata.online/*|/etc/caddy/*|/var/lib/dewata/*)
            echo "FATAL: refusing to run rollback against production path $DEWATA_PROD_CADDY without DEWATA_TEST_MODE=1." >&2
            exit 4
            ;;
    esac
fi

# Mandatory: the rollback target path must be supplied via env.
# No mutable default: refuse to run if unset.
if [[ -z "${DEWATA_PROD_CADDY:-}" ]]; then
    echo "FATAL: DEWATA_PROD_CADDY is unset or empty." >&2
    echo "  supply the production Caddyfile path, e.g.:" >&2
    echo "    DEWATA_PROD_CADDY=/opt/dewata.online/deploy/caddy/Caddyfile.dewata" >&2
    exit 2
fi
PROD=$DEWATA_PROD_CADDY
SERVICE=${DEWATA_CADDY_SERVICE:-dewata-caddy}
LISTENER_PORT=${DEWATA_LISTENER_PORT:-8443}
RELEASE_DST=${DEWATA_RELEASE_DST:-/opt/dewata.online/deploy/www/dewata-org/v0.1.0-pre1}

# --------------------------------------------------------------------
# G0: validate the snapshot directory + its runtime file
# --------------------------------------------------------------------
RUNTIME_BACKUP="$SNAPSHOT_DIR/Caddyfile.dewata.runtime"
[[ -d "$SNAPSHOT_DIR" ]] || { echo "ERROR: $SNAPSHOT_DIR is not an existing directory"; exit 1; }
[[ -f "$RUNTIME_BACKUP" ]] || { echo "ERROR: $RUNTIME_BACKUP missing (not a pre-apex snapshot?)"; exit 1; }

# --------------------------------------------------------------------
# G1: validate the saved runtime caddyfile before installing
# --------------------------------------------------------------------
echo "G1: validating $RUNTIME_BACKUP"
/usr/bin/caddy validate --config "$RUNTIME_BACKUP" --adapter caddyfile || {
    echo "ERROR: saved runtime file does not validate; refusing to install"
    exit 1
}

# --------------------------------------------------------------------
# G2: atomic install the saved runtime caddyfile
# --------------------------------------------------------------------
echo "G2: atomic install of saved runtime caddyfile to $PROD"
# Capture pre-rollback production caddyfile sha BEFORE we touch it.
PRE_ROLLBACK_PROD_SHA=$(sha256sum "$PROD" | cut -d' ' -f1)
echo "G2: pre-rollback $PROD sha256 = $PRE_ROLLBACK_PROD_SHA"
# Failure-injection hook: corrupt the saved runtime file AFTER
# capturing its sha.  This simulates a disk write corruption that
# breaks the snapshot file post-snapshot.  The rollback's G3
# re-validate then fails, and the rollback refuses to declare success.
if [[ "${DEWATA_FAKE_FAIL_AT_GATE:-}" == "rollback-validate" ]]; then
    echo "FATAL: DEWATA_FAKE_FAIL_AT_GATE=rollback-validate -> corrupting snapshot runtime in place" >&2
    printf "\n{ broken syntax\n" >> "$RUNTIME_BACKUP"
fi
install -m 0644 "$RUNTIME_BACKUP" "$PROD.new"
sync
mv -f "$PROD.new" "$PROD"
POST_ROLLBACK_PROD_SHA=$(sha256sum "$PROD" | cut -d' ' -f1)
echo "G2: post-rollback $PROD sha256 = $POST_ROLLBACK_PROD_SHA"
echo "G2: saved runtime file installed at $PROD"

# --------------------------------------------------------------------
# G3: re-validate the now-installed file
# --------------------------------------------------------------------
echo "G3: re-validating installed file"
/usr/bin/caddy validate --config "$PROD" --adapter caddyfile

# No-op check: if the just-installed snapshot caddyfile is byte-
# identical to the caddyfile we started with, no configuration change
# occurred and we MUST NOT restart the service.
if [[ "$PRE_ROLLBACK_PROD_SHA" == "$POST_ROLLBACK_PROD_SHA" ]]; then
    echo "G4: rollback was a no-op (snapshot == current prod caddyfile, sha $PRE_ROLLBACK_PROD_SHA)"
    echo "G4: skipping systemctl restart -- no live change to apply"
    ROLLBACK_RESTART_INVOKED=0
else
    echo "G4: snapshot caddyfile differs from production (was $PRE_ROLLBACK_PROD_SHA, now $POST_ROLLBACK_PROD_SHA); restart required"
fi

# --------------------------------------------------------------------
# G4: restart (mirrors install's restart semantics)
# --------------------------------------------------------------------
echo "G4: restart $SERVICE"

if [[ "$PRE_ROLLBACK_PROD_SHA" == "$POST_ROLLBACK_PROD_SHA" ]]; then
    OLD_PID=$(systemctl show "$SERVICE" -p MainPID --value 2>/dev/null || echo 0)
    NEW_PID="$OLD_PID"
    ROLLBACK_RESTART_INVOKED=0
    echo "G4: $SERVICE MainPID unchanged: $OLD_PID (no-op rollback, no restart)"
elif [[ "${DEWATA_TEST_MODE:-0}" == "1" ]]; then
    OLD_PID=$(systemctl show "$SERVICE" -p MainPID --value 2>/dev/null || echo 0)
    NEW_PID=0
    ROLLBACK_RESTART_INVOKED=0
    echo "G4: DEWATA_TEST_MODE=1 -> skipping systemctl restart (driver will take over)"
    echo "G4: pre-restart $SERVICE MainPID=$OLD_PID"
    echo "G4: post-restart $SERVICE MainPID=$NEW_PID (driver will take over)"
else
    OLD_PID=$(systemctl show "$SERVICE" -p MainPID --value)
    ROLLBACK_RESTART_INVOKED=1
    echo "G4: pre-restart $SERVICE MainPID=$OLD_PID"
    if [[ "${DEWATA_FAKE_RESTART_FAILURE:-0}" == "1" ]]; then
        echo "G4: DEWATA_FAKE_RESTART_FAILURE=1 -> simulating post-restart failure"
        systemctl restart "$SERVICE" || true
        NEW_PID=$(systemctl show "$SERVICE" -p MainPID --value)
    else
        systemctl restart "$SERVICE"
        for attempt in 1 2 3 4 5 6 7 8 9 10 11 12; do
            state=$(systemctl is-active "$SERVICE" || true)
            if [[ "$state" == "active" ]]; then break; fi
            sleep 1
        done
        NEW_PID=$(systemctl show "$SERVICE" -p MainPID --value)
    fi
    echo "G4: post-restart $SERVICE MainPID=$NEW_PID"
fi

# verify the listener is back up.  In test mode the driver controls
# the listener; this check would race.  so only enforce in production.
if [[ "${DEWATA_TEST_MODE:-0}" != "1" ]]; then
    ss -ltn | grep -q ":$LISTENER_PORT " && echo "G4: :$LISTENER_PORT listening" || {
        echo "ERROR: :$LISTENER_PORT not listening after restart"; exit 1
    }
fi

# --------------------------------------------------------------------
# G5: HTTP probes (only in production mode; the lifecycle driver does
# probing in test mode)
# --------------------------------------------------------------------
if [[ "${DEWATA_TEST_MODE:-0}" == "1" ]]; then
    echo
    echo "================================================================"
    echo "G5: HTTP probes (DEWATA_TEST_MODE=1 -> skipped; lifecycle driver handles)"
    echo "================================================================"
    echo
    echo "================================================================"
    echo "ROLLBACK SUCCESS (test mode: file operations only)"
    echo "================================================================"
    echo "  snapshot:    $SNAPSHOT_DIR"
    echo "  Caddyfile:   $PROD restored from $SNAPSHOT_DIR/Caddyfile.dewata.runtime"
    echo "  release dir: $RELEASE_DST retained (no deletion)"
    echo
    echo "PAUSE -- the lifecycle driver will now launch the disposable"
    echo "caddy with the restored snapshot caddyfile and run probes."
    exit 0
fi
echo "G5: HTTP probes against $SERVICE on 127.0.0.1:$LISTENER_PORT"
fail=0

probe() {
    local host="$1" path="$2" expected_code="$3"
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" \
        --max-time 5 \
        -H "Host: $host" \
        "http://127.0.0.1:$LISTENER_PORT$path")
    if [[ "$code" == "$expected_code" ]]; then
        printf "  OK  %-22s %-30s -> %s\n" "$host" "$path" "$code"
    else
        printf "  FAIL %-22s %-30s -> got %s expected %s\n" "$host" "$path" "$code" "$expected_code"
        fail=1
    fi
}

# After rollback, dewata.org apex should be 503 again (catch-all).
probe dewata.org          "/"                                       503 || fail=1
probe api.dewata.org      "/health"                                 200 || fail=1
probe api.dewata.org      "/dsp/v0.1/calendar/ruleset"              200 || fail=1
probe bci.dewata.org      "/"                                       503 || fail=1
probe protocol.dewata.org "/"                                       503 || fail=1
probe datasets.dewata.org "/"                                       503 || fail=1
probe localhost           "/"                                       503 || fail=1

if (( fail )); then
    echo
    echo "ROLLBACK: some probes failed.  inspect manually before further action."
    exit 1
fi

echo
echo "ROLLBACK SUCCESS"
echo "  Caddyfile:    restored from $SNAPSHOT_DIR"
echo "  release dir:  retained at (no deletion)"
echo "  caddy:        restarted, MainPID $OLD_PID -> $NEW_PID"
echo
echo "PAUSE -- operator-driven dashboard work, in this exact order:"
echo
echo "  Step 1 (DNS cutover for rollback, mirror of the install DNS cutover):"
echo
echo "    1a. Zero Trust -> dewata-vps -> Public Hostnames -> REMOVE the"
echo "        dewata.org entry."
echo "    1b. confirm any corresponding apex CNAME or tunnel DNS record"
echo "        is removed before doing anything that re-adds A records."
echo
echo "  Step 2 (only if you want to return the apex to the documented-"
echo "          broken baseline state):"
echo
echo "    2a. recreate the two known-broken A records, both proxy ON:"
echo "          dewata.org A 54.149.79.189"
echo "          dewata.org A 34.216.117.25"
echo "        Restoring them RE-CREATES the 522 problem; they are"
echo "        labelled as the previous broken state, not a known-good state."
echo
echo "    If Step 2 is done without Step 1, the apex A records will"
echo "    briefly take precedence over the now-removed tunnel route."
echo "    Do Step 1 first."
echo
echo "  DNS cutover order summary (mirrors the install-side cutover):"
echo "    Install:   (a) record the two old A records (54.149.79.189 / 34.216.117.25)"
echo "               (b) remove those A records"
echo "               (c) add dewata.org published-application tunnel route -> 127.0.0.1:8443"
echo "    Rollback:  (a) remove the dewata.org published-application tunnel route"
echo "               (b) optionally restore the two old A records (re-creates 522)"
