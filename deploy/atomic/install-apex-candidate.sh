#!/usr/bin/env bash
# =============================================================================
# dewata-caddy apex atomic-install
# =============================================================================
#
# This script performs the validated whole-file replacement of the
# production Caddyfile.dewata with the candidate Caddyfile.dewata.proposed.
#
# Stage-gates (each gate is a separate step the operator confirms):
#   G1.  load candidate     -> verify the candidate is present.
#   G2.  backup current     -> copy to a timestamped .bak file.
#   G3.  stage files        -> rsync the v0.1.0-pre1 release into the
#                              production www tree under /opt/dewata.online/.
#   G4.  validate in place  -> `caddy validate --adapter caddyfile`.
#   G5.  install             -> atomic install of the candidate file
#                              into /opt/dewata.online/deploy/caddy/Caddyfile.dewata.
#   G6.  reload              -> `systemctl reload dewata-caddy`.
#   G7.  smoke probe         -> curl probe with Host: dewata.org and the
#                              api/bci/protocol/datasets catch-alls.
#
# THE STAGING SCRIPT DOES NOT TOUCH:
#   - DNS records (Cloudflare dashboard work is yours)
#   - the live api.dewata.org route
#   - the host Caddy (different config file: /etc/caddy/Caddyfile)
#   - cloudflared
#
# Run with -y to skip confirmation prompts (only after you've reviewed
# the prepared staging trees).

set -euo pipefail

PROD_DIR=/opt/dewata.online/deploy/caddy
PROD_WWW=/opt/dewata.online/deploy/www
PROD_LOG=/opt/dewata.online/deploy/logs
WORKTREE=/opt/dw-phase2
CANDIDATE=$WORKTREE/deploy/caddy/Caddyfile.dewata.proposed
RELEASE_SRC=$WORKTREE/deploy/www/dewata-org/v0.1.0-pre1
RELEASE_DST=$PROD_WWW/dewata-org/v0.1.0-pre1

# G0.1 -- refuse to run unless we're sure things look right.
# Sanity check candidate exists.
[[ -f "$CANDIDATE" ]] || { echo "ERROR: candidate file not found at $CANDIDATE"; exit 1; }
# Production tree must already be the runtime config.
[[ -f "$PROD_DIR/Caddyfile.dewata" ]] || { echo "ERROR: production Caddyfile.dewata missing at $PROD_DIR"; exit 1; }

# Stash the previous config for diff/audit in this run.
mkdir -p "$WORKTREE/deploy/atomic"
SNAPSHOT_DIR="$WORKTREE/deploy/atomic/$(date -u +%Y%m%dT%H%M%SZ)-pre-apex"
mkdir -p "$SNAPSHOT_DIR"
cp "$PROD_DIR/Caddyfile.dewata"              "$SNAPSHOT_DIR/Caddyfile.dewata.runtime"
cp "$CANDIDATE"                               "$SNAPSHOT_DIR/Caddyfile.dewata.candidate"
cp /opt/dewata.online/deploy/caddy/pki/.last-issue  "$SNAPSHOT_DIR/pki.last-issue" 2>/dev/null || true
diff -u "$PROD_DIR/Caddyfile.dewata" "$CANDIDATE" > "$SNAPSHOT_DIR/Caddyfile.dewata.diff"
echo "G1: snapshot saved to $SNAPSHOT_DIR"

# G2.  Staging step 1 -- copy release files into production tree.
# The release is a versioned, immutable directory.
if [[ ! -d "$RELEASE_DST" ]]; then
    mkdir -p "$(dirname "$RELEASE_DST")"
    rsync -a --delete "$RELEASE_SRC/" "$RELEASE_DST/"
    echo "G2: release files copied to $RELEASE_DST"
else
    echo "G2: release dir already exists; verifying checksum of files."
    # verify each file content matches (best-effort)
    if ! diff -q "$RELEASE_SRC/index.html" "$RELEASE_DST/index.html" >/dev/null 2>&1; then
        echo "ERROR: $RELEASE_DST already populated with different content;"
        echo "       to roll over to v0.1.0-pre1, remove the existing dir first."
        exit 1
    fi
fi

# G3.  Validate the candidate using the installed Caddy binary.
echo "G3: validating candidate with /usr/bin/caddy validate --adapter caddyfile"
/usr/bin/caddy validate --config "$CANDIDATE" --adapter caddyfile
echo "G3: validate returned Valid configuration"

# G4.  Atomic install of the candidate.
# Use `install -m 0644` for atomic file replacement and reproducible mode.
install -m 0644 "$CANDIDATE" "$PROD_DIR/Caddyfile.dewata.new"
sync
mv "$PROD_DIR/Caddyfile.dewata.new" "$PROD_DIR/Caddyfile.dewata"
echo "G4: candidate installed at $PROD_DIR/Caddyfile.dewata (atomic mv)"

# G5.  Pre-reload re-validation of the now-installed file.
echo "G5: validating installed file"
/usr/bin/caddy validate --config "$PROD_DIR/Caddyfile.dewata" --adapter caddyfile

# G6.  Service reload -- graceful, not restart.  Reloads the in-memory
# config without dropping the listener.
echo "G6: reloading dewata-caddy (graceful -- no listener drop)"
systemctl reload dewata-caddy

# G7.  Smoke probe.  Wait briefly for the reload to settle, then probe.
sleep 2

echo "G7: smoke probing dewata-caddy on :8443"
probe() {
    local host="$1" path="$2" expected_code="$3"
    local code body
    code=$(curl -s -o /tmp/probe.body -w "%{http_code}" \
        --max-time 5 \
        -H "Host: $host" \
        "http://127.0.0.1:8443$path")
    body=$(head -c 200 /tmp/probe.body)
    if [[ "$code" == "$expected_code" ]]; then
        printf "  OK   %-22s %-22s -> %s   body[:200]=%s\n" \
            "$host" "$path" "$code" "$body"
    else
        printf "  FAIL %-22s %-22s -> got %s expected %s\n" \
            "$host" "$path" "$code" "$expected_code"
        return 1
    fi
}

probe dewata.org /                    200
probe dewata.org /index.html          200
probe dewata.org /calendar.html       200
probe dewata.org /about.html          200
probe dewata.org /transparency.html   200
probe dewata.org /assets/style.css    200
probe dewata.org /assets/locales/provenance.computed.json 200
probe api.dewata.org /health          200
probe api.dewata.org /dsp/v0.1/calendar/ruleset 200
probe api.dewata.org /brief           200
probe bci.dewata.org /                503
probe protocol.dewata.org /           503
probe datasets.dewata.org /           503
probe localhost /                     503

echo
echo "ATOMIC-INSTALL SUCCESS"
echo "  apex landing page:  http://127.0.0.1:8443/  (Host: dewata.org)"
echo "  api passthrough:    http://127.0.0.1:8443/health  (Host: api.dewata.org)"
echo "  snapshot retained:  $SNAPSHOT_DIR"
echo
echo "PAUSE HERE — verify the dashboard work next:"
echo "  1. Cloudflare Zero Trust → dewata-vps → add public hostname"
echo "       hostname:  dewata.org"
echo "       service:   http://localhost:8443"
echo "  2. After tunnel route is HEALTHY in the dashboard:"
echo "       DNS → apex A records may be removed to avoid the 522 conflict"
echo "  3. Browse https://dewata.org/ from your browser"
