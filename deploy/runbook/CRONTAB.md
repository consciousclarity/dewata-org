# daily ops cron — v0.1.0
#
# install with:
#   crontab -u root -e
# then paste this file's body minus comments

# ───── daily: refresh disputes registry at 02:00 WITA ─────
0 2 * * * cd /opt/dewata.online && python -m dewatacalendar disputes --refresh >> /opt/dewata.online/deploy/logs/disputes-cron.log 2>&1

# ───── weekly: snapshot sign + publish (phase 2 ships this) ─────
# 0 3 * * 1  cd /opt/dewata.online && python -m dewata_snapshots sign today

# ───── every-5-min: ping dewata-api and alert on failure ─────
*/5 * * * * curl -sf --max-time 5 http://127.0.0.1:8765/health > /dev/null || (echo "[$(date -Is)] dewata-api health check failed" >> /var/log/dewata/uptime.log; systemctl restart dewata-api.service)

# ───── monthly: dispute review cadence ─────
0 4 1 * *  cd /opt/dewata.online && python -m dewatacalendar disputes > /opt/dewata.online/deploy/logs/disputes-monthly.log 2>&1
