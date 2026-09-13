# fallback: cloudflared tunnel for dewata.org
#
# ONLY used if cloudflare's "Origin Server → Port" panel is not
# user-editable on the free plan. run instructions:
#
#   curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg \
#     | gpg --dearmor -o /etc/apt/keyrings/cloudflare.gpg
#   echo "deb [signed-by=/etc/apt/keyrings/cloudflare.gpg] \
#     https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" \
#     > /etc/apt/sources.list.d/cloudflared.list
#   apt-get update
#   apt-get install -y cloudflared
#
# then authenticate and create a tunnel:
#   cloudflared tunnel login
#   cloudflared tunnel create dewata
#   cloudflared tunnel route dns dewata api.dewata.org
#
# config file lives in /etc/cloudflared/config.yml:
#
#   tunnel: <tunnel-uuid>
#   credentials-file: /etc/cloudflared/<tunnel-uuid>.json
#   ingress:
#     - hostname: api.dewata.org
#       service: http://127.0.0.1:8765  # dewata-api direct
#     - hostname: "*.dewata.org"
#       service: http://127.0.0.1:8443  # dewata-caddy
#     - service: http_status:404
#
# run via systemd:
#   cloudflared service install  # creates user /etc/cloudflared
#   systemctl enable --now cloudflared
#
# this bypasses the origin-port entirely: cloudflared connects from this
# vps *outbound* to cloudflare's tunnel endpoints; the host caddy + port
# 80/443 are untouched. isolated.
