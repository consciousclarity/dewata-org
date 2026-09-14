#!/usr/bin/env bash
# =============================================================================
# dewata-caddy apex rollback -- control: RESTART, not reload
# =============================================================================
#
# PRODUCTION-ONLY script.  Do NOT execute unless you intend to roll back
# the apex landing page on the actual host.
#
# To exercise the install/rollback procedures end-to-end without touching
# production, run the lifecycle test:
#
#   /opt/dw-phase2/deploy/lifecycle-test/run-lifecycle-test.sh
#
# =============================================================================
#
# Restores the previous Caddyfile.dewata from the snapshot directory
# and RESTARTS the dewata-caddy service.  Returns the dewata.org apex
# to its previous broken state (catch-all 503).
#
# --------------------------------------------------------------------
# Mirror of install-apex-candidate.sh's restart semantics
# --------------------------------------------------------------------
# We use `systemctl restart` here for the same reason the installer does:
# the production Caddyfile sets `admin off`, so `systemctl reload`
# (which executes `caddy reload`) cannot push a config change.
#
# --------------------------------------------------------------------
# What this script does NOT do
# --------------------------------------------------------------------
#   - It does NOT delete the release directory.
#   - It does NOT touch DNS.
#   - It does NOT touch the host Caddy, dewata-api, or cloudflared.
#   - It does NOT use pkill or any signal that could affect
#     processes outside dewata-caddy.service.
#
# --------------------------------------------------------------------
# DNS rollback (operator-driven, in the Cloudflare dashboard)
# --------------------------------------------------------------------
# Run the following steps in this order.  Steps A and B below are the
# "reverse the apex changes" path that makes dewata.org apex unreachable
# again — explicitly labelled in the user's review notes as the
# "previous broken state":
#
#   A. Cloudflare Zero Trust -> Networks -> dewata-vps ->
#      Public Hostnames -> remove the dewata.org entry.
#   B. DNS -> dewata.org -> replace the tunnel route that's currently
#      in place with the OLD apex A records (these are the user's
#      previously-broken state, labelled as such):
#        dewata.org  A  54.149.79.189  proxy ON
#        dewata.org  A  34.216.117.25  proxy ON
#
# If the operator wants the apex to keep working through the tunnel
# (instead of returning to the previous-broken 522 state), they can
# leave the tunnel public hostname in place.  Removing the tunnel
# route is only needed to fully revert this deploy.

set -euo pipefail

WORKTREE=/opt/dw-phase2
SNAPSHOT_DIR="${1:-}"

if [[ -z "$SNAPSHOT_DIR" ]]; then
    echo "usage: $0 <SNAPSHOT_DIR>"
    echo "  snapshots are at: $WORKTREE/deploy/atomic/<utc-timestamp>-pre-apex/"
    echo "  the latest is the one to use:"
    ls -1 "$WORKTREE/deploy/atomic" 2>/dev/null | tail -1 || true
    exit 1
fi

RUNTIME_BACKUP="$SNAPSHOT_DIR/Caddyfile.dewata.runtime"
[[ -f "$SNAPSHOT_DIR" ]] || { echo "ERROR: $SNAPSHOT_DIR does not exist"; exit 1; }
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
PROD=/opt/dewata.online/deploy/caddy/Caddyfile.dewata
echo "G2: atomic install of saved runtime caddyfile to $PROD"
install -m 0644 "$RUNTIME_BACKUP" "$PROD.new"
sync
mv -f "$PROD.new" "$PROD"
echo "G2: saved runtime file installed at $PROD"

# --------------------------------------------------------------------
# G3: re-validate the now-installed file
# --------------------------------------------------------------------
echo "G3: re-validating installed file"
/usr/bin/caddy validate --config "$PROD" --adapter caddyfile

# --------------------------------------------------------------------
# G4: RESTART dewata-caddy (mirror of install's restart)
# --------------------------------------------------------------------
echo "G4: restarting dewata-caddy"
OLD_PID=$(systemctl show dewata-caddy -p MainPID --value)
echo "G4: pre-restart dewata-caddy MainPID=$OLD_PID"
systemctl restart dewata-caddy
for attempt in 1 2 3 4 5 6 7 8 9 10 11 12; do
    state=$(systemctl is-active dewata-caddy || true)
    if [[ "$state" == "active" ]]; then break; fi
    sleep 1
done
NEW_PID=$(systemctl show dewata-caddy -p MainPID --value)
echo "G4: post-restart dewata-caddy MainPID=$NEW_PID"

ss -ltn | grep -q ":8443 " && echo "G4: :8443 listening" || {
    echo "ERROR: :8443 not listening after restart"; exit 1
}

# --------------------------------------------------------------------
# G5: HTTP probes
# --------------------------------------------------------------------
echo "G5: HTTP probes against the live dewata-caddy on 127.0.0.1:8443"
fail=0

probe() {
    local host="$1" path="$2" expected_code="$3" desc="$4"
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" \
        --max-time 5 \
        -H "Host: $host" \
        "http://127.0.0.1:8443$path")
    if [[ "$code" == "$expected_code" ]]; then
        printf "  OK  %-22s %-30s -> %s\n" "$host" "$path" "$code"
    else
        printf "  FAIL %-22s %-30s -> got %s expected %s  (%s)\n" \
            "$host" "$path" "$code" "$expected_code" "$desc"
        fail=1
    fi
}

# After rollback, dewata.org apex should be 503 again (catch-all).
probe dewata.org          "/"                                       503 "apex now 503 (catch-all)"
probe api.dewata.org      "/health"                                 200 "api passthrough still works"
probe api.dewata.org      "/dsp/v0.1/calendar/ruleset"              200 "api dsp still works"
probe bci.dewata.org      "/"                                       503 "bci placeholder"
probe protocol.dewata.org "/"                                       503 "protocol placeholder"
probe datasets.dewata.org "/"                                       503 "datasets placeholder"
probe localhost           "/"                                       503 "catch-all"

if (( fail )); then
    echo
    echo "ROLLBACK: some probes failed.  inspect manually before further action."
    exit 1
fi

echo
echo "ROLLBACK SUCCESS"
echo "  Caddyfile: restored from $SNAPSHOT_DIR"
echo "  release files retained at /opt/dewata.online/deploy/www/dewata-org/v0.1.0-pre1/"
echo "  dewata-caddy restarted, MainPID $OLD_PID -> $NEW_PID"
echo
echo "PAUSE -- next steps are operator-driven in the Cloudflare dashboard,"
echo "in this exact order:"
echo
echo "  A. Cloudflare Zero Trust -> Networks -> dewata-vps ->"
echo "     Public Hostnames -> remove the dewata.org entry."
echo "  B. (Optional, only to return the apex to the user's known-broken"
echo "     state) replace whatever currently serves dewata.org with:"
echo "       dewata.org A 54.149.79.189  proxy ON"
echo "       dewata.org A 34.216.117.25  proxy ON"
echo
echo "  If A is not done before B, the apex A records will briefly"
echo "  inherit the tunnel routing and serve the apex page on top of"
echo "  the A record backends.  Do A first."
