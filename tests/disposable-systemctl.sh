#!/usr/bin/env bash
# =============================================================================
# disposable-systemctl.sh -- the systemctl shim used by the lifecycle test
# =============================================================================
#
# Lifecycle test relies on this script (not the real systemctl) when
# DEWATA_DISPOSABLE_MODE=1.  Test sets PATH to put this shim first.
#
# What it does:
#   show     MainPID:    reads /tmp/dewata-lifecycle-caddy.pid (writeable
#                       by the test harness)
#   is-active <unit>:    reads /tmp/dewata-lifecycle-caddy.active
#                       (returns "active" if "1", "inactive" otherwise)
#   restart <unit>:      writes "restart: $(date -u +%Y%m%dT%H%M%SZ) unit=<unit>"
#                       to /tmp/dewata-lifecycle-systemctl.log
#   start   <unit>:      same as restart
#   stop    <unit>:      writes to log, sets active=0
#   status  <unit>:      reads the log file
#
# Anything else: log and pass through to the real systemctl.
#
# The lifecycle test launches caddy as a child process on a
# disposable port (e.g. 18443) outside of any systemd involvement,
# then asserts via this shim that the install/rollback script
# invoked systemctl in the documented sequence.
# =============================================================================

readonly REAL_SYSTEMCTL="$(command -v systemctl 2>/dev/null || echo "/bin/false")"
readonly LOG="/tmp/dewata-lifecycle-systemctl.log"
readonly PIDFILE="/tmp/dewata-lifecycle-caddy.pid"
readonly ACTIVEFILE="/tmp/dewata-lifecycle-caddy.active"

ts="$(date -u +%Y%m%dT%H%M%SZ)"

case "${1:-}" in
    show)
        unit="${2:-unknown}"
        # collect -p KEY [--value] [--other...] argument tokens
        shift 2
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
                echo "[shim] $ts show $unit -p $prop -> $val" >> "$LOG"
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
                echo "[shim] $ts show $unit -p $prop -> $val" >> "$LOG"
                ;;
            "")
                echo "[shim] $ts show $unit (no-prop)" >> "$LOG"
                # no -p flag; return a stub.
                echo "Id=shim-stub"
                ;;
            *)
                echo "[shim] $ts show $unit -p $prop (unknown-prop)" >> "$LOG"
                echo "$prop="
                ;;
        esac
        ;;
    is-active)
        unit="${2:-unknown}"
        state="inactive"
        if [[ -f "$ACTIVEFILE" && "$(cat "$ACTIVEFILE")" == "1" ]]; then
            state="active"
        fi
        echo "$state"
        echo "[shim] $ts is-active $unit -> $state" >> "$LOG"
        ;;
    restart|start)
        unit="${2:-unknown}"
        # bump PID so the install's no-op check sees MainPID changed
        : > "$PIDFILE"
        # new PID = current log-size mod max, so each restart bumps it
        prior_pid=$(awk -F'=pid=' '/^restart/{count++}END{print count+1000}' "$LOG" 2>/dev/null || echo 1000)
        printf "%s\\n" "$prior_pid" > "$PIDFILE"
        printf "1\\n" > "$ACTIVEFILE"
        echo "[shim] $ts $1 $unit -> pid=$prior_pid active=1" >> "$LOG"
        ;;
    stop)
        unit="${2:-unknown}"
        : > "$PIDFILE"
        printf "0\\n" > "$PIDFILE"
        printf "0\\n" > "$ACTIVEFILE"
        echo "[shim] $ts stop $unit -> pid=0 active=0" >> "$LOG"
        ;;
    status)
        unit="${2:-unknown}"
        echo "[shim] $ts status $unit" >> "$LOG"
        if [[ -f "$ACTIVEFILE" && "$(cat "$ACTIVEFILE")" == "1" ]]; then
            echo "active (shim)"
        else
            echo "inactive (shim)"
        fi
        ;;
    is-enabled|enable|disable|mask|unmask|daemon-reload)
        unit="${2:-unknown}"
        echo "[shim] $ts $1 $unit (no-op)" >> "$LOG"
        ;;
    *)
        # anything else: pass-through to the real systemctl
        # but only if the real one exists.
        if [[ -f "$REAL_SYSTEMCTL" ]]; then
            echo "[shim] $ts $* (passthrough)" >> "$LOG"
            "$REAL_SYSTEMCTL" "$@"
        else
            echo "[shim] $ts $* (passthrough-failed-no-real-systemctl)" >> "$LOG"
            exit 0
        fi
        ;;
esac
