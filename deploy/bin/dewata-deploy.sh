#!/usr/bin/env bash
# dewata-deploy.sh — apply the dewata stack on the host.
#
# This is the *minimum* viable deployment run from this vps.
# It assumes:
#   - /opt/dewata.online is on disk (this repo)
#   - /root/.env.dewata.online has the cloudflare token, etc.
#   - cloudflare has been delegated for dewata.org
#
# what it does:
#   1. creates a venv and installs the package
#   2. registers and starts the systemd unit
#   3. validates via curl http://127.0.0.1:8765/health
#
# usage:
#   /opt/dewata.online/deploy/bin/dewata-deploy.sh apply
#   /opt/dewata.online/deploy/bin/dewata-deploy.sh status

set -euo pipefail

PROJECT=/opt/dewata.online
SERVICE_NAME="dewata-api"
HEALTH_URL="http://127.0.0.1:8765/health"

action="${1:-status}"

ensure_venv() {
    if [ ! -d "$PROJECT/.venv" ]; then
        echo "[deploy] creating venv"
        python3 -m venv "$PROJECT/.venv"
        "$PROJECT/.venv/bin/pip" install -q --upgrade pip
        # install package + dev extras (pytest, pytest-asyncio, httpx)
        "$PROJECT/.venv/bin/pip" install -q -e "$PROJECT/phase-1[dev]"
    else
        echo "[deploy] venv present"
        # idempotent upgrade of the package
        "$PROJECT/.venv/bin/pip" install -q -e "$PROJECT/phase-1[dev]" 2>/dev/null || true
    fi
}

ensure_systemd() {
    if [ ! -f /etc/systemd/system/"$SERVICE_NAME".service ]; then
        echo "[deploy] installing systemd unit"
        cp "$PROJECT/deploy/systemd/$SERVICE_NAME.service" /etc/systemd/system/"$SERVICE_NAME".service
        systemctl daemon-reload
        systemctl enable "$SERVICE_NAME"
    else
        echo "[deploy] systemd unit present"
    fi
    systemctl restart "$SERVICE_NAME" || systemctl start "$SERVICE_NAME"
    sleep 2
}

verify_health() {
    echo "[deploy] checking $HEALTH_URL"
    if curl -sf --max-time 5 "$HEALTH_URL" >/dev/null; then
        echo "[deploy] ✓ $HEALTH_URL is up"
        curl -sS "$HEALTH_URL"
    else
        echo "[deploy] ✗ $HEALTH_URL is unreachable; recent log follows"
        journalctl -n 30 --no-pager -u "$SERVICE_NAME" || true
        return 1
    fi
}

case "$action" in
    apply)
        ensure_venv
        ensure_systemd
        verify_health
        ;;
    status)
        systemctl --no-pager --full status "$SERVICE_NAME" 2>/dev/null || true
        echo
        echo "[deploy] last 20 log lines:"
        journalctl -n 20 --no-pager -u "$SERVICE_NAME" 2>/dev/null || true
        echo
        verify_health || true
        ;;
    *)
        echo "usage: $0 {apply|status}"
        exit 2
        ;;
esac
