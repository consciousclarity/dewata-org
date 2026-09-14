#!/usr/bin/env bash
# =============================================================================
# apex-deploy.sh -- one-shot operator wrapper for the reviewed apex install.
# =============================================================================
#
# This wrapper is the operator's single entry point for installing the
# reviewed v0.1.0 apex bundle into /opt/dewata.online.
#
# Reviewed paths (immutable -- all scripts + manifests live here):
#
#     REVIEWED_ROOT=/opt/dw-phase2/deploy
#     apex-deploy.sh                <-- this script
#     atomic/install-apex-candidate.sh
#     atomic/rollback-apex.sh
#     atomic/RELEASES/v0.1.0-pre1.MANIFEST.txt
#     www/dewata-org/v0.1.0-pre1/   (reviewed source release tree)
#     caddy/Caddyfile.dewata.proposed  (reviewed candidate Caddyfile)
#
# Production destinations (writes go here):
#
#     /opt/dewata.online/deploy/caddy/Caddyfile.dewata
#     /opt/dewata.online/deploy/www/dewata-org/v0.1.0-pre1/
#     /opt/dewata.online/deploy/atomic/  (snapshot parent -- empty initially)
#
# The wrapper:
#   1. Verifies DEWATA_APPLY_PRODUCTION=1 (the installer's authorization).
#   2. Captures the production baseline sha256 RIGHT NOW and refuses if a
#      snapshot in the same parent was created in the last 60 seconds (the
#      now-implemented cooldown).
#   3. Records pre-flight sha256 of the wrapper, installer, rollback script,
#      candidate Caddyfile, reviewed manifest, and the reviewed release tree
#      counts + a sample hash.  These are required for audit.
#   4. Invokes the installer with every required DEWATA_* value explicit
#      (no default values -- missing values cause the installer to refuse).
#      The wrapper sets DEWATA_APPLY_PRODUCTION=1 explicitly; the installer's
#      production-path guard permits writes only against /opt/dewata.online/*
#      (or other known production prefixes).
#   5. Captures the installer's actual_snapshot_path= line from stdout so
#      the operator knows which snapshot to roll back to (rollback is
#      idempotent -- the same path can be rolled back multiple times).
#
# DEWATA_FORCE_REINSTALL=1: bypass the 60-second cooldown (operator escape
# hatch; documented in the bundle).
#
# Re-enterable wrappers and absolute paths:
#   The wrapper is the SAME reviewed script from the bundle -- copy it to
#   /opt/dewata.online ONLY if you want a shortcut there.  The default
#   invocation is `bash /opt/dw-phase2/deploy/apex-deploy.sh` from the
#   worktree directory.
#
# Do NOT put scripts under /opt/dewata.online/deploy/atomic/.  That
# directory is for INSTALLER-CREATED SNAPSHOTS ONLY.  Keep scripts in the
# reviewed source tree (the worktree).
# =============================================================================

set -Eeuo pipefail

# Standard binary locations.
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
BASH_XTRACEFD=""     # disabled by default; set to a file path for `-x` tracing.

# Disable inheritance of `set -e` into the installer sub-bash so the
# installer's failure can be captured in $installer_rc without killing the
# wrapper.  See "installer exit capture" below.
shopt -u inherit_errexit 2>/dev/null || true

# --------------------------------------------------------------------
# Required authorization flag (mutually exclusive with DEWATA_DISPOSABLE_MODE).
# --------------------------------------------------------------------
if [[ "${DEWATA_APPLY_PRODUCTION:-0}" != "1" ]]; then
    echo "FATAL: DEWATA_APPLY_PRODUCTION=1 must be set to authorize a production install." >&2
    echo "  this script is the only authorized entry point for /opt/dewata.online writes." >&2
    echo "  set DEWATA_APPLY_PRODUCTION=1 explicitly.  there is no default." >&2
    exit 2
fi

# --------------------------------------------------------------------
# Reviewed paths (immutable from the operator's checked-out worktree).
# The operator MUST verify these paths exist before running.
# Override via env vars (DEPLOY_*) only for a disposable mirror run;
# production runs use the defaults exactly.
# --------------------------------------------------------------------
REVIEWED_ROOT_DEFAULT="/opt/dw-phase2/deploy"

INSTALLER="${DEPLOY_INSTALLER:-$REVIEWED_ROOT_DEFAULT/atomic/install-apex-candidate.sh}"
ROLLBACK="${DEPLOY_ROLLBACK:-$REVIEWED_ROOT_DEFAULT/atomic/rollback-apex.sh}"
REVIEWED_MANIFEST="${DEPLOY_REVIEWED_MANIFEST:-$REVIEWED_ROOT_DEFAULT/atomic/RELEASES/v0.1.0-pre1.MANIFEST.txt}"
REVIEWED_RELEASE_SRC="${DEPLOY_REVIEWED_RELEASE_SRC:-$REVIEWED_ROOT_DEFAULT/www/dewata-org/v0.1.0-pre1}"
REVIEWED_CANDIDATE="${DEPLOY_REVIEWED_CANDIDATE:-$REVIEWED_ROOT_DEFAULT/caddy/Caddyfile.dewata.proposed}"

# Production destinations (writes go here -- these are PATH-PROTECTED).
PROD_CADDY_DEFAULT="/opt/dewata.online/deploy/caddy/Caddyfile.dewata"
PROD_RELEASE_DST_DEFAULT="/opt/dewata.online/deploy/www/dewata-org/v0.1.0-pre1"
SNAPSHOT_PARENT_DEFAULT="/opt/dewata.online/deploy/atomic"

PROD_CADDY="${DEPLOY_PROD_CADDY:-$PROD_CADDY_DEFAULT}"
PROD_RELEASE_DST="${DEPLOY_PROD_RELEASE_DST:-$PROD_RELEASE_DST_DEFAULT}"
SNAPSHOT_PARENT="${DEPLOY_SNAPSHOT_PARENT:-$SNAPSHOT_PARENT_DEFAULT}"

LISTENER_PORT="${DEPLOY_LISTENER_PORT:-8443}"
SERVICE="${DEPLOY_SERVICE:-dewata-caddy}"

# --------------------------------------------------------------------
# Pre-flight checks: every reviewed and production path must exist.
# --------------------------------------------------------------------
require_file() {
    local name="$1" path="$2"
    if [[ ! -e "$path" ]]; then
        echo "FATAL: $name missing at $path" >&2
        return 1
    fi
}
require_file "wrapper itself"                  "$0"
require_file "review-install script"           "$INSTALLER"
require_file "review-rollback script"          "$ROLLBACK"
require_file "reviewed candidate Caddyfile"     "$REVIEWED_CANDIDATE"
require_file "reviewed release source"          "$REVIEWED_RELEASE_SRC"
require_file "reviewed manifest"               "$REVIEWED_MANIFEST"
require_file "production Caddyfile destination" "$PROD_CADDY"

# Snapshot parent must be createable.
mkdir -p "$SNAPSHOT_PARENT" 2>/dev/null || {
    echo "FATAL: cannot create snapshot parent at $SNAPSHOT_PARENT" >&2
    exit 1
}

# --------------------------------------------------------------------
# Pre-flight hashes.  Print these BEFORE invoking the installer so the
# bundle records the exact bytes of every script and the candidate.
# --------------------------------------------------------------------
sha256_of_file() { sha256sum "$1" | cut -d' ' -f1; }
sha256_of_tree() {
    ( cd "$1" && find . -type f | sort | xargs -I{} sha256sum "{}" \
      | awk '{print $1}' | sort | sha256sum | cut -d' ' -f1)
}

echo "================================================================"
echo "[pre-flight] reviewed-path hashes"
echo "================================================================"
echo "wrapper itself        ($0):"
echo "  sha256: $(sha256_of_file "$0")"
echo "install script        ($INSTALLER):"
echo "  sha256: $(sha256_of_file "$INSTALLER")"
echo "rollback script       ($ROLLBACK):"
echo "  sha256: $(sha256_of_file "$ROLLBACK")"
echo "candidate Caddyfile   ($REVIEWED_CANDIDATE):"
echo "  sha256: $(sha256_of_file "$REVIEWED_CANDIDATE")"
echo "reviewed manifest     ($REVIEWED_MANIFEST):"
echo "  sha256: $(sha256_of_file "$REVIEWED_MANIFEST")"
echo "release tree          ($REVIEWED_RELEASE_SRC):"
n_release_files=$(find "$REVIEWED_RELEASE_SRC" -type f | wc -l)
release_tree_hash=$(sha256_of_tree "$REVIEWED_RELEASE_SRC")
echo "  file count: $n_release_files"
echo "  aggregate sha256: $release_tree_hash"

echo
echo "================================================================"
echo "[pre-flight] production baseline"
echo "================================================================"
echo "production Caddyfile  ($PROD_CADDY):"
echo "  sha256: $(sha256_of_file "$PROD_CADDY")"
PROD_BASELINE_SHA=$(sha256_of_file "$PROD_CADDY")

# --------------------------------------------------------------------
# Idempotence / cooldown.
# --------------------------------------------------------------------
if [[ "${DEWATA_FORCE_REINSTALL:-0}" != "1" ]]; then
    recent=$(find "$SNAPSHOT_PARENT" -mindepth 1 -maxdepth 1 \
            -type d -name "*-pre-apex" -mmin -1 -printf '%T@ %p\n' 2>/dev/null \
        | head -1 || true)
    if [[ -n "$recent" ]]; then
        recent_age=$(awk "{print \$1}" <<< "$recent")
        now=$(date +%s)
        age_seconds=$(awk -v n="$now" -v r="$recent_age" 'BEGIN{print n - r}')
        recent_path=$(awk '{print $2}' <<< "$recent")
        if awk -v a="$age_seconds" 'BEGIN{exit !(a < 60)}'; then
            echo "FATAL: idempotence / cooldown: a previous install ran ${age_seconds}s ago at $recent_path" >&2
            echo "  wait at least 60 seconds, or pass DEWATA_FORCE_REINSTALL=1 to bypass." >&2
            exit 3
        fi
    fi
else
    echo "[cooldown] DEWATA_FORCE_REINSTALL=1 -- cooldown bypassed."
fi

# --------------------------------------------------------------------
# Print the literal env-var values the installer will receive.
# --------------------------------------------------------------------
echo
echo "================================================================"
echo "[deploy] invoking: $INSTALLER"
echo "================================================================"
echo "        DEWATA_APPLY_PRODUCTION=1"
echo "        DEWATA_PROD_CADDY=$PROD_CADDY"
echo "        DEWATA_PROD_WWW=$(dirname "$PROD_RELEASE_DST")"
echo "        DEWATA_RELEASE_SRC=$REVIEWED_RELEASE_SRC"
echo "        DEWATA_RELEASE_DST=$PROD_RELEASE_DST"
echo "        DEWATA_CANDIDATE=$REVIEWED_CANDIDATE"
echo "        DEWATA_REVIEWED_MANIFEST=$REVIEWED_MANIFEST"
echo "        DEWATA_PROD_BASELINE_SHA=$PROD_BASELINE_SHA"
echo "        DEWATA_LISTENER_PORT=$LISTENER_PORT"
echo "        DEWATA_WORKTREE=$(dirname "$REVIEWED_ROOT_DEFAULT")"
echo "        DEWATA_SNAPSHOT_PARENT=$SNAPSHOT_PARENT"
echo "        DEWATA_CADDY_SERVICE=$SERVICE"

# --------------------------------------------------------------------
# Run the installer.  Capture stdout+stderr WITHOUT `set -e` killing us.
#
# `installer_rc` carries the installer's exit code.  The `|| rc=$?`
# handler ensures `set -e` doesn't propagate the installer's non-zero
# exit (the installer prints the snapshot path even on failure, so we
# want to capture and surface the full output).
# --------------------------------------------------------------------
unset POSIXLY_CORRECT
# Build the env -i block.  If DEWATA_DEPLOYER_TEST_MODE=1 is set,
# pass it through so the installer's production-path guard is bypassed.
TEST_MODE_FLAG=""
SHIM_FLAG=""
if [[ "${DEWATA_DEPLOYER_TEST_MODE:-0}" == "1" ]]; then
    TEST_MODE_FLAG="DEWATA_DEPLOYER_TEST_MODE=1"
    # In test mode, redirect every systemctl call to the disposable shim
    # under tests/ so the install cannot accidentally restart the real
    # production service.
    DEWATA_DEPLOYER_SHIM="$REVIEWED_ROOT_DEFAULT/../tests/disposable-systemctl.sh"
    DEWATA_DEPLOYER_SHIM_LOG="$REVIEWED_ROOT_DEFAULT/../tests/disposable-systemctl.log"
    DEWATA_DEPLOYER_SHIM_PIDFILE="/tmp/deploy-mirror-tests-caddy.pid"
    DEWATA_DEPLOYER_SHIM_ACTIVE="/tmp/deploy-mirror-tests-caddy.active"
    rm -f "$DEWATA_DEPLOYER_SHIM_PIDFILE" "$DEWATA_DEPLOYER_SHIM_ACTIVE" "$DEWATA_DEPLOYER_SHIM_LOG"
    SHIM_FLAG="DEWATA_SYSTEMCTL_CMD=$DEWATA_DEPLOYER_SHIM \
              DEWATA_DISPOSABLE_SYSTEMCTL_LOG=$DEWATA_DEPLOYER_SHIM_LOG \
              DEWATA_DISPOSABLE_SYSTEMCTL_PIDFILE=$DEWATA_DEPLOYER_SHIM_PIDFILE \
              DEWATA_DISPOSABLE_SYSTEMCTL_ACTIVE=$DEWATA_DEPLOYER_SHIM_ACTIVE \
              DEWATA_PROBE_LISTENER=0"
fi
set +e
output=$(
    env -i \
        PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
        DEWATA_APPLY_PRODUCTION=1 \
        DEWATA_PROD_CADDY="$PROD_CADDY" \
        DEWATA_PROD_WWW="$(dirname "$PROD_RELEASE_DST")" \
        DEWATA_RELEASE_SRC="$REVIEWED_RELEASE_SRC" \
        DEWATA_RELEASE_DST="$PROD_RELEASE_DST" \
        DEWATA_CANDIDATE="$REVIEWED_CANDIDATE" \
        DEWATA_REVIEWED_MANIFEST="$REVIEWED_MANIFEST" \
        DEWATA_PROD_BASELINE_SHA="$PROD_BASELINE_SHA" \
        DEWATA_LISTENER_PORT="$LISTENER_PORT" \
        DEWATA_WORKTREE="$(dirname "$REVIEWED_ROOT_DEFAULT")" \
        DEWATA_SNAPSHOT_PARENT="$SNAPSHOT_PARENT" \
        DEWATA_CADDY_SERVICE="$SERVICE" \
        $TEST_MODE_FLAG \
        $SHIM_FLAG \
        bash "$INSTALLER" 2>&1
)
installer_rc=$?
set -e

echo
echo "================================================================"
echo "[deploy] installer output (full)"
echo "================================================================"
echo "$output"

# Capture the actual_snapshot_path line.
# It's printed by the installer on success and by do_restore on failure.
actual_snapshot=$(grep -E '^[[:space:]]*actual_snapshot_path=' <<< "$output" \
                | tail -1 \
                | sed 's/^[[:space:]]*actual_snapshot_path=//')
if [[ -z "$actual_snapshot" ]]; then
    echo
    echo "[deploy] FATAL: installer did not print actual_snapshot_path=" >&2
    echo "[deploy] rc=$installer_rc -- this is the installer's actual exit code; printed for the audit trail." >&2
    exit 6
fi
echo
echo "[deploy] installer reports: actual_snapshot_path=$actual_snapshot"

if (( installer_rc != 0 )); then
    echo
    echo "[deploy] FATAL: installer rc=$installer_rc -- fail closed." >&2
    echo "[deploy] do_restore may have already moved the prior release back into place," >&2
    echo "[deploy] or (first-install failure) may have moved the freshly-published release to" >&2
    echo "[deploy] $PROD_RELEASE_DST.rejected.*" >&2
    exit "$installer_rc"
fi
echo "[deploy] installer rc=0 -- install succeeded."

# --------------------------------------------------------------------
# Dashboard cutover steps (Cloudflare -- NOT executed by this script).
# --------------------------------------------------------------------
echo
echo "================================================================"
echo "[deploy] dashboard cutover steps (operator runs these manually)"
echo "================================================================"
echo "1. remove the apex A records at the Cloudflare dashboard:"
echo "     - host @, value 54.149.79.189, type A, TTL auto, proxied (delete)"
echo "     - host @, value 34.216.117.25,  type A, TTL auto, proxied (delete)"
echo "2. create the apex published-application tunnel route:"
echo "     - on the existing dewata-vps cloudflared tunnel, add ingress:"
echo "       hostname : dewata.org"
echo "       service : http://localhost:$LISTENER_PORT"
echo "   (or via published-application CNAME: @ -> dewata-vps.cfargotunnel.com)"
echo "3. verify public:"
echo "     - curl -4 -I https://dewata.org/             # expect 200"
echo "     - curl -4 -I https://api.dewata.org/health   # expect 200"
echo
echo "================================================================"
echo "[deploy] rollback reference (operator)"
echo "================================================================"
echo "    DEWATA_APPLY_PRODUCTION=1 \\"
echo "        DEWATA_PROD_CADDY=$PROD_CADDY \\"
echo "        DEWATA_LISTENER_PORT=$LISTENER_PORT \\"
echo "        DEWATA_WORKTREE=$(dirname "$REVIEWED_ROOT_DEFAULT") \\"
echo "        DEWATA_CADDY_SERVICE=$SERVICE \\"
echo "        bash $ROLLBACK \\"
echo "        $actual_snapshot"
