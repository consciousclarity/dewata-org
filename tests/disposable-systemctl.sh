#!/usr/bin/env bash
# =============================================================================
# disposable-systemctl.sh -- the systemctl shim used by the lifecycle test
# =============================================================================
#
# Used by the lifecycle test (deploy/lifecycle-test/run-lifecycle-test.sh)
# when DEWATA_DISPOSABLE_MODE=1 + DEWATA_DISPOSABLE_SERVICE_MODE=restart.
# Production runs do NOT use this shim.
#
# Configuration (env vars the test sets):
#   DEWATA_DISPOSABLE_SYSTEMCTL_LOG     -- log file path (default
#                                           /tmp/dewata-lifecycle-systemctl.log)
#   DEWATA_DISPOSABLE_SYSTEMCTL_PIDFILE -- shim's PIDFILE
#                                           (default /tmp/dewata-lifecycle-caddy.pid)
#   DEWATA_DISPOSABLE_SYSTEMCTL_ACTIVE   -- shim's active state file
#   DEWATA_FAKE_RESTART_FAILURE         -- if "1", the next "restart" call
#                                           exits non-zero to simulate a
#                                           failure (used in NEGATIVE-9)
#
# What this shim does:
#   1. It DOES NOT touch the real production systemctl.
#   2. It records every accepted call to the log file (in call order).
#   3. It supports the operations the install/rollback scripts call.
#   4. It FAILS CLOSED on ANY unrecognized command -- never passthrough.
# =============================================================================

set -u

# Default paths
: "${DEWATA_DISPOSABLE_SYSTEMCTL_LOG:=/tmp/dewata-lifecycle-systemctl.log}"
: "${DEWATA_DISPOSABLE_SYSTEMCTL_PIDFILE:=/tmp/dewata-lifecycle-caddy.pid}"
: "${DEWATA_DISPOSABLE_SYSTEMCTL_ACTIVE:=/tmp/dewata-lifecycle-caddy.active}"

LOG="$DEWATA_DISPOSABLE_SYSTEMCTL_LOG"
PIDFILE="$DEWATA_DISPOSABLE_SYSTEMCTL_PIDFILE"
ACTIVEFILE="$DEWATA_DISPOSABLE_SYSTEMCTL_ACTIVE"

ts="$(date -u +%Y%m%dT%H%M%SZ)"

cmd="${1:-}"
shift || true

log() {
    printf "[shim] %s %s %s\\n" "$ts" "$cmd" "$*" >> "$LOG"
}

case "$cmd" in

    # ----- show <unit> -p <prop> [--value] ... -----
    show)
        unit="${1:-unknown}"
        shift || true
        # parse -p KEY [--value] and ignore anything else
        prop=""
        value_mode=0
        while (( $# > 0 )); do
            case "$1" in
                -p) prop="${2:-}"; shift 2 ;;
                --value) value_mode=1; shift ;;
                *) shift ;;
            esac
        done
        case "$prop" in
            MainPID)
                if [[ -f "$PIDFILE" ]]; then
                    val=$(cat "$PIDFILE")
                else
                    val="0"
                fi
                if (( value_mode )); then
                    echo "$val"
                else
                    echo "MainPID=$val"
                fi
                log "show $unit -p $prop -> $val"
                ;;
            ActiveState)
                if [[ -f "$ACTIVEFILE" ]]; then
                    val=$(cat "$ACTIVEFILE")
                else
                    val="inactive"
                fi
                if (( value_mode )); then
                    echo "$val"
                else
                    echo "ActiveState=$val"
                fi
                log "show $unit -p $prop -> $val"
                ;;
            "")
                log "show $unit (no-prop)"
                echo "Id=shim-stub"
                ;;
            *)
                log "show $unit -p $prop (unknown-prop)"
                echo "$prop="
                ;;
        esac
        ;;

    # ----- is-active <unit> -----
    is-active)
        unit="${1:-unknown}"
        state="inactive"
        if [[ -f "$ACTIVEFILE" && "$(cat "$ACTIVEFILE")" == "1" ]]; then
            state="active"
        fi
        echo "$state"
        log "is-active $unit -> $state"
        ;;

    # ----- restart <unit> -----
    restart)
        unit="${1:-unknown}"
        log "restart $unit (entry)"
        # If a fake-restart failure is requested, fail before doing the restart work
        if [[ "${DEWATA_FAKE_RESTART_FAILURE:-0}" == "1" ]]; then
            log "restart $unit -> FAKE_FAILURE (DEWATA_FAKE_RESTART_FAILURE=1)"
            echo "[shim] FAKE restart failure on $unit" >&2
            exit 1
        fi
        # Pre-restart activity: mark inactive briefly
        printf "0\\n" > "$ACTIVEFILE"
        # Issue a new PID and mark active
        prior=$(cat "$PIDFILE" 2>/dev/null || echo 1000)
        new_pid=$((prior + 1))
        printf "%s\\n" "$new_pid" > "$PIDFILE"
        printf "1\\n" > "$ACTIVEFILE"
        log "restart $unit -> pid=$new_pid active=1"
        ;;

    # ----- start <unit> -----
    start)
        unit="${1:-unknown}"
        log "start $unit"
        printf "1\\n" > "$ACTIVEFILE"
        if [[ ! -f "$PIDFILE" ]]; then
            echo "1" > "$PIDFILE"
        fi
        ;;

    # ----- stop <unit> -----
    stop)
        unit="${1:-unknown}"
        log "stop $unit"
        printf "0\\n" > "$PIDFILE"
        printf "0\\n" > "$ACTIVEFILE"
        ;;

    # ----- status <unit> -----
    status)
        unit="${1:-unknown}"
        log "status $unit"
        if [[ -f "$ACTIVEFILE" && "$(cat "$ACTIVEFILE")" == "1" ]]; then
            echo "active (shim)"
        else
            echo "inactive (shim)"
        fi
        ;;

    # ----- is-enabled / enable / disable / mask / unmask / daemon-reload -----
    is-enabled|enable|disable|mask|unmask|daemon-reload)
        unit="${1:-unknown}"
        log "$cmd $unit (no-op)"
        ;;

    # ----- FAIL CLOSED on any unknown command.  Never passthrough. -----
    "")
        echo "FATAL: disposable-systemctl.sh invoked with no command" >&2
        exit 7
        ;;
    *)
        echo "FATAL: disposable-systemctl.sh does not implement command '$cmd' (args: $*)" >&2
        echo "       (no passthrough to real systemctl in the disposable test path)" >&2
        log "$cmd (UNHANDLED-COMMAND; fail-closed)"
        exit 7
        ;;
esac
