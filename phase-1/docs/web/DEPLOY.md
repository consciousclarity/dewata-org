# Balinese Cultural Index (BCI) — Frontend Deployment Runbook

> the bci is the public-facing static site.  as of v0.1 it is **not**
> deployed.  this runbook documents how to build and ship it later.
> **DO NOT** execute it yet — no deployments until staging review.

## scope

- static html pages, no javascript framework at v0.1
- i18n bundles per page (`bal`, `id`, `en`)
- nothing commercial: no ads, booking, directions, tracking
- explicit `provisional` policy marker on every page

## what it does NOT include

- no DNS records created
- no caddy surface modified
- no nginx / no apache
- no Next.js / no React at v0.1 (kept optional for v0.2)
- no live deployment targets before review

## build

```
PYTHONPATH=phase-1/src:phase-1/web/src \
    python phase-1/web/src/build.py
```

produces a static site at `phase-1/web/dist/`:

- `index.html`, `calendar.html`, `about.html`, `transparency.html`
- `assets/style.css`
- `assets/locales/*.json`

## test

```
python -m pytest phase-1/web/tests/ -v
```

7 tests in `test_build.py` enforce:

- the balinese locale has ≥5 keys
- every page carries the `provisional` policy marker
- no leftover `{{…}}` template tokens
- no commercial vocabulary (with negated phrases allowed in the footer)

## deployment (DO NOT EXECUTE UNTIL REVIEW)

```
# 1. build
PYTHONPATH=phase-1/src:phase-1/web/src python phase-1/web/src/build.py

# 2. choose a target.  options:
#    a. copy to a sub-path behind an existing caddy vhost
#    b. publish to a separate static-origin via cloudflare
#    c. hand to a content-cdn service
#
# 3. point bci.dewata.org at the chosen target via DNS A/CNAME.

# 4. ensure CSP headers are set by the hosting layer:
#    Content-Security-Policy: default-src 'self'; img-src 'self' data:;
#       style-src 'self'; script-src 'none'; frame-ancestors 'none'
```

## acceptance criteria

- [ ] page response < 200ms p95 from any single bali region
- [ ] no third-party fonts, no third-party scripts
- [ ] every page has a `<meta name="robots" content="noindex,nofollow">`
      during the staging period
- [ ] the `provisional` policy marker is visible in the footer
- [ ] all three locales (bal/id/en) are reachable
- [ ] keyboard navigation works on every page

## rollback

```
# rollback = point bci.dewata.org AWAY from this build.
# until DNS changes, the existing build remains.
```

## staged rollout

1. internal staging first: serving the dist via the existing private
   caddy on :8443 (vhost `bci-staging.dewata.org`)
2. pilot banjar review
3. bci.dewata.org DNS cutover only after #2 pass
4. remove `noindex,nofollow` after customary sign-off received
