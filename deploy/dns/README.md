# dewata-dns

idempotent DNS provisioning for `dewata.org`, written to be the smallest
thing that can do the banjar pilot cleanly.

## install

```bash
sudo install -m 0755 /opt/dewata.online/deploy/dns/dewata-dns /usr/local/bin/
```

## configure

1. copy `/opt/dewata.online/deploy/dns/.env.dewata.online.template`
   to `/root/.env.dewata.online`, chmod 600
2. fill in:
   - `CLOUDFLARE_API_TOKEN` — `Edit zone DNS` scope on zone `dewata.org`
   - `CLOUDFLARE_ZONE_ID` — from cloudflare dashboard, zone `dewata.org`
   - `HOSTINGER_IP` — the IP of the hostinger server where api/map/data live

## use

```bash
# single canonical record
dewata-dns upsert-canonical bjr gianyar 0001 62.72.7.218

# human-friendly alias (CNAME)
dewata-dns upsert-alias banjar-ubud-tengah gianyar bjr gianyar 0001

# bulk from registry TSV
dewata-dns sync-registry /opt/dewata.online/registry/banjar.gianyar.tsv

# audit current cloudflare state
dewata-dns list

# drift detection: registry vs cloudflare
dewata-dns diff --tsv /opt/dewata.online/registry/banjar.gianyar.tsv

# verify apex + ns
dewata-dns verify
```

## idempotency

every call is idempotent on `(name, type, content, proxied)`. calling twice
does nothing on the second call; calling with a different IP edits in place.
no records are deleted except by explicit operator action.

## what it does *not* do

- does not delete records (use cloudflare dashboard for that)
- does not manage the apex `dewata.org` A record (managed separately to avoid breaking live service)
- does not touch `dewata.online` (separate legacy domain, namecheap registrar)
- does not manage ssl/wildcard cert (cloudflare does that with one-click)
