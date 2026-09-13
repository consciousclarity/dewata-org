# RELEASE_v0.1.0 (13 September 2026)

> ini bukan "rilis resmi produksi" — ini adalah **rilis
> foundational pertama**, dengan customary review **belum selesai**.

## apa yang di-ship

- **kalender engine v0.1**: pawukon + saka + wewaran + rahinan,
  deterministic, 75,608 conformance vectors, 43 tests pass in 3.14s.
- **DSP v0.1 spec skeleton** (calendar endpoints).
- **conformance cross-validation**: engine dibandingkan dengan
  Cunningham 1994 dan Igarashi 1999 sources. disagreement tercatat
  dengan provenance penuh.
- **i18n**: indonesian + balinese + english wrappers untuk 30 wuku,
  5 pancawara, 7 saptawara, 12 sasih, 12 rahinan.
- **operator handbook**: dua versi (indonesian + basabali) untuk
  pemangku dan bendesa adat.
- **ruleset versioning runbook** dengan 7 invariants cultural.
- **dispute review protocol**: 30/90-day review cadence dengan
  classification (`epoch_offset`, `rule_drift`, `calendar_variant`).
- **CI workflow**: `.github/workflows/test.yml` runs `pytest` and
  `dewatacalendar test` on push and on PR.
- **LICENSE** dengan cultural-sovereignty notice.
- **CITATION.cff** untuk akademik sitiran.
- **README dalam tiga bahasa**: basabali utama, indonesia kedua,
  inggris opt-in.

## apa yang BELUM

- **customary sign-off**: 3 cross-validation disputes masih `pending`.
  kami **belum** memiliki seorang bendesa adat atau pemangku Keramas
  yang telah sign-off pada ruleset v0.1. lihat `docs/runbook/SIGNOFF.md`.
- **public deployment**: belum ada `api.dewata.org`/`bci.dewata.org`
  domain yang live. domain `dewata.org` terdaftar di spaceship, dns
  akan migrate ke cloudflare.
- **mirror chain**: belum ada mirror partner yang terpasang.
- **time-machine archives**: belum ada historical archive
  dipublikasikan.
- **event CRUD, cultural federation mesh**: phase 2 belum shipped.

## jumlah & metrik

- 1,250+ baris python code (engine)
- 750+ baris dokumentasi (handbook + runbook)
- 75,608 conformance vectors
- 43 tests pass (3.14s)
- 0 failed

## metadata

```
package:            dewatacalendar
version:            0.1.0
ruleset:            pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0
release_date:       2026-09-13
license:            MIT (with cultural-sovereignty notice)
github:             https://github.com/consciousclarity/dewata-org
hosting:            hostinger (this VPS)
default_branch:     main
```

## catatan penting

karena customary review belum selesai, rilis ini **tidak boleh**
dipublikasikan atau dipromosikan untuk publik. rilis hanya untuk
peninjauan internal dan koordinasi dengan calon partners.

---

the next release, v0.1.1, akan meningkatkan:

1. customary sign-off didokumentasikan untuk ruleset `pawukon-v0.4.1`
2. at least 1 mirror partner terpasang
3. at least 1 dispute berubah status (accepted / rejected / variant)
4. api publik resmi untuk end-user banjar

---

bali / september 2026 / tim dewata
