#!/usr/bin/env bash
# =============================================================================
# dewata-caddy apex rollback
# =============================================================================
#
# Restores the previous Caddyfile.dewata from the snapshot directory.
# Keeps the release files in place (per the brief: "do not delete the
# release directory").  This means a subsequent re-deploy can re-point
# the Caddyfile at the same v0.1.0-pre1/ directory without re-rsyncing.
#
# Usage:
#   ./rollback-apex.sh <SNAPSHOT_DIR>
#
# The snapshot directory is created by install-apex-candidate.sh and is
# identified by timestamp (e.g. 20260914T153000Z-pre-apex).
#
# DNS rollback is a manual operation done in Cloudflare.  The DNS
# rollback order is documented but is NOT executed here:
#
#   1. remove the dewata.org public hostname from the dewata-vps tunnel
#   2. restore the previous apex A records:
#        dewata.org A 54.149.79.189  proxy ON
#        dewata.org A 34.216.117.25  proxy ON
#
# After this 2-step DNS rollback, the tunnel route no longer intercepts
# the apex and the A records point at the previous broken state, which
# served the user's question of "where did the 522 come from?".  This
# is intentional: the brief says to label those A records as the
# "previous broken DNS state".

set -euo pipefail

WORKTREE=/opt/dw-phase2
SNAPSHOT_DIR="${1:-}"

if [[ -z "$SNAPSHOT_DIR" ]]; then
    echo "usage: $0 <SNAPSHOT_DIR>"
    echo "  snapshot dirs are at: $WORKTREE/deploy/atomic/*-pre-apex/"
    exit 1
fi

if [[ ! -d "$SNAPSHOT_DIR" ]]; then
    echo "ERROR: $SNAPSHOT_DIR does not exist"
    exit 1
fi

# Identify the saved runtime Caddyfile in the snapshot.
RUNTIME_BACKUP="$SNAPSHOT_DIR/Caddyfile.dewata.runtime"
[[ -f "$RUNTIME_BACKUP" ]] || { echo "ERROR: $RUNTIME_BACKUP missing"; exit 1; }

# Validate the saved file before installing.
echo "validating $RUNTIME_BACKUP"
/usr/bin/caddy validate --config "$RUNTIME_BACKUP" --adapter caddyfile || {
    echo "ERROR: saved file does not validate; refusing to install"
    exit 1
}

# Atomic install of the saved runtime caddyfile.
PROD=/opt/dewata.online/deploy/caddy/Caddyfile.dewata
install -m 0644 "$RUNTIME_BACKUP" "$PROD.new"
sync
mv "$PROD.new" "$PROD"
echo "rollback installed at $PROD"

# Reload the service.
systemctl reload dewata-caddy
sleep 2

# Smoke probe: catch-all now active (no @apex route).
probe() {
    local host="$1" path="$2" expected_code="$3"
    local code
    code=$(curl -s -o /tmp/rollback.body -w "%{http_code}" \
        --max-time 5 \
        -H "Host: $host" \
        "http://127.0.0.1:8443$path")
    if [[ "$code" == "$expected_code" ]]; then
        printf "  OK   %-22s %-22s -> %s\n" "$host" "$path" "$code"
    else
        printf "  FAIL %-22s %-22s -> got %s expected %s\n" "$host" "$path" "$code" "$expected_code"
        return 1
    fi
}

probe dewata.org /                    503
probe api.dewata.org /health          200
probe bci.dewata.org /                503
probe localhost /                     503

echo
echo "ROLLBACK SUCCESS"
echo "  Caddyfile: restored to pre-apex state"
echo "  Release files retained at /opt/dewata.online/deploy/www/dewata-org/v0.1.0-pre1/"
echo "  Dashboard work needed to fully revert (DO THIS IN THE CLOUDFLARE UI):"
echo
echo "  Step A. Zero Trust → Networks → dewata-vps → Public Hostnames"
echo "          -> remove the dewata.org entry"
echo "  Step B. DNS → dewata.org → restore these A records (these are the OLD"
echo "          state known to have caused 522 — restore only if you want the"
echo "          apex to be unreachable through the tunnel):"
echo "            dewata.org A 54.149.79.189  proxy ON"
echo "            dewata.org A 34.216.117.25  proxy ON"
echo
echo "  Step A must complete BEFORE Step B.  Otherwise the apex A records"
echo "  briefly inherit the tunnel routing, which is what the A records"
echo "  previously fought with."
