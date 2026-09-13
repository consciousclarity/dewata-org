# README (Basa Bali — primary for Balinese readers)

> README ringkas antuk basa Bali. veri basa Indonesia ada ring
> `README_ID.md`. veri basa Inggris ada ring `README_EN.md`.

## Apa puniki dewata?

Dewata (ᬤᭂᬯᬢ, "dewa-dewa" — para dewa) punika protokol komputer anggén
nyatet, ngresin, miwah ngejelajah pakélingan upaca adat bali.

proyekiki kalaksanayang antuk **banjar, pura, miwah desa adat bali** —
nénten antuk turis. iraga nyatet *nyepi* miwah *odalan*, nénten *what's
closed for traffic*.

## Apa sane prasida katerpawang

- piodalan (rahinan ulang tahun pura, 210 dina)
- odalan ageng miwah odalan alit
- melasti (prosesi nuju segara utawi sumber toya)
- ngaben miwah pelebon
- paruman (rapat desa adat)
- ngayah (kewajiban gotong royong)
- kerama

## Apa sane nénten prasida katerpawang

- wewenang adat (bendesa adat sane labih mangrerahang)
- putusan pribadi pemangku
- tanggal sane iraga usulang dados wiadin (iraga kantun nyurat naén
  sane sampun katerpawang olih banjar)
- rekomendasi bisnis utawi catatan iklan

## Masang ring sistem

```bash
pip install -e phase-1/
python -m dewatacalendar ruleset
python -m dewatacalendar date 2026-09-13
```

## Arsip ringkas

katerpawang ring `phase-1/conformance/`. 75k+ vector kamargiang saking
engine, makudang sikiwot kapingkelsiang saking soroh sane sampun
katerbitiang (cunningham, igarashi). soang-soang vector ngicén pakélingan
asil (`source`, `page`).

## Wenten masalah ring tanggal sane katerpawang iraga?

cingak `docs/runbook/disputes.json`. iraga nyatet makudang pabesen
mawiguna ring soroh sane sampun katetah - pabean punika epoch-offset,
pabean puniki variants régional, pabean puniki bugs.

## Struktur proyek

```
ARCHITECTURE.md         rencana teknik
phase-1/                engine kalender + api
phase-1/conformance/    vector ringkas (75k+)
phase-1/src/dewatacalendar/
                        paket python paiun
phase-1/docs/           paédoman + runbook
deploy/                 dns cli + scaffolding
registry/               banjar/pura/dataset registry tsv
scripts/                verify.sh, dll
.github/workflows/      CI test workflow
```

## Ngubungang iraga

cingak `bci.dewata.org/connect` sawireh deploy ka wantah publik.
wa, ussd, miwah surel makasami prasida kaanggen antuk banjar / pura /
individu sane ngakin ngereh pakélingan upacané.

## Lisensi miwah sitiran akadmis

MIT, antuk **ayat pelindung kedaulatan adat**. antuk sitiran akadmis,
cingak `CITATION.cff`.

---

Paikél Dewata, bali
