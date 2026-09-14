#!/usr/bin/env bash
# =============================================================================
# disposable-validate.sh -- the validation adapter used by tests
# =============================================================================
#
# Mirrors `caddy validate --config <file>` but is a separate exec so the
# installer can be redirected to it via DEWATA_VALIDATE_CMD.  Honors:
#
#   DEWATA_FAKE_VALIDATE_FAILURE   -- if "1", the next invocation exits
#                                     non-zero (used by NEGATIVE-10 to
#                                     exercise the recovery-validation
#                                     failure path WITHOUT corrupting the
#                                     snapshot file).
#
#   argument 1: the Caddyfile path to "validate"
#
# Exit codes:
#   0 -- the Caddyfile validated.
#   1 -- the Caddyfile did not validate (FAKE failure).
#   7 -- no argument supplied / unknown subcommand.
# =============================================================================

set -u

LOG="${DEWATA_VALIDATE_LOG:-${DEWATA_DISPOSABLE_VALIDATE_LOG:-/tmp/dewata-lifecycle-validate.log}}"
ts="$(date -u +%Y%m%dT%H%M%SZ)"

arg="${1:-}"
log() { printf "[validate] %s %s\\n" "$ts" "$*" >> "$LOG"; }

if [[ -z "$arg" ]]; then
    echo "FATAL: disposable-validate.sh invoked without a Caddyfile path" >&2
    exit 7
fi

# Record the call
log "validate $arg"

# Optional fake-failure hook (used by NEGATIVE-10 to exercise the
# do_restore validation-failure path without touching real caddy or
# corrupting snapshots).
if [[ "${DEWATA_FAKE_VALIDATE_FAILURE:-0}" == "1" ]]; then
    log "FAKE_VALIDATE_FAILURE -- exiting 1"
    echo "Invalid Caddyfile: \"syntax error in disposable validation (DEWATA_FAKE_VALIDATE_FAILURE=1)\"" >&2
    exit 1
fi

# Check that the file exists and looks like a caddyfile.
if [[ ! -f "$arg" ]]; then
    echo "Invalid Caddyfile: file $arg does not exist" >&2
    exit 1
fi
# Minimal structural check: looking for an opening brace and at least
# one site block or option.  Real caddy has much richer checks; this
# is just enough to make a Caddyfile that doesn't look like one fail.
if ! grep -q '^[[:space:]]*{[[:space:]]*$' "$arg"; then
    echo "Invalid Caddyfile: missing top-level opening brace" >&2
    exit 1
fi

# Touch the file's mtime (the installer's logger reads it later).
touch -c "$arg"
log "validate OK"
exit 0
