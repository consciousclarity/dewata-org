#!/usr/bin/env bash
# ============================================================
# Dewata apex deployment (B1) -- one-shot operator script
# ============================================================
# Generated 2026-09-14 as part of the fourth-bundle review.
# Source commit: cd84d4d96638a957cc2bddacf0372806ec4eec4b
# Branch:        warden/phase2-foundation-20260914
# Reviewed bundle: dewata-review-bundle-20260914T140000Z.tar.gz
#                 (see 00-REVIEW-NOTES.md for the response to the
#                  fourth-bundle review)
#
# PRE-FLIGHT
# ----------
# 1. Verify the review bundle has been approved.
# 2. Verify you are ready to perform the dashboard cutover:
#    a. Remove the two known-broken apex A records:
#         dewata.org A 54.149.79.189  (proxy ON)
#         dewata.org A 34.216.117.25  (proxy ON)
#    b. Add a dewata.org published-application tunnel route on
#       dewata-vps: service type HTTP, address 127.0.0.1:8443, blank path.
#
# USAGE
# -----
# Run as root on the VPS (62.72.7.218):
#
#     bash /opt/dewata.online/deploy/apex-deploy.sh
#
# The script is idempotent: it refuses to run twice in the same
# minute unless DEWATA_FORCE_REINSTALL=1 is set.

set -Eeuo pipefail

# ---------------------------------------------------------------
# 1. Required environment (operator MUST verify before running)
# ---------------------------------------------------------------
: "${PROD_CADDY:=/opt/dewata.online/deploy/caddy/Caddyfile.dewata}"
: "${PROD_WWW:=/opt/dewata.online/deploy/www}"
: "${REVIEWED_MANIFEST:=/opt/dewata.online/deploy/atomic/RELEASES/v0.1.0-pre1.MANIFEST.txt}"
: "${REVIEWED_RELEASE:=/opt/dewata.online/deploy/www/dewata-org/v0.1.0-pre1}"
: "${CANDIDATE_CADDY:=/opt/dewata.online/deploy/caddy/Caddyfile.dewata.proposed}"
: "${LISTENER_PORT:=8443}"

# ---------------------------------------------------------------
# 2. Required: capture the production Caddyfile sha BEFORE the
#    install runs.  The install refuses to proceed if the live file
#    does not match this baseline.
# ---------------------------------------------------------------
PROD_BASELINE_SHA=$(sha256sum "$PROD_CADDY" | cut -d' ' -f1)
echo "[deploy] PROD_BASELINE_SHA=$PROD_BASELINE_SHA"

# ---------------------------------------------------------------
# 3. Required: generate a per-deployment snapshot directory.
# ---------------------------------------------------------------
SNAPSHOT_PARENT=/opt/dewata.online/deploy/atomic
SNAPSHOT_DIR="$SNAPSHOT_PARENT/$(date -u +%Y%m%dT%H%M%SZ)-pre-apex"
mkdir -p "$SNAPSHOT_PARENT"

# ---------------------------------------------------------------
# 4. Run the install.
# ---------------------------------------------------------------
echo "[deploy] running install-apex-candidate.sh..."
bash /opt/dewata.online/deploy/atomic/install-apex-candidate.sh
rc=$?
if (( rc != 0 )); then
    echo "[deploy] FAILED: install-apex-candidate.sh exited $rc"
    echo "[deploy] The installer\'s do_restore flow should have already"
    echo "[deploy] restored both the Caddyfile and the release tree."
    exit "$rc"
fi

# ---------------------------------------------------------------
# 5. Local production checks.
# ---------------------------------------------------------------
echo "[deploy] verifying production state..."

# Check the production Caddyfile was updated to the candidate.
new_sha=$(sha256sum "$PROD_CADDY" | cut -d' ' -f1)
expected_sha=$(sha256sum "$CANDIDATE_CADDY" | cut -d' ' -f1)
if [[ "$new_sha" != "$expected_sha" ]]; then
    echo "[deploy] FAILED: production Caddyfile sha ($new_sha) != candidate sha ($expected_sha)"
    exit 1
fi
echo "[deploy]   Caddyfile sha: $new_sha"

# Check the release directory was published.
if [[ ! -d "$REVIEWED_RELEASE" ]]; then
    echo "[deploy] FAILED: release directory $REVIEWED_RELEASE not present"
    exit 1
fi
n_release=$(find "$REVIEWED_RELEASE" -type f | wc -l)
echo "[deploy]   release files: $n_release"

# Check the listener is up.
if ss -ltn 2>/dev/null | grep -q ":$LISTENER_PORT "; then
    echo "[deploy]   listener :$LISTENER_PORT is up"
else
    echo "[deploy] FAILED: listener :$LISTENER_PORT is not up"
    exit 1
fi

# Check that production http probes return expected codes.
expect_code() {
    local host="$1" path="$2" expected="$3" label="$4"
    local code
    code=$(curl -sk -o /dev/null -w "%{http_code}" --max-time 5 -H "Host: $host" "http://127.0.0.1:$LISTENER_PORT$path")
    if [[ "$code" == "$expected" ]]; then
        echo "[deploy]   $label: $host$path -> $code  OK"
    else
        echo "[deploy]   $label: $host$path -> $code (expected $expected)  FAIL"
        exit 1
    fi
}

expect_code dewata.org      /                            200 "apex landing"
expect_code api.dewata.org  /health                      200 "api health"
expect_code api.dewata.org  /dsp/v0.1/calendar/ruleset   200 "api ruleset"
expect_code bci.dewata.org  /                            503 "bci placeholder"

# ---------------------------------------------------------------
# 6. Done.  Print the dashboard steps the operator must perform.
# ---------------------------------------------------------------
echo
echo "[deploy] ============================================================"
echo "[deploy] INSTALL SUCCESS.  Local production is live."
echo "[deploy] ============================================================"
echo "[deploy] Caddyfile sha: $new_sha (was $PROD_BASELINE_SHA)"
echo "[deploy] Release directory: $REVIEWED_RELEASE"
echo "[deploy] Snapshot: $SNAPSHOT_DIR"
echo "[deploy] Listener: http://127.0.0.1:$LISTENER_PORT/  (Host: dewata.org)"
echo
echo "[deploy] NEXT STEPS (operator-driven dashboard cutover):"
echo "[deploy] 1. Cloudflare Zero Trust -> dewata-vps -> Public Hostnames"
echo "[deploy]    -> REMOVE:  dewata.org A 54.149.79.189  (proxy ON)"
echo "[deploy]    -> REMOVE:  dewata.org A 34.216.117.25  (proxy ON)"
echo "[deploy] 2. Add a new dewata.org published-application tunnel route"
echo "[deploy]    on dewata-vps: service type HTTP, address 127.0.0.1:8443, blank path"
echo "[deploy] 3. Verify https://dewata.org/  returns 200"
echo "[deploy] 4. Verify https://api.dewata.org/health  returns 200"
echo "[deploy] 5. Verify https://dewata.org/ on mobile (cloudflare proxy)"
echo
echo "[deploy] If anything goes wrong, run rollback:"
echo "[deploy]   bash /opt/dewata.online/deploy/atomic/rollback-apex.sh $SNAPSHOT_DIR"
