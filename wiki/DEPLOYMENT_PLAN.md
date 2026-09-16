# Deployment plan — `wiki.dewata.org` (unexecuted)

> **Status: a written plan, not a deployment.**
>
> This document is the **deployment plan** required by §10 of the
> wiki foundation work. It is committed to the repository as
> reviewable evidence that the plan exists. **No part of it has
> been executed** as of this PR. DNS, Cloudflare, Caddy, the
> systemd unit on the production VPS, and the live
> `wiki.dewata.org` hostname all remain untouched.

## 1. Pre-deployment steps (run by a human, not Hermes)

1. Confirm the PR that publishes the wiki has been merged.
2. Confirm the resulting `wiki/site/` artefact is hosted as a
   static build that matches the markdown source in
   `wiki/docs/`. The reproducibility test in
   `wiki/tests/test_build_reproducibility.py` runs `mkdocs build`
   against pinned dependencies. **The build is reproducible
   because** every dependency in `wiki/requirements.txt` is pinned
   to a single version, and the nav is generated programmatically
   from the page tree by `wiki/scripts/build_mkdocs_config.py`
   (not handwritten).

## 2. DNS — record for `wiki.dewata.org`

| step | command (illustrative) | validated |
|---|---|---|
| 1 | `cloudflared` style A/AAAA record for `wiki.dewata.org` pointing at the static-host origin. | requires human execution |
| 2 | verify with `dig wiki.dewata.org A` that resolution succeeds. | requires human execution |

> The wiki MUST stay on the existing
> `dewata.org` zone. **No DNS record is created by this PR.**

## 3. TLS — Cloudflare-managed certificate

Use the Cloudflare-managed certificate bundle the same way the
existing `dewata.org` and `api.dewata.org` hostnames use it. The
wiki inherits Cloudflare's existing issuer configuration. There is
no new DNS-validation flow.

The wiki is a **read-only public site**. HTTP→HTTPS upgrade is
already handled by Cloudflare's edge.

## 4. Caddy / static-hosting configuration

> The active `deploy/caddy/Caddyfile.dewata` already routes
> `*.dewata.org` subdomains through the dewata-private Caddy
> process (currently on `:8443`). For `wiki.dewata.org`, the host
> matcher in that file should reach the static site directory.

A proposed, **non-binding** addition to
`deploy/caddy/Caddyfile.dewata`:

```caddyfile
@wiki host wiki.dewata.org
handle @wiki {
    root * /opt/dewata.online/deploy/www/wiki/v0.1.0
    encode zstd gzip
    file_server
}
```

> This proposal is illustrative. It must follow the existing
> `deploy/caddy/Caddyfile.dewata` review and the apex-deployment
> process (atomic `deploy/atomic/<timestamp>-wiki/` snapshot and
> rolled-restart), neither of which is touched by this PR.

The file served by Caddyfile's `root` directive is the
`wiki/site/` output of `mkdocs build`. We do **not** bind Caddy to
a development checkout.

## 5. Cache policy

The wiki ships as static HTML with a published
`sitemap.xml`. Use Cloudflare's cache-tier rules:

- `.html` — cache `public, max-age=300, must-revalidate` at the
  edge; `Cache-Control: public, max-age=600` at the origin.
- `assets/*` (Material theme CSS/JS bundles) —
  `Cache-Control: public, max-age=31536000, immutable`.
- `sitemap.xml` and `sitemap.xml.gz` —
  `Cache-Control: public, max-age=86400`.
- `search/search_index.json` — `Cache-Control: public, max-age=86400`.

The cache rule is implemented in
`deploy/caddy/Caddyfile.dewata` as
`header Cache-Control "..."` blocks under the `@wiki` host
matcher. **Those header blocks are NOT in the file today** — they
are added during the deployment PR.

## 6. Monitoring

We use the existing host Caddy's access log
(`/opt/dewata.online/deploy/logs/caddy-private.log`) as the only
monitoring surface. We add the following metrics:

- 4xx rate per minute, broken down by `error_code` and `path`,
  emitted to the existing log.
- 5xx rate per minute, same breakdown.
- bytes-served per minute.

We do **not** add a third-party monitoring agent. The wiki rejects
adoption of:

- tracking pixels,
- analytics JS,
- remote fonts,
- remote stylesheets.

The only network calls the static HTML makes are to in-site
`assets/`.

## 7. Rollback

Mirror the apex-deployment pattern:

1. Keep the prior wiki release under
   `/opt/dewata.online/deploy/www/wiki/v0.x.y/<PREVIOUS>`.
2. To roll back, point the Caddyfile `@wiki` matcher at the
   previous directory and reload Caddy.
3. Document the rollback in a `FROZEN_<version>_<date>.md` per
   `docs/PROTOCOL.md` §1.4 ("Append-only history").

The same `atomic/` snapshot discipline used by the apex
deployment applies. **This PR does not create that snapshot.**

## 8. Post-deployment checks

After deploying the wiki for the first time:

- `curl -I https://wiki.dewata.org/` returns HTTP 200.
- `curl -I https://wiki.dewata.org/id/` returns HTTP 200.
- `curl -I https://wiki.dewata.org/en/` returns HTTP 200.
- `curl -I https://wiki.dewata.org/ban/` returns HTTP 200.
- Each response carries the expected `Cache-Control` header.
- `https://wiki.dewata.org/sitemap.xml` is reachable and lists the
  same URL set as the build's `page_count`.
- `gnupg --verify` on any release artefact (we sign with the
  existing AGE key in `/root/.env.dewata.online`'s
  `SNAPSHOT_SIGNING_KEY`) succeeds.
- `python -m pytest wiki/tests` succeeds in CI for the deployed
  SHA.

These checks are written into
`docs/runbook/POST_DEPLOYMENT_wiki.md` in the deployment PR
(not in this PR).

## 9. Pre-conditions the deployment PR must satisfy

Before `wiki.dewata.org` is live:

1. customary sign-off for the Bahasa Bali translations (the wiki
   currently carries `pending_customary_review` for all `ban/`
   pages).
2. RESOLVED records for the three malformed `disputes.json`
   entries that pre-date this audit.
3. The 366-day range guard merged (the calendar engine
   `compose_day` is the wiki's primary term-page test surface;
   the wiki links back to its test contract).
4. customary review of the ceremony descriptions in
   `/en/rahinan/` and `/id/rahinan/` so the `daily_status` of
   those pages moves from `implementation_definition` to
   `customary_attestation_required` (a transition, not a claim).

## 10. What this document does NOT do

This document does **not** add the Caddy route. It does **not**
issue a Cloudflare API token. It does **not** change the
production VPS. It does **not** push to GitHub.

This document is the design record of what the deployment PR will
do when it is eventually opened by the operator authorised to make
those changes. Until that PR exists, `wiki.dewata.org` continues
to return NXDOMAIN.
