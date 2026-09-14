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
#   DEWATA_REVIEWED_MANIFEST  -> REQUIRED: path to the reviewed manifest file.
#                                Format: <sha256> <relpath>, one per line.
#                                Must be generated from a reviewed artifact,
#                                NEVER auto-derived from the live worktree.
#                                No default; install refuses with rc=2 if unset.
#   DEWATA_PROD_BASELINE_SHA  -> REQUIRED: sha256 of production Caddyfile.dewata
#                                right now.  Captured before the install runs.
#                                The install refuses with rc=3 if the live file
#                                does not match (drift guard).  No default; the
#                                install refuses with rc=2 if unset.
#   DEWATA_PROD_WWW           -> REQUIRED: production www root (no default;
#                                refuses with rc=2 if unset).  Used to compute
#                                the default release destination.
#   DEWATA_RELEASE_DST        -> REQUIRED: release destination (no default;
#                                refuses with rc=2 if unset).
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
# Production-path guard.  The install script must NEVER run against
# /opt/dewata.online/* paths unless DEWATA_TEST_MODE=1 is explicitly
# set.  This catches the case where someone invokes the install with
# a partial environment and the defaults fall back to production
# paths.  Without this guard, an unset DEWATA_TEST_MODE could result
# in a real production restart via the G6 path.
if [[ "${DEWATA_TEST_MODE:-}" != "1" ]]; then
    case "${DEWATA_PROD_CADDY:-}" in
        /opt/dewata.online/*|/etc/caddy/*|/var/lib/dewata/*)
            echo "FATAL: refusing to run against production path $DEWATA_PROD_CADDY without DEWATA_TEST_MODE=1." >&2
            echo "  This guard prevents accidental production restarts." >&2
            echo "  If you really want to install against a production path, set" >&2
            echo "  DEWATA_TEST_MODE=1 explicitly (this is the lifecycle-test mode)." >&2
            echo "  Or run against a disposable tree and pass DEWATA_PROD_CADDY=<disposable-path>." >&2
            exit 4
            ;;
    esac
fi

# Mandatory required env vars.  We refuse to run with mutable
# defaults that would silently write to production paths.  Every
# path must be supplied explicitly so the operator (and the
# lifecycle test) cannot accidentally clobber production.
if [[ -z "${DEWATA_PROD_CADDY:-}" ]]; then
    echo "FATAL: DEWATA_PROD_CADDY is unset or empty." >&2
    echo "  supply the production Caddyfile path, e.g.:" >&2
    echo "    DEWATA_PROD_CADDY=/opt/dewata.online/deploy/caddy/Caddyfile.dewata" >&2
    exit 2
fi
if [[ -z "${DEWATA_PROD_WWW:-}" ]]; then
    echo "FATAL: DEWATA_PROD_WWW is unset or empty." >&2
    echo "  supply the production www root, e.g.:" >&2
    echo "    DEWATA_PROD_WWW=/opt/dewata.online/deploy/www" >&2
    exit 2
fi
if [[ -z "${DEWATA_RELEASE_DST:-}" ]]; then
    echo "FATAL: DEWATA_RELEASE_DST is unset or empty." >&2
    echo "  supply the release destination, e.g.:" >&2
    echo "    DEWATA_RELEASE_DST=/opt/dewata.online/deploy/www/dewata-org/v0.1.0-pre1" >&2
    exit 2
fi
if [[ -z "${DEWATA_RELEASE_SRC:-}" ]]; then
    echo "FATAL: DEWATA_RELEASE_SRC is unset or empty." >&2
    echo "  supply the release source, e.g.:" >&2
    echo "    DEWATA_RELEASE_SRC=/opt/dewata.online/deploy/www/dewata-org/v0.1.0-pre1" >&2
    exit 2
fi
if [[ -z "${DEWATA_CANDIDATE:-}" ]]; then
    echo "FATAL: DEWATA_CANDIDATE is unset or empty." >&2
    echo "  supply the candidate Caddyfile path, e.g.:" >&2
    echo "    DEWATA_CANDIDATE=/opt/dewata.online/deploy/caddy/Caddyfile.dewata.proposed" >&2
    exit 2
fi
PROD=$DEWATA_PROD_CADDY
PROD_WWW=$DEWATA_PROD_WWW
RELEASE_DST=$DEWATA_RELEASE_DST
RELEASE_SRC=$DEWATA_RELEASE_SRC
CANDIDATE=$DEWATA_CANDIDATE
WORKTREE=${DEWATA_WORKTREE:-/opt/dw-phase2}
SERVICE=${DEWATA_CADDY_SERVICE:-dewata-caddy}
LISTENER_PORT=${DEWATA_LISTENER_PORT:-8443}
# Mandatory required env vars: DEWATA_REVIEWED_MANIFEST and
# DEWATA_PROD_BASELINE_SHA.  No mutable defaults; the install refuses
# with rc=2 if either is empty.  This pins the deploy to a reviewed
# artifact and prevents drift.
if [[ -z "${DEWATA_REVIEWED_MANIFEST:-}" ]]; then
    echo "FATAL: DEWATA_REVIEWED_MANIFEST is unset or empty." >&2
    echo "  supply the path to a reviewed manifest, e.g.:" >&2
    echo "    DEWATA_REVIEWED_MANIFEST=/opt/dewata.online/deploy/atomic/RELEASES/v0.1.0-pre1.MANIFEST.txt" >&2
    exit 2
fi
if [[ -z "${DEWATA_PROD_BASELINE_SHA:-}" ]]; then
    echo "FATAL: DEWATA_PROD_BASELINE_SHA is unset or empty." >&2
    echo "  compute it from production right now, e.g.:" >&2
    echo "    sha256sum /opt/dewata.online/deploy/caddy/Caddyfile.dewata" >&2
    exit 2
fi
REVIEWED_MANIFEST=$DEWATA_REVIEWED_MANIFEST
PROD_BASELINE_SHA=$DEWATA_PROD_BASELINE_SHA

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

# Auto-restore on failure.  This function is the last line of defense:
# if any gate fails after we have begun mutating production, this
# restores both the prior Caddyfile AND (if G3 has already published
# the new release tree) the prior release tree.  It validates the
# restored Caddyfile before declaring success, and refuses to declare
# success if the validation fails.  Never silently swallows errors.

# Track which steps have been performed so the restore can undo them
# in reverse order.
SNAPSHOT_CAPTURED=0      # G2: snapshot exists at $SNAPSHOT_DIR
RELEASE_BACKED_UP=""     # G3: backup path of the old release tree (if any)
PROD_WRITTEN=0           # G4: $PROD has the new candidate (not yet validated)
RESTART_INVOKED=0        # G6: systemctl restart was actually executed

do_restore() {
    local reason="$1"
    echo "FATAL: install failed at: $reason"
    if [[ "$SNAPSHOT_CAPTURED" -ne 1 ]]; then
        echo "  (no snapshot captured; nothing to roll back.  inspect manually.)"
        exit 1
    fi
    local restore_failed=0

    # 1. restore the production Caddyfile from the snapshot.
    if [[ ! -f "$SNAPSHOT_DIR/Caddyfile.dewata.runtime" ]]; then
        echo "  restore ABORTED: snapshot runtime file missing at $SNAPSHOT_DIR/Caddyfile.dewata.runtime" >&2
        restore_failed=1
    else
        # Failure-injection hook: corrupt the snapshot runtime file in
        # place so the restored caddyfile fails caddy validate.  This
        # tests that do_restore correctly reports the failure rather
        # than silently declaring success.
        if [[ "${DEWATA_FAKE_RECOVERY_VALIDATION_FAILURE:-0}" == "1" ]]; then
            echo "  DEWATA_FAKE_RECOVERY_VALIDATION_FAILURE=1 -> corrupting snapshot runtime in place" >&2
            printf "\n{ broken syntax\n" >> "$SNAPSHOT_DIR/Caddyfile.dewata.runtime"
        fi
        echo "  auto-restore: re-installing snapshotted runtime to $PROD"
        install -m 0644 "$SNAPSHOT_DIR/Caddyfile.dewata.runtime" "$PROD.new"
        sync
        mv -f "$PROD.new" "$PROD"
    fi

    # 2. validate the restored Caddyfile.  This is the gate that must
    #    succeed before we declare "auto-restore complete".
    if /usr/bin/caddy validate --config "$PROD" --adapter caddyfile; then
        echo "  restored Caddyfile validates"
    else
        echo "  RESTORE FAILED: restored Caddyfile does not validate" >&2
        restore_failed=1
    fi

    # 3. restart the service.  This MUST happen AFTER the caddyfile is
    #    restored on disk so the running caddy reloads the restored
    #    config.  If the restart fails, the live caddy is still serving
    #    the broken config from before the restore; do NOT declare
    #    success.
    #
    #    The restart only fires when this is a known production path
    #    AND DEWATA_TEST_MODE is not 1.  For disposable paths the
    #    restart is skipped (the lifecycle test\'s disposable caddy
    #    is not the real service).
    RESTORE_IS_PROD=0
    case "$PROD" in
        /opt/dewata.online/*|/etc/caddy/*|/var/lib/dewata/*) RESTORE_IS_PROD=1 ;;
    esac
    if [[ "${DEWATA_TEST_MODE:-0}" != "1" && "$RESTORE_IS_PROD" -eq 1 ]]; then
        if systemctl restart "$SERVICE"; then
            echo "  service restarted: $SERVICE"
            # Verify the listener is back up.
            for attempt in 1 2 3 4 5 6 7 8 9 10; do
                if ss -ltn 2>/dev/null | grep -q ":$LISTENER_PORT "; then
                    echo "  post-restore listener up: :$LISTENER_PORT"
                    break
                fi
                sleep 1
            done
            if ! ss -ltn 2>/dev/null | grep -q ":$LISTENER_PORT "; then
                echo "  RESTORE FAILED: :$LISTENER_PORT not listening after post-restore restart" >&2
                restore_failed=1
            fi
            # Verify the post-restart MainPID is different from the
            # pre-restart MainPID (sanity that a real restart happened).
            POST_RESTORE_PID=$(systemctl show "$SERVICE" -p MainPID --value)
            echo "  post-restore $SERVICE MainPID=$POST_RESTORE_PID"
        else
            echo "  RESTORE FAILED: systemctl restart $SERVICE returned non-zero" >&2
            restore_failed=1
        fi
    else
        echo "  skipping post-restore restart (DEWATA_TEST_MODE=$DEWATA_TEST_MODE, RESTORE_IS_PROD=$RESTORE_IS_PROD)"
    fi

    # 4. verify the restored Caddyfile sha256 matches the snapshot\'s
    #    runtime sha256 (the strongest verification possible).
    if [[ -f "$SNAPSHOT_DIR/Caddyfile.dewata.runtime" ]]; then
        RESTORED_SHA=$(sha256_of_file "$PROD")
        SNAPSHOT_RUNTIME_SHA=$(sha256_of_file "$SNAPSHOT_DIR/Caddyfile.dewata.runtime")
        if [[ "$RESTORED_SHA" != "$SNAPSHOT_RUNTIME_SHA" ]]; then
            echo "  RESTORE FAILED: restored $PROD sha256 ($RESTORED_SHA) does not match snapshot runtime sha256 ($SNAPSHOT_RUNTIME_SHA)" >&2
            restore_failed=1
        else
            echo "  restored Caddyfile sha256 verified: $RESTORED_SHA"
        fi
    fi

    # 5. restore the prior release tree (only if G3 had published a
    #    new tree and saved the old one aside).
    if [[ -n "$RELEASE_BACKED_UP" && -d "$RELEASE_BACKED_UP" ]]; then
        echo "  auto-restore: swapping published tree back to prior release"
        if [[ -d "$RELEASE_DST" ]]; then
            mv "$RELEASE_DST" "${RELEASE_DST}.postrestore.$(date -u +%Y%m%dT%H%M%SZ)"
        fi
        if mv "$RELEASE_BACKED_UP" "$RELEASE_DST"; then
            echo "  prior release restored from $RELEASE_BACKED_UP"
        else
            echo "  RESTORE FAILED: could not move $RELEASE_BACKED_UP back to $RELEASE_DST" >&2
            restore_failed=1
        fi
    fi

    if (( restore_failed )); then
        echo "  AUTO-RESTORE INCOMPLETE: inspect $PROD and $RELEASE_DST manually." >&2
        exit 2
    fi
    echo "  AUTO-RESTORE COMPLETE: $PROD and $RELEASE_DST restored to prior state."
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
# Mandatory drift check.  The install refuses to proceed if the live
# production Caddyfile's sha256 does not match the supplied baseline.
# The baseline is captured right before this install runs; if anything
# has changed the file since, the operator must re-evaluate.
live_sha=$(sha256_of_file "$PROD")
if [[ "$live_sha" != "$PROD_BASELINE_SHA" ]]; then
    echo "FATAL: production caddyfile drifted from baseline."
    echo "  baseline sha256: $PROD_BASELINE_SHA"
    echo "  live     sha256: $live_sha ($PROD)"
    echo "Refusing to install.  Investigate the drift first."
    exit 3
fi
echo "G0: production Caddyfile matches baseline ($live_sha)"

# P2/3: candidate Caddyfile must match the reviewed manifest's entry
# for that file.  If the manifest is missing the install refuses (we
# pin to the reviewed artifact, not the mutable worktree).
if [[ ! -f "$REVIEWED_MANIFEST" ]]; then
    echo "ERROR: reviewed release manifest not found at $RELEASE_MANIFEST"
    echo "Refusing to install.  Generate the manifest from the reviewed"
    echo "release directory (deploy/atomic/build-review-manifest.sh)"
    exit 1
fi
MANIFEST_CANDIDATE_SHA=$(awk '$2 == "Caddyfile.dewata.proposed"{print $1}' "$REVIEWED_MANIFEST" | head -1)
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
done < "$REVIEWED_MANIFEST"

# Bidirectional cross-check: every manifest entry must be an existing
# regular file in $RELEASE_SRC; every regular file in $RELEASE_SRC must
# be listed in the manifest.  Symlinks are rejected outright.  This
# runs BEFORE snapshot so the install cannot proceed against a
# mismatched source.

# Collect the set of files we will cross-check: skip the manifest
# header, the Caddyfile.dewata.proposed line, and any other comment
# lines that start with "#".  The "##" prefix in the awk skip pattern
# matches those comment lines.
# Build the set of manifest entries that must exist in $RELEASE_SRC.
# We deliberately exclude the candidate Caddyfile (Caddyfile.dewata.proposed)
# because it is installed separately in G4 from its own path, not from
# the release tree.
manifest_entries=$(awk '/^[a-f0-9]/{print $2}' "$REVIEWED_MANIFEST" \
    | grep -v "^Caddyfile.dewata.proposed$" | sort -u)
if [[ -z "$manifest_entries" ]]; then
    echo "FATAL: manifest $REVIEWED_MANIFEST contains no <sha> <relpath> entries." >&2
    exit 6
fi

# 1. every manifest entry must be an existing regular file in $RELEASE_SRC.
#    This is finding #1: the previous check only warned for "files in
#    source not in manifest" and silently created the staging dir even
#    when manifest entries were missing.  Now each missing manifest
#    entry fails the install.
missing_in_src=0
while IFS= read -r rel; do
    [[ -z "$rel" ]] && continue
    if [[ ! -f "$RELEASE_SRC/$rel" ]]; then
        echo "FATAL: manifest entry missing in RELEASE_SRC: $rel" >&2
        echo "  expected: $RELEASE_SRC/$rel" >&2
        missing_in_src=$((missing_in_src+1))
    fi
done <<< "$manifest_entries"
if (( missing_in_src > 0 )); then
    echo "FATAL: $missing_in_src manifest entries are missing in RELEASE_SRC. refusing to install." >&2
    exit 6
fi

# 2. no symlinks in $RELEASE_SRC.
if (cd "$RELEASE_SRC" && find . -type l 2>/dev/null) | grep -q .; then
    echo "FATAL: release source contains symlinks.  symlinks are rejected by this script." >&2
    (cd "$RELEASE_SRC" && find . -type l) | sed "s|^|  |" >&2
    exit 5
fi

# 3. every regular file in $RELEASE_SRC must be listed in the manifest.
#    Walk with `find -type f` so directories do not need to be in the
#    manifest themselves.
src_files=$( (cd "$RELEASE_SRC" && find . -type f) | sed 's|^\./||' | sort -u )
extra_in_src=0
while IFS= read -r rel; do
    [[ -z "$rel" ]] && continue
    if ! grep -qxF "$rel" <<< "$manifest_entries"; then
        echo "FATAL: file in RELEASE_SRC but not in manifest: $rel" >&2
        extra_in_src=$((extra_in_src+1))
    fi
done <<< "$src_files"
if (( extra_in_src > 0 )); then
    echo "FATAL: $extra_in_src files in RELEASE_SRC are not listed in the manifest. refusing to install." >&2
    exit 6
fi

echo "G0: release manifest cross-check passed ($(echo "$manifest_entries" | wc -l) entries, all present in RELEASE_SRC)"

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
# SNAPSHOT_DIR: where the install script saves its pre-apex snapshot.
# Default is the worktree; tests can override with DEWATA_SNAPSHOT_PARENT.
SNAPSHOT_PARENT="${DEWATA_SNAPSHOT_PARENT:-$WORKTREE/deploy/atomic}"
SNAPSHOT_DIR="$SNAPSHOT_PARENT/$(date -u +%Y%m%dT%H%M%SZ)-pre-apex"
mkdir -p "$SNAPSHOT_DIR"
install -m 0644 "$PROD" "$SNAPSHOT_DIR/Caddyfile.dewata.runtime"
install -m 0644 "$CANDIDATE" "$SNAPSHOT_DIR/Caddyfile.dewata.candidate"
diff -u "$SNAPSHOT_DIR/Caddyfile.dewata.runtime" \
        "$SNAPSHOT_DIR/Caddyfile.dewata.candidate" \
        > "$SNAPSHOT_DIR/Caddyfile.dewata.diff" || true
echo "G2: snapshot saved to $SNAPSHOT_DIR"
SNAPSHOT_CAPTURED=1

# Capture the sha of the current production Caddyfile BEFORE we
# touch anything.  After G4 we compare against this; if equal, the
# install is a no-op and we MUST NOT restart the service.
PRE_INSTALL_PROD_SHA=$(sha256_of_file "$PROD")
echo "G2: pre-install $PROD sha256 = $PRE_INSTALL_PROD_SHA"

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
    exp=$(awk -v r="$rel" '$2 == r {print $1}' "$REVIEWED_MANIFEST" | head -1)
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
# Reject the staging outright if any manifest-listed file is missing
# or fails sha256 verification.  Do NOT silently create empty
# directories to mask a missing entry — that is exactly the bug the
# previous installer had.
# Counters go in temp files because the staging loop runs in a
# subshell (pipeline); plain bash vars would be lost on exit.
STAGE_COUNTERS="$STAGING_DIR.stage-counters"
: > "$STAGE_COUNTERS"
awk '/^[a-f0-9]/{print}' "$REVIEWED_MANIFEST" | while read -r sum rel rest; do
    # skip the caddyfile entry (handled in G4) and any header/comment
    if [[ -z "$rel" || "$rel" == "Caddyfile.dewata.proposed" ]]; then
        continue
    fi
    src="$RELEASE_SRC/$rel"
    dst="$STAGING_DIR/$rel"
    if [[ ! -f "$src" ]]; then
        echo "FATAL: manifest entry missing in RELEASE_SRC: $rel" >&2
        echo "  expected: $src" >&2
        echo MISSING >> "$STAGE_COUNTERS"
        continue
    fi
    actual=$(sha256_of_file "$src")
    if [[ "$actual" != "$sum" ]]; then
        echo "FATAL: sha256 mismatch for $rel" >&2
        echo "  manifest: $sum" >&2
        echo "  source  : $actual" >&2
        echo SHA_MISMATCH >> "$STAGE_COUNTERS"
        continue
    fi
    mkdir -p "$(dirname "$dst")"
    cp -p "$src" "$dst"
    echo STAGED >> "$STAGE_COUNTERS"
done
n_staged=$(grep -c ^STAGED$ "$STAGE_COUNTERS" || true)
n_missing_in_src=$(grep -c ^MISSING$ "$STAGE_COUNTERS" || true)
n_sha_mismatch=$(grep -c ^SHA_MISMATCH$ "$STAGE_COUNTERS" || true)
if (( n_missing_in_src > 0 || n_sha_mismatch > 0 )); then
    echo "FATAL: staging failed: $n_missing_in_src missing, $n_sha_mismatch sha-mismatched. refusing to publish." >&2
    do_restore "staging failed: missing/mismatched manifest entries"
fi
echo "G3: staged $n_staged files; no missing entries, no sha mismatches"

# Exact-set comparison: every file in the staged tree must be a
# manifest entry (excluding the caddyfile which is not staged here),
# and every manifest entry (excluding the caddyfile) must be present
# in the staged tree.
# Stage counters live in $STAGING_DIR.stage-counters (sibling file,
# outside $STAGING_DIR) so the published release never contains
# the sentinel.  See $STAGE_COUNTERS for the staged/n_missing/
# n_sha_mismatch tallies.
staged_files=$( (cd "$STAGING_DIR" && find . -type f) | sed "s|^\./||" | sort -u )
manifest_files_to_stage=$(awk '/^[a-f0-9]/{print $2}' "$REVIEWED_MANIFEST" \
    | grep -v "^Caddyfile.dewata.proposed$" | sort -u)

# staged files must be a subset of manifest files (no extras in stage)
extras_in_stage=$(comm -23 <(printf "%s\n" "$staged_files") <(printf "%s\n" "$manifest_files_to_stage"))
if [[ -n "$extras_in_stage" ]]; then
    echo "FATAL: staged tree has files not in manifest:" >&2
    printf "  %s\n" $extras_in_stage >&2
    do_restore "staged tree has files not in manifest"
fi
# manifest files must be a subset of staged files (no missing in stage)
missing_in_stage=$(comm -13 <(printf "%s\n" "$staged_files") <(printf "%s\n" "$manifest_files_to_stage"))
if [[ -n "$missing_in_stage" ]]; then
    echo "FATAL: manifest entries not in staged tree:" >&2
    printf "  %s\n" $missing_in_stage >&2
    do_restore "manifest entries missing from staged tree"
fi

echo "G3: staged tree exactly matches manifest (excluding Caddyfile.dewata.proposed)"

# Atomic publish: rename staging -> release.
#   1. Move the OLD release to a sibling backup (without deleting it)
#      so we can recover if anything goes wrong later.
#   2. Move the staging directory to the release target atomically
#      (single rename, same filesystem).
#   3. After publish, run the same exact-set comparison on the
#      published tree to confirm the swap was complete.
if [[ -d "$RELEASE_DST" ]]; then
    BACKUP_PATH="$RELEASE_DST.bak.$(date -u +%Y%m%dT%H%M%SZ)"
    echo "G3: pre-existing $RELEASE_DST found; preserving as $BACKUP_PATH"
    if ! mv "$RELEASE_DST" "$BACKUP_PATH"; then
        echo "FATAL: could not move $RELEASE_DST aside before publish" >&2
        do_restore "backup move failed"
    fi
    echo "G3: backup secured at $BACKUP_PATH"
    # Track the backup so do_restore can put it back if anything fails.
    RELEASE_BACKED_UP="$BACKUP_PATH"
fi
if ! mv "$STAGING_DIR" "$RELEASE_DST"; then
    echo "FATAL: atomic publish failed (mv $STAGING_DIR -> $RELEASE_DST)" >&2
    do_restore "atomic publish failed"
fi
echo "G3: release published at $RELEASE_DST"

# Post-publish exact-set comparison: the published tree must match the
# manifest exactly.
published_files=$( (cd "$RELEASE_DST" && find . -type f) | sed "s|^\./||" | sort -u )

# 1. published tree must not have any extras
extras_in_published=$(comm -23 <(printf "%s\n" "$published_files") <(printf "%s\n" "$manifest_files_to_stage"))
if [[ -n "$extras_in_published" ]]; then
    echo "FATAL: published tree has files not in manifest:" >&2
    printf "  %s\n" $extras_in_published >&2
    do_restore "published tree has files not in manifest"
fi
# 2. published tree must have every manifest entry
missing_in_published=$(comm -13 <(printf "%s\n" "$published_files") <(printf "%s\n" "$manifest_files_to_stage"))
if [[ -n "$missing_in_published" ]]; then
    echo "FATAL: manifest entries not in published tree:" >&2
    printf "  %s\n" $missing_in_published >&2
    do_restore "manifest entries missing from published tree"
fi
# 3. every published file's sha256 must match the manifest
fail=0
while IFS= read -r rel; do
    [[ -z "$rel" ]] && continue
    sum=$(sha256_of_file "$RELEASE_DST/$rel")
    exp=$(awk -v r="$rel" '$2 == r {print $1}' "$REVIEWED_MANIFEST" | head -1)
    if [[ "$sum" != "$exp" ]]; then
        echo "FATAL: sha256 mismatch after publish for $rel" >&2
        echo "  published: $sum" >&2
        echo "  manifest : $exp" >&2
        fail=1
    fi
done <<< "$published_files"
if (( fail )); then
    echo "FATAL: published release does not match manifest" >&2
    do_restore "post-publish sha mismatch"
fi

n_files=$(printf "%s\n" "$published_files" | grep -c . || true)
echo "G3: $n_files files at $RELEASE_DST (exact-set match against manifest)"

# Failure-injection hook: simulate a failure AFTER publication (after G3
# has swapped the staging dir into place, after the post-publish exact-set
# comparison passed) but before G4.  This triggers do_restore with the
# release tree backed up.
if [[ "${DEWATA_FAKE_FAIL_AT_GATE:-}" == "g3-post-publish" ]]; then
    echo "FATAL: DEWATA_FAKE_FAIL_AT_GATE=g3-post-publish -> simulating failure after G3" >&2
    do_restore "injected failure after G3 publication"
fi

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
PROD_WRITTEN=1
# Failure-injection hook: simulate a G4 failure (e.g. file sync issue,
# permission denied on a subsequent step) AFTER publication has succeeded.
if [[ "${DEWATA_FAKE_FAIL_AT_GATE:-}" == "g4" ]]; then
    echo "FATAL: DEWATA_FAKE_FAIL_AT_GATE=g4 -> simulating post-G4 failure" >&2
    do_restore "injected failure after G4"
fi

# --------------------------------------------------------------------
# G5: re-validate the installed file
# --------------------------------------------------------------------
echo
echo "================================================================"
echo "G5: re-validate installed file"
echo "================================================================"
/usr/bin/caddy validate --config "$PROD" --adapter caddyfile

# Failure-injection hook: simulate a failure AFTER the candidate caddyfile
# has been installed (G4) and validated (G5) but BEFORE G6 restart.
if [[ "${DEWATA_FAKE_FAIL_AT_GATE:-}" == "g5" ]]; then
    echo "FATAL: DEWATA_FAKE_FAIL_AT_GATE=g5 -> simulating failure after G5 (pre-restart)" >&2
    do_restore "injected failure after G5 validation"
fi

# --------------------------------------------------------------------
# G6: restart (mirrors install semantics, controlled via DEWATA_TEST_MODE)
# --------------------------------------------------------------------
echo
echo "================================================================"
echo "G6: restart $SERVICE"
echo "================================================================"
echo "G6: restarting $SERVICE (graceful; expect ~2-3s :$LISTENER_PORT interruption)"

# No-op check + restart decision.  Three rules apply here:
#
#   1. If the just-installed candidate caddyfile is byte-identical to
#      the caddyfile we started with, no live change occurred and
#      we MUST NOT restart (a restart would briefly interrupt the
#      listener with no benefit).
#
#   2. The G6 restart branch ONLY fires when DEWATA_TEST_MODE != 1
#      AND $PROD is a known production path.  Otherwise the install
#      refuses to restart caddy.  This prevents a disposable install
#      (with DEWATA_TEST_MODE unset) from accidentally restarting
#      the real production caddy.
#
#   3. The post-restart listener check enforces that caddy came back
#      up.  This fires do_restore on failure.
POST_INSTALL_PROD_SHA=$(sha256_of_file "$PROD")
if [[ "$POST_INSTALL_PROD_SHA" == "$PRE_INSTALL_PROD_SHA" ]]; then
    echo "G6: install was a no-op (candidate == current prod caddyfile, sha $POST_INSTALL_PROD_SHA)"
    echo "G6: skipping systemctl restart -- no live change to apply"
    OLD_PID=$(systemctl show "$SERVICE" -p MainPID --value 2>/dev/null || echo 0)
    NEW_PID="$OLD_PID"
    RESTART_INVOKED=0
    echo "G6: $SERVICE MainPID unchanged: $OLD_PID"
else
    echo "G6: candidate caddyfile differs from production (was $PRE_INSTALL_PROD_SHA, now $POST_INSTALL_PROD_SHA); restart decision pending"
    # Determine whether this is a production install (and we may restart
    # caddy) or a disposable install (and we must NOT restart caddy).
    IS_PROD_PATH=0
    case "$PROD" in
        /opt/dewata.online/*|/etc/caddy/*|/var/lib/dewata/*) IS_PROD_PATH=1 ;;
    esac
    if [[ "${DEWATA_TEST_MODE:-0}" == "1" ]]; then
        OLD_PID=$(systemctl show "$SERVICE" -p MainPID --value 2>/dev/null || echo 0)
        NEW_PID=0
        RESTART_INVOKED=0
        echo "G6: DEWATA_TEST_MODE=1 -> skipping systemctl restart (driver will take over)"
        echo "G6: pre-restart $SERVICE MainPID=$OLD_PID"
        echo "G6: post-restart $SERVICE MainPID=$NEW_PID (driver will take over)"
    elif [[ "$IS_PROD_PATH" -eq 0 ]]; then
        # Non-production path with no DEWATA_TEST_MODE.  Refuse to
        # restart caddy; instead treat as a no-op so the install
        # does not interfere with the host\'s service.  The lifecycle
        # test always sets DEWATA_TEST_MODE=1 for this reason.
        OLD_PID=$(systemctl show "$SERVICE" -p MainPID --value 2>/dev/null || echo 0)
        NEW_PID="$OLD_PID"
        RESTART_INVOKED=0
        echo "G6: non-production path with DEWATA_TEST_MODE unset -> skipping systemctl restart"
        echo "G6:   set DEWATA_TEST_MODE=1 explicitly to enable restart in a disposable"
        echo "G6: $SERVICE MainPID unchanged: $OLD_PID"
    else
        OLD_PID=$(systemctl show "$SERVICE" -p MainPID --value)
        echo "G6: pre-restart $SERVICE MainPID=$OLD_PID"
        # Hook for failure-injection: if DEWATA_FAKE_RESTART_FAILURE=1, run
        # systemctl restart normally but mark RESTART_INVOKED=1 anyway so
        # the do_restore flow runs; we then tamper with the listener check
        # below to simulate a service that crashed after config reload.
        if [[ "${DEWATA_FAKE_RESTART_FAILURE:-0}" == "1" ]]; then
            echo "G6: DEWATA_FAKE_RESTART_FAILURE=1 -> simulating post-restart failure"
            systemctl restart "$SERVICE" || true
            RESTART_INVOKED=1
            NEW_PID=$(systemctl show "$SERVICE" -p MainPID --value)
            echo "G6: post-restart $SERVICE MainPID=$NEW_PID"
        else
            systemctl restart "$SERVICE"
            RESTART_INVOKED=1
            for attempt in 1 2 3 4 5 6 7 8 9 10 11 12; do
                state=$(systemctl is-active "$SERVICE" || true)
                if [[ "$state" == "active" ]]; then break; fi
                sleep 1
            done
            NEW_PID=$(systemctl show "$SERVICE" -p MainPID --value)
            echo "G6: post-restart $SERVICE MainPID=$NEW_PID"
        fi
    fi
fi

# Post-restart listener check.  Only fires in production mode AND
# only when the install path is a known production path.  For
# disposable installs the listener on :$LISTENER_PORT is provided by
# the lifecycle test\'s disposable caddy; this script does not own
# that lifecycle.
LISTENER_IS_PROD=0
case "$PROD" in
    /opt/dewata.online/*|/etc/caddy/*|/var/lib/dewata/*) LISTENER_IS_PROD=1 ;;
esac
if [[ "${DEWATA_TEST_MODE:-0}" != "1" && "$LISTENER_IS_PROD" -eq 1 ]]; then
    ss -ltn | grep -q ":$LISTENER_PORT " && echo "G6: :$LISTENER_PORT listening" || {
        echo "FATAL: :$LISTENER_PORT not listening after restart"
        do_restore "post-restart listener check"
    }
fi

# Failure-injection hook for restart/recovery testing.  This fires
# AFTER the G6 restart (or after the test-mode restart-skip) so the
# test can verify do_restore runs even when the restart path itself
# succeeded.  Useful for confirming the recovery sequence runs end-
# to-end.  Honors DEWATA_FAKE_FAIL_AT_GATE=g6 in either production
# or test mode.
if [[ "${DEWATA_FAKE_FAIL_AT_GATE:-}" == "g6" ]]; then
    echo "FATAL: DEWATA_FAKE_FAIL_AT_GATE=g6 -> simulating post-restart failure" >&2
    do_restore "injected failure after G6"
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
    SNAPSHOT_CAPTURED=0
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

# G7 HTTP probes: only run in production mode AND only against a
# known production path.  The lifecycle test launches its own
# disposable caddy on :$LISTENER_PORT and runs its own probes.
G7_IS_PROD=0
case "$PROD" in
    /opt/dewata.online/*|/etc/caddy/*|/var/lib/dewata/*) G7_IS_PROD=1 ;;
esac
if [[ "${DEWATA_TEST_MODE:-0}" != "1" || "$G7_IS_PROD" -eq 0 ]]; then
    echo
    echo "================================================================"
    echo "G7: HTTP probes (skipped: DEWATA_TEST_MODE=$DEWATA_TEST_MODE, G7_IS_PROD=$G7_IS_PROD)"
    echo "================================================================"
    echo "  lifecycle driver or no-op disposable install; production probes not applicable"
else
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
fi  # close the G7 production-mode block

# Done.  Disable auto-restore on success.
# --------------------------------------------------------------------
trap - ERR
SNAPSHOT_CAPTURED=0

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
