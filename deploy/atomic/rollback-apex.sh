#!/usr/bin/env bash
# =============================================================================
# dewata-caddy apex rollback -- reviewed for fifth-bundle corrections
# =============================================================================
#
# Restores the production Caddyfile + release tree from a pre-apex
# snapshot directory produced by install-apex-candidate.sh.
#
# Modes (same as the installer):
#   DEWATA_DISPOSABLE_MODE=1   -- operate against a disposable tree,
#     skip the production restart
#   DEWATA_APPLY_PRODUCTION=1   -- authorize writes to a known
#     production path AND restart the real production service
# Mutually exclusive.
#
# Snapshot path: the install script saved the snapshot at
# $SNAPSHOT_DIR (passed as $1) with files:
#   - Caddyfile.dewata.runtime  (the saved production Caddyfile)
#   - Caddyfile.dewata.candidate (the failed candidate)
#   - Caddyfile.dewata.diff     (the diff between them)
#   - installed.log             (record of when the install ran)
#   - stage-counters*           (may be present from the failed install)
#   - <snapshot_dir>.postrestore.<ts> (only present after a previous rollback)
# The rollback restores $DEWATA_PROD_CADDY from Caddyfile.dewata.runtime.
# =============================================================================

set -Eeuo pipefail
shopt -s inherit_errexit 2>/dev/null || true

# --------------------------------------------------------------------
# Mode selection (mutually exclusive)
# --------------------------------------------------------------------
DISPOSABLE=${DEWATA_DISPOSABLE_MODE:-}
APPLY_PROD=${DEWATA_APPLY_PRODUCTION:-}
if [[ -n "$DISPOSABLE" && -n "$APPLY_PROD" ]]; then
    echo "FATAL: DEWATA_DISPOSABLE_MODE and DEWATA_APPLY_PRODUCTION are mutually exclusive." >&2
    exit 5
fi
if [[ -z "$DISPOSABLE" && -z "$APPLY_PROD" ]]; then
    echo "FATAL: neither DEWATA_DISPOSABLE_MODE nor DEWATA_APPLY_PRODUCTION is set." >&2
    exit 5
fi
if [[ "$DISPOSABLE" != "1" && "$APPLY_PROD" != "1" ]]; then
    echo "FATAL: mode flag must be exactly \"1\"." >&2
    exit 5
fi

# --------------------------------------------------------------------
# Required env vars (no mutable defaults)
# --------------------------------------------------------------------
require_var() {
    local name="$1"
    local hint="$2"
    if [[ -z "${!name:-}" ]]; then
        echo "FATAL: $name is unset or empty." >&2
        [[ -n "$hint" ]] && echo "  $hint" >&2
        exit 2
    fi
}
require_var DEWATA_PROD_CADDY "supply the production Caddyfile path"
require_var DEWATA_LISTENER_PORT "supply the listener port"
require_var DEWATA_WORKTREE "supply the worktree root"

PROD=$DEWATA_PROD_CADDY
LISTENER_PORT=$DEWATA_LISTENER_PORT
WORKTREE=$DEWATA_WORKTREE
: "${DEWATA_CADDY_SERVICE:=dewata-caddy}"
# Configurable systemctl command (install uses the same hook).  The
# lifecycle test sets this to the disposable shim path.
SYSTEMCTL_CMD="${DEWATA_SYSTEMCTL_CMD:-systemctl}"

# --------------------------------------------------------------------
# Snapshot dir (positional arg)
# --------------------------------------------------------------------
SNAPSHOT_DIR="${1:-${DEWATA_SNAPSHOT_DIR:-}}"
if [[ -z "$SNAPSHOT_DIR" ]]; then
    echo "FATAL: snapshot dir is required (pass as positional arg or DEWATA_SNAPSHOT_DIR)" >&2
    echo "  example: $0 /opt/dewata.online/deploy/atomic/20260914T143000Z-pre-apex" >&2
    exit 1
fi
RUNTIME_BACKUP="$SNAPSHOT_DIR/Caddyfile.dewata.runtime"
if [[ ! -d "$SNAPSHOT_DIR" ]]; then
    echo "FATAL: $SNAPSHOT_DIR is not an existing directory" >&2
    exit 1
fi
if [[ ! -f "$RUNTIME_BACKUP" ]]; then
    echo "FATAL: $RUNTIME_BACKUP missing (not a pre-apex snapshot?)" >&2
    exit 1
fi

# --------------------------------------------------------------------
# Production-path guard
# --------------------------------------------------------------------
IS_PROD_PATH=0
case "$PROD" in
    /opt/dewata.online/*|/etc/caddy/*|/var/lib/dewata/*) IS_PROD_PATH=1 ;;
esac
if [[ "$IS_PROD_PATH" -eq 1 && "$APPLY_PROD" != "1" ]]; then
    echo "FATAL: refusing to rollback against production path $PROD without DEWATA_APPLY_PRODUCTION=1." >&2
    exit 4
fi
if [[ "$IS_PROD_PATH" -eq 0 && "$APPLY_PROD" == "1" ]]; then
    echo "FATAL: DEWATA_APPLY_PRODUCTION=1 set but DEWATA_PROD_CADDY ($PROD) is not a known production path." >&2
    exit 4
fi

# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------
sha256_of_file() { sha256sum "$1" | cut -d' ' -f1; }

# --------------------------------------------------------------------
# G1: validate the saved runtime caddyfile
# --------------------------------------------------------------------
echo "G1: validating $RUNTIME_BACKUP"
/usr/bin/caddy validate --config "$RUNTIME_BACKUP" --adapter caddyfile || {
    echo "FATAL: saved runtime file does not validate; refusing to install" >&2
    exit 1
}

# --------------------------------------------------------------------
# G2: atomic install the saved runtime caddyfile
# --------------------------------------------------------------------
echo "G2: atomic install of saved runtime caddyfile to $PROD"
PRE_ROLLBACK_PROD_SHA=$(sha256_of_file "$PROD")
echo "G2: pre-rollback $PROD sha256 = $PRE_ROLLBACK_PROD_SHA"

# Failure-injection hook: corrupt the saved runtime file so the
# G3 re-validate fails.
if [[ "${DEWATA_FAKE_FAIL_AT_GATE:-}" == "rollback-validate" ]]; then
    echo "FATAL: DEWATA_FAKE_FAIL_AT_GATE=rollback-validate -> corrupting snapshot runtime in place" >&2
    printf "\\n{ broken syntax\\n" >> "$RUNTIME_BACKUP"
fi

install -m 0644 "$RUNTIME_BACKUP" "$PROD.new"
sync
mv -f "$PROD.new" "$PROD"
POST_ROLLBACK_PROD_SHA=$(sha256_of_file "$PROD")
echo "G2: post-rollback $PROD sha256 = $POST_ROLLBACK_PROD_SHA"
echo "G2: saved runtime file installed at $PROD"

# Failure-injection hook: simulate a post-G2 failure (e.g. caddy
# validate fails because the file is somehow broken).
if [[ "${DEWATA_FAKE_FAIL_AT_GATE:-}" == "rollback-post-g2" ]]; then
    echo "FATAL: DEWATA_FAKE_FAIL_AT_GATE=rollback-post-g2 -> simulating failure after G2" >&2
    # Try to restore the prior state (which was just before G2 ran).
    # This is best-effort; the script will exit 1.
    install -m 0644 /opt/dw-phase2/deploy/caddy/Caddyfile.dewata.runtime "$PROD.new"
    sync
    mv -f "$PROD.new" "$PROD"
    exit 1
fi

# --------------------------------------------------------------------
# G3: re-validate the now-installed file
# --------------------------------------------------------------------
echo "G3: re-validating installed file"
/usr/bin/caddy validate --config "$PROD" --adapter caddyfile

# --------------------------------------------------------------------
# G4: restart
#   No-op check: if the post-rollback Caddyfile is byte-identical to
#   the pre-rollback Caddyfile, no live change occurred.
# --------------------------------------------------------------------
echo "G4: restart $DEWATA_CADDY_SERVICE"

if [[ "$POST_ROLLBACK_PROD_SHA" == "$PRE_ROLLBACK_PROD_SHA" ]]; then
    echo "G4: rollback was a no-op (snapshot == current prod caddyfile, sha $PRE_ROLLBACK_PROD_SHA)"
    echo "G4: skipping ${SYSTEMCTL_CMD:-systemctl} restart -- no live change to apply"
    OLD_PID=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value 2>/dev/null || echo 0)
    NEW_PID="$OLD_PID"
elif [[ "$DISPOSABLE" == "1" ]]; then
    OLD_PID=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value 2>/dev/null || echo 0)
    NEW_PID=0
    echo "G4: DEWATA_DISPOSABLE_MODE=1 -> skipping ${SYSTEMCTL_CMD:-systemctl} restart (driver will take over)"
    echo "G4: pre-restart $DEWATA_CADDY_SERVICE MainPID=$OLD_PID"
    echo "G4: post-restart $DEWATA_CADDY_SERVICE MainPID=$NEW_PID (driver will take over)"
elif [[ "$APPLY_PROD" == "1" && "$IS_PROD_PATH" -eq 1 ]]; then
    OLD_PID=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value)
    echo "G4: pre-restart $DEWATA_CADDY_SERVICE MainPID=$OLD_PID"
    if [[ "${DEWATA_FAKE_RESTART_FAILURE:-0}" == "1" ]]; then
        echo "G4: DEWATA_FAKE_RESTART_FAILURE=1 -> simulating post-restart failure"
        ${SYSTEMCTL_CMD:-systemctl} restart "$DEWATA_CADDY_SERVICE" || true
        NEW_PID=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value)
    else
        ${SYSTEMCTL_CMD:-systemctl} restart "$DEWATA_CADDY_SERVICE"
        for attempt in 1 2 3 4 5 6 7 8 9 10 11 12; do
            state=$(${SYSTEMCTL_CMD:-systemctl} is-active "$DEWATA_CADDY_SERVICE" || true)
            if [[ "$state" == "active" ]]; then break; fi
            sleep 1
        done
        NEW_PID=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value)
    fi
    echo "G4: post-restart $DEWATA_CADDY_SERVICE MainPID=$NEW_PID"
fi

# Post-restart listener check (production only).
if [[ "$APPLY_PROD" == "1" && "$IS_PROD_PATH" -eq 1 ]]; then
    ss -ltn | grep -q ":$LISTENER_PORT " && echo "G4: :$LISTENER_PORT listening" || {
        echo "FATAL: :$LISTENER_PORT not listening after restart"; exit 1
    }
fi

# Failure-injection hook: simulate a post-G4 failure (e.g. restart
# succeeded but a post-restart check failed).  The rollback script
# itself exits non-zero; we don't have a do_restore here because the
# rollback is already the recovery action.
if [[ "${DEWATA_FAKE_FAIL_AT_GATE:-}" == "g4" ]]; then
    echo "FATAL: DEWATA_FAKE_FAIL_AT_GATE=g4 -> simulating failure after G4" >&2
    exit 1
fi

# --------------------------------------------------------------------
# G5: HTTP probes (production only)
# --------------------------------------------------------------------
if [[ "$APPLY_PROD" == "1" && "$IS_PROD_PATH" -eq 1 ]]; then
    echo
    echo "================================================================"
    echo "G5: HTTP probes"
    echo "================================================================"
    echo "G5: HTTP probes against $DEWATA_CADDY_SERVICE on 127.0.0.1:$LISTENER_PORT"
    fail=0
    probe() {
        local host="$1" path="$2" expected_code="$3"
        local code body
        code=$(curl -s -o /tmp/probe.body -w "%{http_code}" \
            --max-time 5 \
            -H "Host: $host" \
            "http://127.0.0.1:$LISTENER_PORT$path")
        body=$(head -c 200 /tmp/probe.body)
        if [[ "$code" == "$expected_code" ]]; then
            printf "  OK  %-22s %-30s -> %s  body[:200]=%s\\n" "$host" "$path" "$code" "$body"
        else
            printf "  FAIL %-22s %-30s -> got %s expected %s\\n" "$host" "$path" "$code" "$expected_code"
            return 1
        fi
    }
    probe dewata.org          "/"               503 || fail=1
    probe api.dewata.org      "/health"         200 || fail=1
    if (( fail )); then
        echo
        echo "ROLLBACK: some probes failed.  inspect manually."
        exit 1
    fi
fi

echo
echo "================================================================"
echo "ROLLBACK SUCCESS"
echo "================================================================"
echo "  mode:        $([[ "$APPLY_PROD" == "1" ]] && echo PRODUCTION || echo DISPOSABLE)"
echo "  snapshot:    $SNAPSHOT_DIR"
echo "  caddyfile:   $PROD restored from $RUNTIME_BACKUP"
echo "  restart:     $([[ -n "$NEW_PID" && "$NEW_PID" != "$OLD_PID" ]] && echo "yes, MainPID $OLD_PID -> $NEW_PID" || echo "skipped (no live change or DISPOSABLE mode)")"

# Log the rollback to the snapshot's installed.log so the trail
# of every install + rollback is in one place.
mkdir -p "$SNAPSHOT_DIR"
echo "$(date -u +%Y%m%dT%H%M%SZ)  rollback  $OLD_PID -> $NEW_PID  prod=$APPLY_PROD  disposable=$DISPOSABLE" >> "$SNAPSHOT_DIR/installed.log"
echo "  actual_snapshot_path=$SNAPSHOT_DIR"
exit 0
