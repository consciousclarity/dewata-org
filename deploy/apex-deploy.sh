#!/usr/bin/env bash
# =============================================================================
# apex-deploy.sh -- one-shot operator wrapper for install-apex-candidate.sh
# =============================================================================
#
# The wrapper:
#   1. Verifies DEWATA_APPLY_PRODUCTION=1 (the installer's authorization
#      flag).  If unset, refuses to run.
#   2. Reads the production Caddyfile's actual sha256 and passes it as
#      DEWATA_PROD_BASELINE_SHA (mandatory drift guard).
#   3. Invokes the installer with all required env vars set explicitly.
#      No default values are accepted; every DEWATA_* path is a
#      mandatory, non-empty env var.
#   4. Captures the installer's actual snapshot path from stdout so the
#      operator knows which snapshot to roll back to (rollback is
#      idempotent -- the same path can be rolled back multiple times).
#   5. Refuses to run if a fresh install ran in the last 60 seconds
#      (idempotence / cooldown).
#
# Source / destination separation:
#   Source files (candidate Caddyfile + reviewed release tree) live
#   under DEWATA_REVIEWED_RELEASE_ROOT, e.g.
#     /opt/dewata.online/review/v0.1.0-pre1/
#   Production destination files (live Caddyfile + live release tree)
#   live under DEWATA_PROD_WWW, e.g.
#     /opt/dewata.online/deploy/www/
#   These are SEPARATE trees.  The installer copies FROM source TO
#   destination; it never reads from the destination as a source.
#
# Run from /opt/dewata.online/deploy:
#     bash apex-deploy.sh
#
# Author: operator (run only when the bundle review authorizes it).
#
# This script is intentionally small.  All work is in the installer.
# =============================================================================

set -Eeuo pipefail

# Required authorization flag (mutually exclusive with DEWATA_DISPOSABLE_MODE).
if [[ "${DEWATA_APPLY_PRODUCTION:-0}" != "1" ]]; then
    echo "FATAL: DEWATA_APPLY_PRODUCTION=1 must be set to authorize a production install." >&2
    echo "  this script is the only authorized entry point for /opt/dewata.online installs." >&2
    echo "  set DEWATA_APPLY_PRODUCTION=1 explicitly.  there is no default." >&2
    exit 2
fi

# Required location of the operator-managed deploy directory.
# The installer is launched via absolute path, NEVER via $PATH or
# relative path, to prevent CWD-shadowing attacks.
INSTALLER="/opt/dewata.online/deploy/atomic/install-apex-candidate.sh"
ROLLBACK="/opt/dewata.online/deploy/atomic/rollback-apex.sh"
SERVICE="dewata-caddy"
LISTENER_PORT="8443"

# --------------------------------------------------------------------
# Configuration -- the absolute paths the operator must verify before
# running.  No defaults: the operator is expected to edit these if
# the layout changes.
# --------------------------------------------------------------------
PROD_CADDY="/opt/dewata.online/deploy/caddy/Caddyfile.dewata"
PROD_WWW="/opt/dewata.online/deploy/www"
PROD_RELEASE_DST="$PROD_WWW/dewata-org/v0.1.0-pre1"
REVIEWED_RELEASE_ROOT="/opt/dewata.online/review/v0.1.0-pre1"
REVIEWED_RELEASE_SRC="$REVIEWED_RELEASE_ROOT/www/dewata-org/v0.1.0-pre1"
REVIEWED_CANDIDATE="$REVIEWED_RELEASE_ROOT/caddy/Caddyfile.dewata.proposed"
REVIEWED_MANIFEST="/opt/dewata.online/deploy/atomic/RELEASES/v0.1.0-pre1.MANIFEST.txt"

# Mandatory preflight: every reviewed and production path must exist.
require_file() {
    local name="$1" path="$2"
    if [[ ! -e "$path" ]]; then
        echo "FATAL: $name missing at $path" >&2
        return 1
    fi
}
require_file "production Caddyfile" "$PROD_CADDY"
require_file "reviewed candidate Caddyfile" "$REVIEWED_CANDIDATE"
require_file "reviewed release source" "$REVIEWED_RELEASE_SRC"
require_file "reviewed manifest" "$REVIEWED_MANIFEST"

# Snapshots live in the deploy/atomic directory (managed by the installer).
SNAPSHOT_PARENT="/opt/dewata.online/deploy/atomic"
mkdir -p "$SNAPSHOT_PARENT"

# Idempotence / cooldown: refuse to run if a recent install ran in
# the last 60 seconds.  This prevents double-clicks on the same
# bundle from racing.
recent=$(find "$SNAPSHOT_PARENT" -mindepth 1 -maxdepth 1 -type d -name "*-pre-apex" -mmin -1 -printf '%T@ %p\\n' 2>/dev/null | head -1 || true)
if [[ -n "$recent" ]]; then
    recent_age=$(awk "{print \$1}" <<< "$recent")
    now=$(date +%s)
    age_seconds=$(awk -v n="$now" -v r="$recent_age" 'BEGIN{print n - r}')
    recent_path=$(awk '{print $2}' <<< "$recent")
    if awk -v a="$age_seconds" 'BEGIN{exit !(a < 60)}'; then
        echo "FATAL: idempotence / cooldown: a previous install ran ${age_seconds}s ago at $recent_path" >&2
        echo "  wait at least 60 seconds, or remove the recent snapshot, or pass DEWATA_FORCE_REINSTALL=1." >&2
        exit 3
    fi
fi

# --------------------------------------------------------------------
# Capture the production baseline sha RIGHT NOW.
# --------------------------------------------------------------------
PROD_BASELINE_SHA=$(sha256sum "$PROD_CADDY" | cut -d' ' -f1)
echo "[deploy] production Caddyfile baseline sha256 = $PROD_BASELINE_SHA"

# --------------------------------------------------------------------
# Print the literal env-var values the installer will receive.
# --------------------------------------------------------------------
echo "[deploy] invoking: $INSTALLER"
echo "        DEWATA_APPLY_PRODUCTION=1"
echo "        DEWATA_PROD_CADDY=$PROD_CADDY"
echo "        DEWATA_PROD_WWW=$PROD_WWW"
echo "        DEWATA_RELEASE_SRC=$REVIEWED_RELEASE_SRC"
echo "        DEWATA_RELEASE_DST=$PROD_RELEASE_DST"
echo "        DEWATA_CANDIDATE=$REVIEWED_CANDIDATE"
echo "        DEWATA_REVIEWED_MANIFEST=$REVIEWED_MANIFEST"
echo "        DEWATA_PROD_BASELINE_SHA=$PROD_BASELINE_SHA"
echo "        DEWATA_LISTENER_PORT=$LISTENER_PORT"
echo "        DEWATA_WORKTREE=/opt/dw-phase2"
echo "        DEWATA_SNAPSHOT_PARENT=$SNAPSHOT_PARENT"
echo "        DEWATA_CADDY_SERVICE=$SERVICE"

# --------------------------------------------------------------------
# Run the installer.
# --------------------------------------------------------------------
output=$(
    env -i \
        PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
        DEWATA_APPLY_PRODUCTION=1 \
        DEWATA_PROD_CADDY="$PROD_CADDY" \
        DEWATA_PROD_WWW="$PROD_WWW" \
        DEWATA_RELEASE_SRC="$REVIEWED_RELEASE_SRC" \
        DEWATA_RELEASE_DST="$PROD_RELEASE_DST" \
        DEWATA_CANDIDATE="$REVIEWED_CANDIDATE" \
        DEWATA_REVIEWED_MANIFEST="$REVIEWED_MANIFEST" \
        DEWATA_PROD_BASELINE_SHA="$PROD_BASELINE_SHA" \
        DEWATA_LISTENER_PORT="$LISTENER_PORT" \
        DEWATA_WORKTREE="/opt/dw-phase2" \
        DEWATA_SNAPSHOT_PARENT="$SNAPSHOT_PARENT" \
        DEWATA_CADDY_SERVICE="$SERVICE" \
        bash "$INSTALLER"
    2>&1
)
installer_rc=$?

echo "$output"

# Capture the actual_snapshot_path line.
actual_snapshot=$(grep -E '^[[:space:]]*actual_snapshot_path=' <<< "$output" | head -1 | sed "s/^[[:space:]]*actual_snapshot_path=//")
if [[ -z "$actual_snapshot" ]]; then
    echo "[deploy] FATAL: installer did not print actual_snapshot_path=" >&2
    exit 6
fi
echo "[deploy] installer reports: $actual_snapshot"

if (( installer_rc != 0 )); then
    echo "[deploy] installer rc=$installer_rc -- fail closed." >&2
    exit "$installer_rc"
fi
echo "[deploy] installer rc=0 -- install succeeded."

# --------------------------------------------------------------------
# Dashboard cutover steps (Cloudflare -- not executed from the script)
# --------------------------------------------------------------------
echo
echo "================================================================"
echo "[deploy] dashboard cutover steps (operator):"
echo "================================================================"
echo "1. remove the apex A records at /opt/dewata.online's Cloudflare dashboard:"
echo "     - host @, value 54.149.79.189, type A,    TTL auto, proxied (delete)"
echo "     - host @, value 34.216.117.25, type A,    TTL auto, proxied (delete)"
echo "2. create the apex published-application tunnel route:"
echo "     - host @, type CNAME, target dewata-vps.cfargotunnel.com"
echo "     or:"
echo "     - on the existing tunnel dewata-vps, add an ingress rule:"
echo "       hostname: dewata.org"
echo "       service : http://localhost:8443"
echo "3. verify public:"
echo "     - curl -4 -I https://dewata.org/           expect 200"
echo "     - curl -4 -I https://api.dewata.org/health expect 200"
echo
echo "================================================================"
echo "[deploy] rollback reference"
echo "================================================================"
echo "    bash $ROLLBACK \${actual_snapshot_path}"
echo
