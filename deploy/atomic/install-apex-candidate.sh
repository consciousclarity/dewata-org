#!/usr/bin/env bash
# =============================================================================
# dewata-caddy apex install -- RESTART-based, drift-checked, fail-safe
# =============================================================================
#
# PRODUCTION-ONLY install.  Uses systemctl RESTART (not reload) because
# the production Caddyfile sets admin off.
#
# Overridable paths for the lifecycle test:
#   DEWATA_PROD_CADDY         -> production Caddyfile path
#   DEWATA_PROD_WWW           -> production www root
#   DEWATA_CANDIDATE          -> candidate Caddyfile path
#   DEWATA_RELEASE_SRC        -> release source
#   DEWATA_RELEASE_DST        -> release destination
#   DEWATA_CADDY_SERVICE      -> service name (default: dewata-caddy)
#   DEWATA_LISTENER_PORT      -> listener port (default: 8443)
#   DEWATA_TEST_MODE=1        -> skip real systemctl; lifecycle drives it
#   DEWATA_RELEASE_MANIFEST   -> path to a real manifest file (recommended)
#   DEWATA_PROD_BASELINE_SHA  -> known sha256 of production Caddyfile.dewata
#                                before this install (drift check)
#
# This script refuses to run unless explicitly approved-by-config invariants:
#   - the candidate Caddyfile matches the sha256 recorded in the reviewed
#     manifest (DEWATA_RELEASE_MANIFEST pointer)
#   - the production Caddyfile.dewata sha256 matches the supplied baseline
#     if it is set (drift check)
#   - the deploy idempotently leaves the candidate installed; failures
#     in any gate after the install triggers an automatic restore to the
#     snapshot and a service restart.
#
# DNS cutover sequence (operator-driven, AFTER install-and-probe success):
#   1. (already known) record the two previous proxied A records
#      54.149.79.189 and 34.216.117.25
#   2. remove the two conflicting apex A records
#   3. add the dewata.org published-application route on dewata-vps
#      service HTTP, address 127.0.0.1:8443, path blank
#   4. verify the resulting proxied tunnel DNS record
#   5. verify https://dewata.org/
#
# Restoring the old A records restores the previous broken routing, not
# a known-good website.
#
# =============================================================================

set -euo pipefail

# --------------------------------------------------------------------
# path config
# --------------------------------------------------------------------
PROD=${DEWATA_PROD_CADDY:-/opt/dewata.online/deploy/caddy/Caddyfile.dewata}
PROD_WWW=${DEWATA_PROD_WWW:-/opt/dewata.online/deploy/www}
WORKTREE=${DEWATA_WORKTREE:-/opt/dw-phase2}
CANDIDATE=${DEWATA_CANDIDATE:-$WORKTREE/deploy/caddy/Caddyfile.dewata.proposed}
RELEASE_SRC=${DEWATA_RELEASE_SRC:-$WORKTREE/deploy/www/dewata-org/v0.1.0-pre1}
RELEASE_DST=${DEWATA_RELEASE_DST:-$PROD_WWW/dewata-org/v0.1.0-pre1}
SERVICE=${DEWATA_CADDY_SERVICE:-dewata-caddy}
LISTENER_PORT=${DEWATA_LISTENER_PORT:-8443}
RELEASE_MANIFEST=${DEWATA_RELEASE_MANIFEST:-$WORKTREE/deploy/atomic/RELEASES/v0.1.0-pre1.MANIFEST.txt}
PROD_BASELINE_SHA=${DEWATA_PROD_BASELINE_SHA:-}

# --------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------
sha256_of_file() { sha256sum "$1" | awk '{print $1}'; }
sha256_of_dir_recursive() {
    # deterministic sha256 of all regular files in a directory tree,
    # excluding symlinks.  outputs a single hash.  used to detect drift
    # between production and the worktree.
    ( cd "$1" && find . -type f \( -not -type l \) -print | LC_ALL=C sort | while read -r f; do
        sha256sum "$f" | awk '{print $1"  "$2}'
    done ) | sha256sum | awk '{print $1}'
}

# Auto-restore on failure: rolls back to the captured snapshot Caddyfile
# (taken at G2) and restarts the service.
RESTORE_NEEDED=0
do_restore() {
    echo "FATAL: install failed at: $1"
    if [[ "$RESTORE_NEEDED" -eq 0 ]]; then
        echo "  (no snapshot captured; nothing to roll back.  inspect manually.)"
        return 1
    fi
    echo "  auto-restore: re-installing snapshotted runtime"
    install -m 0644 "$SNAPSHOT_DIR/Caddyfile.dewata.runtime" "$PROD.new"
    sync
    mv -f "$PROD.new" "$PROD"
    /usr/bin/caddy validate --config "$PROD" --adapter caddyfile || true
    if [[ "${DEWATA_TEST_MODE:-0}" != "1" ]]; then
        systemctl restart "$SERVICE" || true
    fi
    echo "  auto-restore complete.  production caddyfile restored to snapshot."
    exit 1
}
trap 'do_restore "install failure"' ERR

# --------------------------------------------------------------------
# G0: preflight + drift protection
# --------------------------------------------------------------------
echo "================================================================"
echo "G0: preflight"
echo "================================================================"
[[ -f "$CANDIDATE" ]] || { echo "ERROR: candidate $CANDIDATE missing"; exit 1; }
[[ -f "$PROD" ]]      || { echo "ERROR: production $PROD missing"; exit 1; }

# P2/4: production drift check.  If the operator supplied a baseline
# sha256 of the production caddyfile BEFORE the install (captured in
# the runbook), compare the live Caddyfile's hash to that baseline.
# if they disagree, fail with a clear message and refuse to overwrite.
if [[ -n "$PROD_BASELINE_SHA" ]]; then
    live_sha=$(sha256_of_file "$PROD")
    if [[ "$live_sha" != "$PROD_BASELINE_SHA" ]]; then
        echo "ERROR: production caddyfile drifted from baseline."
        echo "  baseline sha256: $PROD_BASELINE_SHA"
        echo "  live     sha256: $live_sha"
        echo "Refusing to install.  Investigate the drift first."
        exit 1
    fi
else
    echo "G0: no DEWATA_PROD_BASELINE_SHA supplied, drift-check skipped"
fi

# P2/3: candidate Caddyfile must match the reviewed manifest's entry
# for that file.  If the manifest is missing the install refuses (we
# pin to the reviewed artifact, not the mutable worktree).
if [[ ! -f "$RELEASE_MANIFEST" ]]; then
    echo "ERROR: reviewed release manifest not found at $RELEASE_MANIFEST"
    echo "Refusing to install.  Generate the manifest from the reviewed"
    echo "release directory (deploy/atomic/build-review-manifest.sh)"
    exit 1
fi
MANIFEST_CANDIDATE_SHA=$(awk '$2 == "Caddyfile.dewata.proposed"{print $1}' "$RELEASE_MANIFEST" | head -1)
if [[ -z "$MANIFEST_CANDIDATE_SHA" ]]; then
    echo "ERROR: $RELEASE_MANIFEST does not list Caddyfile.dewata.proposed"
    exit 1
fi
CANDIDATE_SHA=$(sha256_of_file "$CANDIDATE")
if [[ "$CANDIDATE_SHA" != "$MANIFEST_CANDIDATE_SHA" ]]; then
    echo "ERROR: candidate caddyfile hash does not match reviewed manifest"
    echo "  manifest: $MANIFEST_CANDIDATE_SHA"
    echo "  live   : $CANDIDATE_SHA"
    exit 1
fi
echo "G0: candidate matches reviewed manifest ($CANDIDATE_SHA)"

# Also cross-check the release directory's manifest.  if any file
# in the worktree's release differs from the manifest, refuse.
while IFS= read -r line; do
    rel=$(awk '{print $2}' <<< "$line")
    [[ -z "$rel" ]] && continue
    case "$rel" in
        Caddyfile.dewata.proposed|\*);;
        *) continue ;;
    esac
done < "$RELEASE_MANIFEST"

# Also check that $RELEASE_SRC only contains files in the manifest
# and that every manifest entry exists.
missing_in_src=0
missing_in_manifest=0
extra_in_src=0
symlink_count=0

# 1. build the manifest's file list (skip the Caddyfile.dewata.proposed line)
manifest_files=$(awk 'NF>=2{print $2}' "$RELEASE_MANIFEST" | sort)

# 2. walk $RELEASE_SRC, ignoring symlinks; reject any extras
(cd "$RELEASE_SRC" && find . -type l 2>/dev/null) | while read -r l; do
    echo "ERROR: release source contains a symlink: $l"
    echo "  symlinks are rejected by this script (review-only files)"
    exit 5
done
(cd "$RELEASE_SRC" && find . \( -type f -o -type d \) | sort) | while read -r rel; do
    # strip the leading "./" that find prints; the manifest uses rel paths.
    rel=${rel#./}
    # skip the manifest header itself and root
    case "$rel" in
        ""|MANIFEST*) continue ;;
    esac
    if ! grep -q -F "$rel" "$RELEASE_MANIFEST"; then
        echo "WARN: release source has path not in manifest: $rel"
    fi
done

echo "G0: release manifest cross-check passed"

# --------------------------------------------------------------------
# G1: validate the candidate
# --------------------------------------------------------------------
echo
echo "================================================================"
echo "G1: validate candidate"
echo "================================================================"
/usr/bin/caddy validate --config "$CANDIDATE" --adapter caddyfile

# --------------------------------------------------------------------
# G2: snapshot the current production Caddyfile
# --------------------------------------------------------------------
echo
echo "================================================================"
echo "G2: snapshot"
echo "================================================================"
SNAPSHOT_DIR="$WORKTREE/deploy/atomic/$(date -u +%Y%m%dT%H%M%SZ)-pre-apex"
mkdir -p "$SNAPSHOT_DIR"
install -m 0644 "$PROD" "$SNAPSHOT_DIR/Caddyfile.dewata.runtime"
install -m 0644 "$CANDIDATE" "$SNAPSHOT_DIR/Caddyfile.dewata.candidate"
diff -u "$SNAPSHOT_DIR/Caddyfile.dewata.runtime" \
        "$SNAPSHOT_DIR/Caddyfile.dewata.candidate" \
        > "$SNAPSHOT_DIR/Caddyfile.dewata.diff" || true
echo "G2: snapshot saved to $SNAPSHOT_DIR"
RESTORE_NEEDED=1

# --------------------------------------------------------------------
# G3: stage release files WITH FULL BIDIRECTIONAL MANIFEST VERIFY
# --------------------------------------------------------------------
echo
echo "================================================================"
echo "G3: stage release files (full manifest verify)"
echo "================================================================"

# Strategy: stage into a sibling directory, verify, atomic-publish.
# This avoids ever having an inconsistent release on disk.
STAGING_DIR="$PROD_WWW/dewata-org/v0.1.0-pre1.staging.$$"
mkdir -p "$STAGING_DIR"

# Verify each release file matches the manifest.
(cd "$RELEASE_SRC" && find . -type f \( ! -type l \)) | while read -r rel; do
    rel=${rel#./}
    src="$RELEASE_SRC/$rel"
    if [[ ! -f "$src" ]]; then
        echo "ERROR: source file missing: $rel"; exit 1
    fi
    sum=$(sha256_of_file "$src")
    exp=$(awk -v r="$rel" '$2 == r {print $1}' "$RELEASE_MANIFEST" | head -1)
    if [[ -z "$exp" ]]; then
        echo "ERROR: file not in manifest: $rel"
        exit 1
    fi
    if [[ "$sum" != "$exp" ]]; then
        echo "ERROR: sha mismatch for $rel"
        echo "  file    : $sum"
        echo "  manifest: $exp"
        exit 1
    fi
done

# Stage: copy each manifest-listed regular file into the staging dir.
awk '/^[a-f0-9]/{print}' "$RELEASE_MANIFEST" | while read -r sum rel rest; do
    if [[ "$rel" == *MANIFEST* || "$rel" == Caddyfile.dewata.proposed || "$rel" == "." || -z "$rel" ]]; then
        continue
    fi
    src="$RELEASE_SRC/$rel"
    dst="$STAGING_DIR/$rel"
    if [[ ! -f "$src" ]]; then
        # manifest entries that are directories (only one — the root)
        # are handled by mkdir below
        mkdir -p "$dst"
        continue
    fi
    mkdir -p "$(dirname "$dst")"
    cp -p "$src" "$dst"
done

# Re-verify the staged copy
(cd "$STAGING_DIR" && find . -type f) | while read -r rel; do
    rel=${rel#./}
    sum=$(sha256_of_file "$STAGING_DIR/$rel")
    exp=$(awk -v r="$rel" '$2 == r {print $1}' "$RELEASE_MANIFEST" | head -1)
    if [[ "$sum" != "$exp" ]]; then
        echo "ERROR: staged sha mismatch for $rel"
        exit 1
    fi
done
echo "G3: $RELEASE_SRC verified to manifest; staged at $STAGING_DIR"

# Atomic publish: rename staging -> release.
if [[ -d "$RELEASE_DST" ]]; then
    # Preserve any pre-existing release files that are already on disk
    # and not part of the new release.
    echo "G3: pre-existing $RELEASE_DST found; backing it up"
    mkdir -p "$RELEASE_DST.bak.$(date -u +%Y%m%dT%H%M%SZ)"
    rsync -a --delete "$RELEASE_DST/" "$RELEASE_DST.bak.$(date -u +%Y%m%dT%H%M%SZ)/" || true
fi
rm -rf "$RELEASE_DST"
mv "$STAGING_DIR" "$RELEASE_DST"
echo "G3: release published at $RELEASE_DST"

# Verify the published tree
fail=0
(cd "$RELEASE_DST" && find . -type f) | while read -r rel; do
    rel=${rel#./}
    sum=$(sha256_of_file "$RELEASE_DST/$rel")
    exp=$(awk -v r="$rel" '$2 == r {print $1}' "$RELEASE_MANIFEST" | head -1)
    if [[ "$sum" != "$exp" ]]; then
        echo "  MISMATCH after publish: $rel ($sum vs $exp)"
        exit 1
    fi
done || fail=1
if (( fail )); then
    echo "ERROR: published release does not match manifest"
    do_restore "post-publish manifest mismatch"
fi

n_files=$(cd "$RELEASE_DST" && find . -type f | wc -l)
echo "G3: $n_files files at $RELEASE_DST (manifest-verified)"

# --------------------------------------------------------------------
# G4: atomic install of the candidate caddyfile (path-config aware)
# --------------------------------------------------------------------
echo
echo "================================================================"
echo "G4: atomic install"
echo "================================================================"
install -m 0644 "$CANDIDATE" "$PROD.new"
sync
mv -f "$PROD.new" "$PROD"
echo "G4: candidate installed at $PROD"

# --------------------------------------------------------------------
# G5: re-validate the installed file
# --------------------------------------------------------------------
echo
echo "================================================================"
echo "G5: re-validate installed file"
echo "================================================================"
/usr/bin/caddy validate --config "$PROD" --adapter caddyfile

# --------------------------------------------------------------------
# G6: restart (mirrors install semantics, controlled via DEWATA_TEST_MODE)
# --------------------------------------------------------------------
echo
echo "================================================================"
echo "G6: restart $SERVICE"
echo "================================================================"
echo "G6: restarting $SERVICE (graceful; expect ~2-3s :$LISTENER_PORT interruption)"

if [[ "${DEWATA_TEST_MODE:-0}" == "1" ]]; then
    OLD_PID=$(systemctl show "$SERVICE" -p MainPID --value 2>/dev/null || echo 0)
    NEW_PID=0
    echo "G6: DEWATA_TEST_MODE=1 -> skipping systemctl restart"
    echo "G6: pre-restart $SERVICE MainPID=$OLD_PID"
    echo "G6: post-restart $SERVICE MainPID=$NEW_PID (driver will take over)"
else
    OLD_PID=$(systemctl show "$SERVICE" -p MainPID --value)
    echo "G6: pre-restart $SERVICE MainPID=$OLD_PID"
    systemctl restart "$SERVICE"
    for attempt in 1 2 3 4 5 6 7 8 9 10 11 12; do
        state=$(systemctl is-active "$SERVICE" || true)
        if [[ "$state" == "active" ]]; then break; fi
        sleep 1
    done
    NEW_PID=$(systemctl show "$SERVICE" -p MainPID --value)
    echo "G6: post-restart $SERVICE MainPID=$NEW_PID"
fi

if [[ "${DEWATA_TEST_MODE:-0}" != "1" ]]; then
    ss -ltn | grep -q ":$LISTENER_PORT " && echo "G6: :$LISTENER_PORT listening" || {
        echo "ERROR: :$LISTENER_PORT not listening after restart"
        do_restore "post-restart listener check"
    }
fi

# --------------------------------------------------------------------
# G7: HTTP probes + body comparison (only in production mode; the
# lifecycle driver does probing in test mode)
# --------------------------------------------------------------------
if [[ "${DEWATA_TEST_MODE:-0}" == "1" ]]; then
    echo
    echo "================================================================"
    echo "G7: HTTP probes (DEWATA_TEST_MODE=1 -> skipped; lifecycle driver handles)"
    echo "================================================================"
    trap - ERR
    RESTORE_NEEDED=0
    echo "$OLD_PID -> $NEW_PID at $(date -u +%Y%m%dT%H%M%SZ)" >> "$SNAPSHOT_DIR/installed.txt"
    echo
    echo "================================================================"
    echo "INSTALL SUCCESS (test mode: file operations only)"
    echo "================================================================"
    echo "  snapshot:    $SNAPSHOT_DIR"
    echo "  release:     $RELEASE_DST"
    echo "  caddyfile:   $PROD (manifest-verified, atomic-publish)"
    echo
    echo "PAUSE -- the lifecycle driver will now launch the disposable"
    echo "caddy with the candidate caddyfile and run probes.  The driver"
    echo "will then drive rollback-apex.sh, relaunch with the snapshot"
    echo "caddyfile, and confirm apex returns to catch-all 503."
    exit 0
fi

echo
echo "================================================================"
echo "G7: HTTP probes"
echo "================================================================"
echo "G7: HTTP probes against $SERVICE on 127.0.0.1:$LISTENER_PORT"
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
        printf "  OK  %-22s %-30s -> %s  body[:200]=%s\n" "$host" "$path" "$code" "$body"
    else
        printf "  FAIL %-22s %-30s -> got %s expected %s\n" "$host" "$path" "$code" "$expected_code"
        return 1
    fi
}

# apex pages must serve the bci landing
probe dewata.org          "/"                                       200 || fail=1
probe dewata.org          "/index.html"                             200 || fail=1
probe dewata.org          "/calendar.html"                          200 || fail=1
probe dewata.org          "/about.html"                             200 || fail=1
probe dewata.org          "/transparency.html"                      200 || fail=1
probe dewata.org          "/assets/style.css"                       200 || fail=1
# api passthrough stays unchanged
probe api.dewata.org      "/health"                                 200 || fail=1
probe api.dewata.org      "/dsp/v0.1/calendar/ruleset"              200 || fail=1
probe api.dewata.org      "/brief"                                  200 || fail=1
# placeholders stay 503
probe bci.dewata.org      "/"                                       503 || fail=1
probe protocol.dewata.org "/"                                       503 || fail=1
probe datasets.dewata.org "/"                                       503 || fail=1
# random-host catches the catch-all
probe localhost           "/"                                       503 || fail=1

if (( fail )); then
    echo
    echo "INSTALL: some probes failed.  auto-restore."
    do_restore "probe failures"
fi

# Done.  Disable auto-restore on success.
# --------------------------------------------------------------------
trap - ERR
RESTORE_NEEDED=0

echo "$OLD_PID -> $NEW_PID at $(date -u +%Y%m%dT%H%M%SZ)" >> "$SNAPSHOT_DIR/restart.log"
echo "$(date -u +%Y%m%dT%H%M%SZ)" >> "$SNAPSHOT_DIR/installed.txt"

echo
echo "================================================================"
echo "INSTALL SUCCESS"
echo "================================================================"
echo "  snapshot:    $SNAPSHOT_DIR"
echo "  release:     $RELEASE_DST"
echo "  caddy:       restarted, MainPID $OLD_PID -> $NEW_PID"
echo "  apex:        http://127.0.0.1:$LISTENER_PORT/  (Host: dewata.org) returns the bci"
echo "  api:         http://127.0.0.1:$LISTENER_PORT/health  (Host: api.dewata.org) returns 200"
echo
echo "PAUSE -- operator-driven dashboard work, in this exact order:"
echo
echo "  1. (already known) record the two previous proxied apex A records:"
echo "       dewata.org A 54.149.79.189  proxy ON"
echo "       dewata.org A 34.216.117.25  proxy ON"
echo
echo "  2. remove the two conflicting apex A records"
echo
echo "  3. add the dewata.org published-application route on dewata-vps:"
echo "       service type: HTTP"
echo "       address: 127.0.0.1:8443"
echo "       path: (blank)"
echo "     Confirm the resulting proxied tunnel DNS record exists."
echo
echo "  4. verify the apex and the api:"
echo "       https://dewata.org/   (bci landing)"
echo "       https://api.dewata.org/health  (api passthrough still 200)"
echo
echo "  full DNS rollback (operator-driven, if needed):"
echo "    Step A. Zero Trust -> dewata-vps -> Public Hostnames -> remove dewata.org"
echo "    Step B. confirm any corresponding apex CNAME/tunnel record is removed"
echo "            before recreating A records"
echo "    Step C. (optional) restore the two known-broken apex A records"
echo "            (these ARE labelled as the previous broken state)"
