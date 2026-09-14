#!/usr/bin/env bash
# =============================================================================
# dewata-caddy apex install -- control: RESTART, not reload
# =============================================================================
#
# PRODUCTION-ONLY script.  Do NOT edit production paths unless you intend to
# install the apex landing page on the actual host.
#
# To exercise the install/rollback procedures end-to-end without touching
# production, run the lifecycle test:
#
#   /opt/dw-phase2/deploy/lifecycle-test/run-lifecycle-test.sh
#
# which mirrors these procedures against an isolated disposable instance on
# 127.0.0.1:18443.  Production paths under /opt/dewata.online are NEVER
# touched in that test.
#
# =============================================================================
#
# This script performs the validated whole-file replacement of the
# production Caddyfile.dewata with the candidate Caddyfile.dewata.proposed,
# then RESTARTS the dewata-caddy service so the new config takes effect.
#
# --------------------------------------------------------------------
# Why RESTART and not RELOAD
# --------------------------------------------------------------------
# Caddy's reload path uses the admin API (POST /config/load).  The
# production Caddyfile.dewata sets `admin off`, so there is no admin
# endpoint to receive the reload and the reload command fails or
# hangs.  The system ExecStart/ExecReload hooks therefore cannot be
# used to push config changes.
#
# Restart briefly interrupts port 8443.  The api.dewata.org tunnel
# ingress routes directly to http://localhost:8765 (NOT through
# dewata-caddy), so the api is **not** interrupted by the restart.
#
# --------------------------------------------------------------------
# What this script does NOT touch
# --------------------------------------------------------------------
#   - DNS records (Cloudflare dashboard work is operator-driven).
#   - the api.dewata.org tunnel route (left as-is).
#   - the host Caddy (different config path /etc/caddy/Caddyfile).
#   - cloudflared.service
#   - dewata-api.service
#   - any systemd units other than dewata-caddy.
#
# --------------------------------------------------------------------
# Stage gates
# --------------------------------------------------------------------
#   G1  validate the candidate with the installed caddy binary.
#   G2  snapshot the current production Caddyfile.
#   G3  stage release files into the versioned release dir;
#       refuse to overwrite an existing release with new content
#       unless every file's sha256 matches the source.
#   G4  atomic-install the candidate file.
#   G5  re-validate the now-installed file.
#   G6  restart dewata-caddy (graceful stop, then start).
#   G7  probe the live :8443 with Host: dewata.org; verify api/bci/
#       protocol/datasets/catch-all remain on their original paths.

set -euo pipefail

PROD=/opt/dewata.online/deploy/caddy/Caddyfile.dewata
PROD_WWW=/opt/dewata.online/deploy/www
WORKTREE=/opt/dw-phase2
CANDIDATE=$WORKTREE/deploy/caddy/Caddyfile.dewata.proposed
RELEASE_SRC=$WORKTREE/deploy/www/dewata-org/v0.1.0-pre1
RELEASE_DST=$PROD_WWW/dewata-org/v0.1.0-pre1

# --------------------------------------------------------------------
# G0: refuse to run if production state is unexpected
# --------------------------------------------------------------------
[[ -f "$CANDIDATE" ]] || { echo "ERROR: candidate $CANDIDATE missing"; exit 1; }
[[ -f "$PROD" ]] || { echo "ERROR: production $PROD missing"; exit 1; }

# --------------------------------------------------------------------
# G1: validate candidate
# --------------------------------------------------------------------
echo "G1: validating candidate (installed caddy binary, --adapter caddyfile)"
/usr/bin/caddy validate --config "$CANDIDATE" --adapter caddyfile

# --------------------------------------------------------------------
# G2: snapshot
# --------------------------------------------------------------------
SNAPSHOT_DIR="$WORKTREE/deploy/atomic/$(date -u +%Y%m%dT%H%M%SZ)-pre-apex"
mkdir -p "$SNAPSHOT_DIR"
install -m 0644 "$PROD" "$SNAPSHOT_DIR/Caddyfile.dewata.runtime"
install -m 0644 "$CANDIDATE" "$SNAPSHOT_DIR/Caddyfile.dewata.candidate"
diff -u "$SNAPSHOT_DIR/Caddyfile.dewata.runtime" \
        "$SNAPSHOT_DIR/Caddyfile.dewata.candidate" \
        > "$SNAPSHOT_DIR/Caddyfile.dewata.diff" || true
echo "G2: snapshot saved to $SNAPSHOT_DIR"

# --------------------------------------------------------------------
# G3: stage release files WITHOUT rsync --delete
# --------------------------------------------------------------------
# We never delete files in the production release dir unless the
# file's sha256 matches the source.  An existing on-disk release with
# different content is treated as "conflicting" and the install ABORTS
# rather than overwrite it.  This protects against accidentally
# clobbering v0.1.0-pre1/ with future-version files that happen to
# land on disk later.
echo "G3: staging release files into $RELEASE_DST"

mkdir -p "$(dirname "$RELEASE_DST")"

need_to_clone() {
    if [[ ! -d "$RELEASE_DST" ]]; then
        return 0  # yes, need to clone
    fi
    if [[ -z "$(ls -A "$RELEASE_DST" 2>/dev/null)" ]]; then
        return 0  # empty destination
    fi
    return 1  # non-empty existing dir: do not clone, verify below
}

declare -a mismatches=()
if need_to_clone; then
    if [[ -d "$RELEASE_DST" ]] && [[ -n "$(ls -A "$RELEASE_DST" 2>/dev/null)" ]]; then
        echo "ERROR: $RELEASE_DST exists and is non-empty."
        echo "       refusing to clobber.  remove manually if intentional."
        exit 1
    fi
    mkdir -p "$RELEASE_DST"
    # clone: only copy files from source that don't already exist locally.
    # every file is sha256-verified at the destination afterwards.
    (cd "$RELEASE_SRC" && find . -type f -print0) \
        | while IFS= read -r -d '' src_file; do
            rel="${src_file#./}"
            dst_file="$RELEASE_DST/$rel"
            mkdir -p "$(dirname "$dst_file")"
            if [[ ! -f "$dst_file" ]]; then
                cp -p "$RELEASE_SRC/$rel" "$dst_file"
            fi
        done
fi

# verify every existing destination file's content matches the source.
# if any file differs, refuse.
(cd "$RELEASE_SRC" && find . -type f -print0) \
    | while IFS= read -r -d '' src_file; do
        rel="${src_file#./}"
        dst_file="$RELEASE_DST/$rel"
        if [[ ! -f "$dst_file" ]]; then
            echo "ERROR: missing file $dst_file"
            exit 2
        fi
        ssum=$(sha256sum "$RELEASE_SRC/$rel"   | awk '{print $1}')
        dsum=$(sha256sum "$dst_file"           | awk '{print $1}')
        if [[ "$ssum" != "$dsum" ]]; then
            echo "MISMATCH: $rel"
            echo "  src: $ssum"
            echo "  dst: $dsum"
            exit 3
        fi
    done

# count files for the report
n_files=$(cd "$RELEASE_DST" && find . -type f | wc -l)
echo "G3: release staged; $n_files files at $RELEASE_DST (sha256-verified)"

# --------------------------------------------------------------------
# G4: atomic install of the candidate caddyfile
# --------------------------------------------------------------------
echo "G4: atomic install of the candidate caddyfile"
install -m 0644 "$CANDIDATE" "$PROD.new"
sync
mv -f "$PROD.new" "$PROD"
echo "G4: candidate installed at $PROD"

# --------------------------------------------------------------------
# G5: re-validate the installed file
# --------------------------------------------------------------------
echo "G5: re-validating installed file"
/usr/bin/caddy validate --config "$PROD" --adapter caddyfile

# --------------------------------------------------------------------
# G6: RESTART the dewata-caddy service (not reload; see file header)
# --------------------------------------------------------------------
# This is the actual caddy process restart that systemctl restarts
# would perform.  We do not use systemctl reload because the admin
# endpoint is disabled.  We do not use pkill: systemd owns the process.

# First, capture the deployment timestamp for the audit trail.
INSTALL_TS=$(date -u +%Y%m%dT%H%M%SZ)
echo "G6: restarting dewata-caddy (graceful; expect ~2-3s :8443 interruption)"

# capture the service's main PID BEFORE restart for the audit trail
OLD_PID=$(systemctl show dewata-caddy -p MainPID --value)
echo "G6: pre-restart dewata-caddy MainPID=$OLD_PID"

# systemctl restart is synchronous on Type=notify; we wait for ActiveState
# to flip to active before resuming.
systemctl restart dewata-caddy

# Wait for the listener to come back up.
for attempt in 1 2 3 4 5 6 7 8 9 10 11 12; do
    state=$(systemctl is-active dewata-caddy || true)
    if [[ "$state" == "active" ]]; then
        break
    fi
    sleep 1
done

NEW_PID=$(systemctl show dewata-caddy -p MainPID --value)
echo "G6: post-restart dewata-caddy MainPID=$NEW_PID"

# Make sure :8443 is actually listening
ss -ltn | grep -q ":8443 " && echo "G6: :8443 listening" || {
    echo "ERROR: :8443 not listening after restart"; exit 1
}

# --------------------------------------------------------------------
# G7: HTTP probes against the running service
# --------------------------------------------------------------------
echo "G7: HTTP probes against the live dewata-caddy on 127.0.0.1:8443"
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

probe dewata.org          "/"                                       200 "apex landing (Beranda)"
probe dewata.org          "/index.html"                             200 "apex explicit index"
probe dewata.org          "/calendar.html"                          200 "apex calendar (scaffolded)"
probe dewata.org          "/about.html"                             200 "apex about"
probe dewata.org          "/transparency.html"                      200 "apex transparency"
probe dewata.org          "/assets/style.css"                       200 "apex css asset"
probe dewata.org          "/assets/locales/provenance.computed.json"  200 "apex locale asset"
probe api.dewata.org      "/health"                                 200 "api passthrough"
probe api.dewata.org      "/dsp/v0.1/calendar/ruleset"              200 "api dsp"
probe api.dewata.org      "/brief"                                  200 "api engineering brief"
probe bci.dewata.org      "/"                                       503 "bci placeholder"
probe protocol.dewata.org "/"                                       503 "protocol placeholder"
probe datasets.dewata.org "/"                                       503 "datasets placeholder"
probe localhost           "/"                                       503 "catch-all"

if (( fail )); then
    echo
    echo "INSTALL: some probes failed.  do NOT continue to the dashboard step."
    echo "Run rollback-apex.sh against the snapshot at $SNAPSHOT_DIR"
    exit 1
fi

# Save the post-install main-pid for the audit trail.
echo "$OLD_PID -> $NEW_PID at $INSTALL_TS" >> "$SNAPSHOT_DIR/restart.log"
echo "$INSTALL_TS" >> "$SNAPSHOT_DIR/installed.txt"

echo
echo "INSTALL SUCCESS"
echo "  snapshot:    $SNAPSHOT_DIR"
echo "  release:     $RELEASE_DST"
echo "  dewata-caddy restarted, MainPID $OLD_PID -> $NEW_PID"
echo "  apex:        http://127.0.0.1:8443/  (Host: dewata.org) returns the bci"
echo "  api:         http://127.0.0.1:8443/health  (Host: api.dewata.org) returns 200"
echo
echo "PAUSE -- next step is operator-driven Cloudflare dashboard work:"
echo "  1. Zero Trust -> dewata-vps -> Public Hostnames -> add:"
echo "       hostname:  dewata.org"
echo "       service:   HTTP   URL:   http://127.0.0.1:8443"
echo "  2. Once the tunnel route is active in the dashboard,"
echo "     verify the apex with a real browser (browser rendering"
echo "     has not been confirmed via this headless harness)."
echo "  3. To redirect existing apex traffic, replace both existing"
echo "     apex A records with the same dewata.org public hostname"
echo "     record just added in step 1 (Cloudflare will point them"
echo "     all at the same tunnel origin)."
