# deployment runbook — v0.1.0

> how `dewata-api` ships and what the deployment surface looks like in
> v0.1.0. customs-first, no tourism-or-navigation scope.

## what's running on this host

| component | unit | listens on | upstream |
|---|---|---|---|
| `dewata-api.service` | systemd unit | `127.0.0.1:8765` (uvicorn) | behind caddy (planned) and cloudflare (planned) |
| fastapi app | `api.main:app` | uvicorn mounts DSP v0.1 calendar endpoints | `dewatacalendar.api.compose_day` |

the systemd unit lives at `/etc/systemd/system/dewata-api.service`.
the source file is `/opt/dewata.online/deploy/systemd/dewata-api.service`.

## why `Type=simple` and not `Type=notify`

`Type=notify` requires uvicorn to integrate with systemd's
`sd_notify(3)` protocol. that needs the `systemd` python package and a
configuration flag on uvicorn. `Type=simple` is robust to all
interpreters and cost us no observability — we still have journald for
log capture.

## what's exposed publicly

| hostname | resolves via | routing | safe to ship today? |
|---|---|---|---|
| `api.dewata.org` | cloudflare cname → 62.72.7.218 | (planned) caddy → :8765 | **not yet**, blocked on caddy import |
| `bci.dewata.org` | (planned) cname | caddy → :8765 | not yet |
| `protocol.dewata.org` | (planned) cname | caddy → :8765 | not yet |
| `datasets.dewata.org` | (planned) cname | caddy → :8765 | not yet |

right now, **the api is reachable only via `127.0.0.1` on this vps**.
nothing is exposed to the public internet until the caddy vhost is
imported and the cloudflare cname is created.

## how to deploy from scratch

paste-ready. takes ~5 minutes.

```bash
cd /opt/dewata.online
./deploy/bin/dewata-deploy.sh apply
```

this script:
1. creates a venv if missing
2. installs the package (`pip install -e phase-1/`)
3. copies the systemd unit if missing
4. (re)starts the service
5. verifies `/health` over curl

## how to verify state

```bash
./deploy/bin/dewata-deploy.sh status
```

prints:
- `systemctl status dewata-api.service`
- last 20 lines from journalctl
- the `/health` curl result

## what to do when something breaks

1. **port 8765 already taken** — `ss -ltnp | grep 8765`, then kill the
   process. likely a previous uvicorn is alive.
2. **service won't start** — `journalctl -xeu dewata-api.service` shows
   the reason. the most common failures are:
   - `EnvironmentFile=/root/.env.dewata.online` missing — recreate
     the env file (paste-only path, not chat)
   - `ExecStart` path not found — re-run `deploy.sh apply` to repair
3. **`/health` returns 503** — engine error. inspect logs; conform
   with `python -m dewatacalendar test`
4. **a banjar / pura operator wants to file a dispute** — they go to
   `dispute report`, the dispute lands in `disputes.json`, the
   30/90-day review cadence kicks in

## what's not deployed yet (and isn't blocking v0.1.0)

- cloudflare cname records for `api.dwata.org` etc.
- caddy vhost imports into the host's existing caddy
- DNS-resolvable public URL
- mirror-chain publication
- signed snapshot publication
- time-machine archive publication

## customary review status

still **none** signed off. see `docs/runbook/SIGNOFF.md`. the 3
cross-validation disputes are still pending.

---

deployment runbook: 2026-09-13 / v0.1.0
