# System Map — dewata.org components

> **snapshot date:** 2026-09-20

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Public internet                                                            │
│   *.dewata.org  (DNS delegated to Cloudflare, apex → 62.72.7.218)           │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼  HTTPS (Cloudflare terminates TLS)
┌─────────────────────────────────────────────────────────────────────────────┐
│ 62.72.7.218 — this VPS                                                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Host Caddy (PID 775, /etc/caddy/Caddyfile)                          │   │
│  │   binds :80/:443, serves *.nusa.business + gustale + ...            │   │
│  │   forwards *.dewata.org traffic to 127.0.0.1:8443                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                  │ plaintext (private backbone)             │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ dewata-caddy.service (Caddyfile.dewata, :8443)                     │   │
│  │   @apex → /opt/dewata.online/deploy/www/dewata-org/{DEWATA_RELEASE_ROOT}│
│  │   @wiki → /opt/dewata.online/deploy/www/wiki/{DEWATA_WIKI_RELEASE_ROOT}│
│  │   @api  → reverse_proxy 127.0.0.1:8765                             │   │
│  │   @bci, @protocol, @datasets → respond 503 (placeholders)         │   │
│  │   catch-all → respond 503                                           │   │
│  │                                                                     │   │
│  │ reload disabled (would address :2019 on the host caddy by accident)│   │
│  │ changes require `systemctl restart dewata-caddy.service`           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                  │                                          │
│                                  ▼ (api only)                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ dewata-api.service                                                  │   │
│  │   ExecStart: /opt/dewata.online/.venv/bin/uvicorn                   │   │
│  │              api.main:app --host 127.0.0.1 --port 8765              │   │
│  │   working dir: /opt/dewata.online                                   │   │
│  │   env: /root/.env.dewata.online (DEWATA_DB_*, DEWATA_LIVE_DOMAIN)   │   │
│  │   imports: dewatacalendar.dsp (editable install at                  │   │
│  │            /opt/dewata.online/phase-1/src via _editable_impl.pth)   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ shared-postgres (postgis/postgis:16-3.4) on 127.0.0.1:5432         │   │
│  │   database: dewata (NOT YET USED by phase-1 calendar API)          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼ (CI)
┌─────────────────────────────────────────────────────────────────────────────┐
│ github.com/consciousclarity/dewata-org                                      │
│   .github/workflows/tests.yml                                              │
│     jobs:                                                                   │
│       pytest (phase-1): checkout (fetch-depth 0), install -e .[dev],       │
│                          curl pinned SakaCalendar.java + sha256 verify,    │
│                          python -m pytest -q -rs                           │
│       wiki: checkout (fetch-depth 0), pip install -r wiki/requirements.txt │
│             + pytest 8.3.5, python -m pytest wiki/tests -q -rs            │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component responsibilities

| component | responsibility | tech | owner |
|---|---|---|---|
| **dewata-api** (FastAPI on 127.0.0.1:8765) | DSP calendar endpoints (read-only v0.1) | fastapi, pydantic, uvicorn | phase-1 |
| **dewata-caddy** (:8443) | reverse proxy for *.dewata.org; env-var-driven release dirs | caddy | deploy |
| **shared-postgres** | phase-2+ state (banjar, pura, ceremony, evidence); not used by phase-1 calendar API yet | postgis 16-3.4 | shared with nusa.business |
| **wiki.dewata.org** | static multilingual knowledge base; term pages with front-matter; runs `wiki/tests` on every PR | mkdocs-material | phase-1 + wiki |
| **dewata.org apex** | static landing page (ban/id/en), explicit "awaiting customary review" banner | static | deploy |
| **CI (tests.yml)** | enforces pytest + sha256 of pinned reference | github actions | n/a |

## Dependencies (declared in pyproject.toml)

- `fastapi>=0.115`, `uvicorn[standard]>=0.32`, `pydantic>=2.9`, `python-dateutil>=2.9` — runtime
- `pytest>=8.3`, `pytest-asyncio>=0.24`, `httpx>=0.28` — dev

Pinned non-vendored LGPL evidence: `https://raw.githubusercontent.com/edysantosa/sakacalendar/21ff347c0431cb12e02296f76077aa40525da9e0/src/main/com/edysantosa/sakacalendar/SakaCalendar.java` (sha256 `dda574c4d0434c9fcc35fa60fa700e1ae1f8e7b5eafc88d20346ed93d5687579`).

## Boundary summary

- **cloudflare → caddy :8443**: TLS terminated at edge; origin sees plaintext over cloudflared's private backbone.
- **caddy :8443 → dewata-api :8765**: localhost-only.
- **dewata-api → postgres**: localhost-only (no public exposure).
- **PROTOCOL.md §0** is the production-safety boundary for Hermes (no deploy, no restart, no main push, no secret rotation).

## Phase roadmap (per ARCHITECTURE.md §13)

| phase | deliverable | status |
|---|---|---|
| 0 | schema, engine skeleton, one DSP endpoint | done |
| 1 | engine + 50k vector corpus | **shipped** |
| 2 | banjar / pura identity model | not shipped |
| 3 | ceremony CRUD + visibility tier system | not shipped |
| 4 | gianyar pilot, one trusted loop published | not shipped |
| 5 | mesh SSE feeds + mirror subscriptions | not shipped |
| 6 | whatsapp bridge | not shipped |
| 7 | USSD hotline | not shipped |
| 8 | time-machine archive publication | not shipped |
| 9 | island-wide federation (year 2) | not shipped |
