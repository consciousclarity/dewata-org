# dewata-org

civic infrastructure for bali: a balinese temporal-spatial protocol.

see `ARCHITECTURE.md` for the full engineering plan and
`Projects/Dewata.org/phase1.engine_release_0.1.md` (obsidian) for the
shipped Phase 1 status.

## phase status

- **phase 0** — DNS / hostinger / database provisioned (in progress, see TODO)
- **phase 1** — calendar engine v0.1 ✓ shipped
- **phase 2-9** — see ARCHITECTURE.md

## quick start

```bash
# install
pip install -e phase-1/

# date lookup
python -m dewatacalendar date 1981-08-23

# calendar ruleset
python -m dewatacalendar ruleset

# conformance vectors (generate first via tests/gen_corpus.py if missing)
python -m dewatacalendar test
```

## end-to-end check

```bash
./scripts/verify.sh
```

## structure

```
ARCHITECTURE.md         canonical engineering plan
phase-1/
  src/dewatacalendar/    pure python, deterministic calendar engine
  src/api/               fastapi app (DSP calendar endpoints)
  tests/                 conformance corpus + pytest
  conformance/           75k generated vectors (gitignored, regenerated)
deploy/
  dns/                   dewata-dns cli, idempotent
registry/
  banjar/                <id>.<kab>.dewata.org registry TSVs
```

## citation

work in progress — see `Projects/Dewata.org/phase1.engine_release_0.1.md`
for what's currently testable.

## license

MIT.
