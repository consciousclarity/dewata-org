#!/usr/bin/env bash
# Wrapper end-to-end disposable mirror test -- evidence for the bundle
# In production, the wrapper is run from /opt/dw-phase2/deploy with
# DEWATA_APPLY_PRODUCTION=1 (and no DEWATA_DEPLOYER_TEST_MODE).
# Here we exercise the same operator command against a disposable
# mirror under /tmp/deploy-mirror so we can prove the wrapper's audit
# trail and fail-closed behavior without touching /opt/dewata.online.
rm -rf /tmp/deploy-mirror
for d in caddy www atomic; do
    mkdir -p /tmp/deploy-mirror/$d
done

# Production Caddyfile destination (mirror)
cp /opt/dewata.online/deploy/caddy/Caddyfile.dewata /tmp/deploy-mirror/caddy/Caddyfile.dewata

DEPLOY_INSTALLER=/opt/dw-phase2/deploy/atomic/install-apex-candidate.sh \
DEPLOY_ROLLBACK=/opt/dw-phase2/deploy/atomic/rollback-apex.sh \
DEPLOY_REVIEWED_MANIFEST=/opt/dw-phase2/deploy/atomic/RELEASES/v0.1.0-pre1.MANIFEST.txt \
DEPLOY_REVIEWED_RELEASE_SRC=/opt/dw-phase2/deploy/www/dewata-org/v0.1.0-pre1 \
DEPLOY_REVIEWED_CANDIDATE=/opt/dw-phase2/deploy/caddy/Caddyfile.dewata.proposed \
DEPLOY_PROD_CADDY=/tmp/deploy-mirror/caddy/Caddyfile.dewata \
DEPLOY_PROD_RELEASE_DST=/tmp/deploy-mirror/www/dewata-org/v0.1.0-pre1 \
DEPLOY_SNAPSHOT_PARENT=/tmp/deploy-mirror/atomic \
DEPLOY_LISTENER_PORT=18443 \
DEPLOY_SERVICE=dewata-caddy-dummy \
DEWATA_APPLY_PRODUCTION=1 \
DEWATA_FORCE_REINSTALL=1 \
DEWATA_DEPLOYER_TEST_MODE=1 \
bash /opt/dw-phase2/deploy/apex-deploy.sh
echo
echo "[wrapper-test] exit=$?"
echo "[wrapper-test] audit-trail summary:"
PROD_CADDY_SHA=$(sha256sum /tmp/deploy-mirror/caddy/Caddyfile.dewata | cut -d' ' -f1)
echo "  prod Caddyfile sha256: $PROD_CADDY_SHA"
echo "  release destination state:"
if [[ -d "$DEPLOY_PROD_RELEASE_DST" ]]; then
    n=$(find "$DEPLOY_PROD_RELEASE_DST" -type f | wc -l)
    echo "    $DEPLOY_PROD_RELEASE_DST EXISTS with $n files"
else
    echo "    $DEPLOY_PROD_RELEASE_DST DOES NOT EXIST (first-install end state)"
fi
echo "  snapshot dirs:"
echo "    $(ls -d /tmp/deploy-mirror/atomic/*-pre-apex 2>/dev/null | wc -l) snapshot(s) under /tmp/deploy-mirror/atomic"
