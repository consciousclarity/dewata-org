# Deployment and Rollback Runbook — Dewata.org

> production is **not** deployed by this commit.  any deployment
> must follow this runbook, peer-reviewed, and only after the staging
> variant passes (`api-staging.dewata.org`).

## 1. pre-flight (read-only)

```
# verify environment is sane
test -f /opt/dewata.online/phase-1/src/api/main.py
docker ps --filter name=shared-postgres | head
systemctl is-active dewata-api
systemctl is-active dewata-caddy
systemctl is-active cloudflared
curl --max-time 5 -i https://api.dewata.org/health
```

expected: `200` from `/health`; cloudflared `active`; caddy active.

## 2. choose a target

- **staging**: `api-staging.dewata.org` (DNS A → 62.72.7.218, separate caddy vhost on :8443)
- **production**: `api.dewata.org` (Cloudflare-proxied → 62.72.7.218 → caddy :8443)

the brief's absolute boundaries prohibit unauthorized deploys.  always
specify one of these targets in advance.

## 3. apply database migration (staging only)

```
# 1. verify the migration does not target production
DEWATA_PROD_CONFIRM=no python -m dewatacalendar.db up \
    --target "host=127.0.0.1 port=54329 dbname=dewata_staging"
# 2. inspect schema diff (postgresql-only)
DEWATA_PROD_CONFIRM=no python -m dewatacalendar.db status \
    --target …
# 3. rollback if failure
DEWATA_PROD_CONFIRM=no python -m dewatacalendar.db down \
    --target …
```

**never** run `down` against the live `dewata` database; the brief
prohibits running migrations against the production db.

## 4. deploy the api

```
cd /opt/dewata.online
git fetch origin
git pull --ff-only
# restart the api service
sudo systemctl restart dewata-api
# verify health
curl -fsS http://127.0.0.1:8765/health
```

## 5. deploy the bci web bundle

see `phase-1/docs/web/DEPLOY.md`.  the bundle is built with:

```
PYTHONPATH=phase-1/src:phase-1/web/src python phase-1/web/src/build.py
```

and then served via caddy or cloudflare-r2.

## 6. smoke tests

```
curl -fsS https://api-staging.dewata.org/health | jq .
curl -fsS https://api-staging.dewata.org/dsp/v0.1/calendar/ruleset | jq .
curl -fsS https://api-staging.dewata.org/dsp/v0.1/calendar/date/2026-09-14
curl -fsS https://api-staging.dewata.org/ceremony/v0.1/visibility-tiers
```

## 7. rollback

```
# 7a) code rollback (last known good)
git log -3
git revert <bad_commit_sha> --no-edit
git push origin HEAD:main  -- requires workflow-scope PAT

# 7b) service rollback
sudo systemctl restart dewata-api

# 7c) dns rollback
#    (no script for this — humans)
```

## 8. backup and restore

| database | backup cadence | location | retention |
|---|---|---|---|
| dewata production | every 6 hours via cron (NOT installed yet — pending ops decision) | object storage | 30 days |
| dewata staging  | pre-migration only | git history | indefinite |

## 9. acceptance criteria

- [ ] staging `/health` returns 200 within 1s
- [ ] staging DSP `/calendar/ruleset` returns the running ruleset version
- [ ] staging DSP `/calendar/date/{YYYY-MM-DD}` returns the expected JSON
- [ ] staging auth: `POST /ceremony/v0.1/ceremonies` with no token → 401
- [ ] staging auth: with forged token → 401
- [ ] staging auth: valid token without scope → 403
- [ ] staging visibility: public-tier request cannot see banjar-tier fields
- [ ] no secret-scan findings in the deployed bundle
- [ ] caddy `:8765` and `:8443` listeners unchanged
- [ ] cloudflared status: healthy

## 10. post-deploy

- record commit SHA on the engineering brief / log
- announce on the staging chat
- copy brief `/home/alex/Documents/Obsidian Vault/Projects/Dewata.org/daily/<DATE>.md`
- if 7-day soak passes with no 4xx/5xx spike, request peer review for v0.2
