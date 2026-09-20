# Caddy reload policy for dewata-caddy

## The problem

`dewata-caddy.service` (PID range 563570 / 976 historically) is a separate
Caddy instance listening on `:8443` for `*.dewata.org` traffic. The host
Caddy (`caddy.service`, PID 775) listens on `:80` and `:443` for
`*.nusa.business`, `gustale.com`, `gustale.recipes`, `komputer.shop`,
and similar.

Both Caddy binaries are the same upstream Caddy 2.x. Both default to
binding their administration API at `localhost:2019` when the loaded
config has no explicit `admin` directive. When `admin off` is set in the
config (as it is in `Caddyfile.dewata:43`), Caddy's `reload` command
falls back to the default `localhost:2019` because the address comes
from the loaded config and there is no address to read.

There is exactly **one** admin API listening on this host: the host
Caddy's, on `127.0.0.1:2019`. The dewata Caddy has no admin API
(both startups log `"admin endpoint disabled"`).

Therefore: `caddy reload` invoked by `ExecReload=/usr/bin/caddy reload
--config /opt/dewata.online/deploy/caddy/Caddyfile.dewata --adapter ''`
will POST the dewata Caddyfile to the **host Caddy's admin API**, not
its own. The host Caddy would attempt to apply the dewata config and
replace its own configuration wholesale.

## Why the host is still up

The 2026-09-17 and 2026-09-20 reload attempts failed because the host
Caddy (user `caddy`) could not open the dewata log path
`/opt/dewata.online/deploy/logs/caddy-private.log` (mode 600,
owner `root:root`) for write. The Caddy reload POST returns HTTP 400;
systemd records the failure; nothing changes.

This is not a control. It is a property of one file's current mode
and ownership. If that file ever becomes `caddy`-writable (different
mode, different ownership, different path), the next reload tears down
every other site on this host — silently, with no log line that says
"this is suspicious."

## Why Option A (drop ExecReload) won

Considered:

- **Option A: drop `ExecReload`.** No reload path. Config changes go
  through `systemctl daemon-reload && systemctl restart
  dewata-caddy.service`. Cost: ~2 seconds of downtime per config
  change (observed in journal: 06:08:48 → 06:08:48 = ~1 second at
  boot; 12:54:33 → 12:54:33 = ~1 second at manual restart).

- **Option B: dedicated admin endpoint on a unix socket.** `admin
  unix//opt/dewata.online/deploy/caddy/admin.sock` plus `--address
  unix//...` in ExecReload. Zero-downtime reloads. Cost: unix socket
  ownership and mode management, plus an extra failure surface.

Chose A. Reasons:

1. **The defect mode is silent.** A successful reload against the
   wrong admin endpoint tears down the host with no warning. The
   only thing standing in the way is a single file's mode.

2. **Option B is not "more correct", just "different bug".** A
   dedicated unix socket still has permissions, still has a creation
   step, still has to be present after ExecStartPre. Each is a
   different failure mode, not the absence of one.

3. **Reload semantics are wrong for this Caddyfile.** The deploy
   procedure is: change `DEWATA_WIKI_RELEASE_ROOT` in the systemd
   unit, restart. Caddy expands env vars at config-load time
   (ExecStart), not at reload time. Reloading does not pick up a new
   env-var value. The reload buys nothing the restart does not also
   give.

4. **No reload justifies the risk.** Every config change goes
   through git. Every deploy is a `systemctl restart`. There is no
   hot-reload use case for this unit.

5. **The blast radius is bounded by a coincidence, not a control.**
   That is the decisive argument. A control is something that
   continues to hold when circumstances change; a coincidence holds
   only until it doesn't.

## Procedure

### Caddyfile change

1. Edit `deploy/caddy/Caddyfile.dewata`.
2. Commit on a branch off `main`.
3. Push and open PR.
4. After merge, on the host:
   ```sh
   sudo cp /opt/dewata.online/deploy/caddy/Caddyfile.dewata /opt/dewata.online/deploy/caddy/Caddyfile.dewata
   sudo systemctl daemon-reload
   sudo systemctl restart dewata-caddy.service
   ```
   There is **no** `systemctl reload dewata-caddy.service`. That
   command does not exist for this unit on purpose.

### Wiki release rotation (env-var only)

1. Stage the new release at `/opt/dewata.online/deploy/www/wiki/<sha>-r<n>/`.
2. Update `DEWATA_WIKI_RELEASE_ROOT` in
   `/etc/systemd/system/dewata-caddy.service`.
3. On the host:
   ```sh
   sudo systemctl daemon-reload
   sudo systemctl restart dewata-caddy.service
   ```
4. Verify with:
   ```sh
   curl -sI -H 'Host: wiki.dewata.org' http://127.0.0.1:8443/
   ```

The Caddyfile itself is unchanged. The repo path `deploy/systemd/dewata-caddy.service`
is not the live unit; `/etc/systemd/system/dewata-caddy.service` is. The
operator step above is required — see "Drift risk" below.

### Apex release rotation

Same as wiki. `DEWATA_RELEASE_ROOT` controls the apex landing page.

## Drift risk

The repo file at `deploy/systemd/dewata-caddy.service` is **not**
the live unit. The live unit is at
`/etc/systemd/system/dewata-caddy.service`. They are not linked by
symlink, not auto-synced, and not enforced by any CI check.

The operator must manually `cp` the repo file over the live unit after
every merge that changes it, then run `systemctl daemon-reload`. This
gap is its own drift risk and is named here for that reason. It is
not fixed by this commit; closing it would require either:

- a CI check that diffs the two files and fails the build on
  divergence, or
- a symlink from `/etc/systemd/system/dewata-caddy.service` to
  `deploy/systemd/dewata-caddy.service` (changes the deploy process;
  requires operator agreement).

Both are out of scope for the present change. The current behavior is
documented in `DEPLOY.md` and in this file.

## Verification chain (post-merge, on the host)

1. `sudo cp deploy/systemd/dewata-caddy.service /etc/systemd/system/dewata-caddy.service`
2. `sudo systemctl daemon-reload`
3. `sudo systemctl restart dewata-caddy.service`
4. `systemctl show dewata-caddy.service -p ExecReload` — must be empty.
   If non-empty, the operator step did not pick up the new unit file.
5. `systemctl show dewata-caddy.service -p ExecStart,User,WorkingDirectory`
   — confirm rest of unit unchanged.
6. `journalctl -u dewata-caddy.service --since '5 minutes ago' --no-pager | grep 'admin endpoint disabled'`
   — must show admin endpoint disabled at the new startup.
7. `ss -tnlp | grep ':8443'` — must show the new PID.
8. `ss -tnlp | grep ':2019'` — must still show PID 775 (host caddy).
9. `curl -sI -H 'Host: dewata.org' http://127.0.0.1:8443/` — must be 200.
10. `curl -sI -H 'Host: wiki.dewata.org' http://127.0.0.1:8443/` — must be 200.
11. `curl -sI -H 'Host: random.dewata.org' http://127.0.0.1:8443/` — must be 503.
12. `curl -sI https://gustale.com/` — must be 200 (host Caddy untouched).

Steps 9-11 confirm the dewata Caddyfile is active. Step 12 confirms
the host Caddy has not been reconfigured. The point of dropping
ExecReload is to make step 12 robust regardless of which file changed.

## History

- 2026-09-17: first reload attempt logged the failure. The reload
  had been broken since the dewata-caddy unit was added.
- 2026-09-19: Caddyfile working-tree added @apex and @wiki
  handlers; live Caddy never picked them up because reload was
  broken.
- 2026-09-20 06:08:48: system boot loaded the working-tree
  Caddyfile directly via ExecStart. The handlers went live for the
  first time.
- 2026-09-20 12:50:49: another reload attempt failed at the same
  step (open caddy-private.log: permission denied). The error
  response was the host Caddy's structured error — confirmed the
  reload was reaching the wrong process.
- 2026-09-20: this policy written; ExecReload removed from the unit;
  Caddyfile corrected to prescribe `restart` not `reload`.

## See also

- `deploy/systemd/dewata-caddy.service` — the repo unit file with
  the ExecReload-deliberately-removed comment.
- `deploy/caddy/Caddyfile.dewata` — header now states the reload
  policy.
- `deploy/runbook/DEPLOY.md` — high-level deploy procedure.
- `phase-1/docs/runbook/RULESET_VERSIONING.md` — how ruleset
  versions relate to engine deploys (separate concern).
