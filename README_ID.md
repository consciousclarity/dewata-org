# README (indonesian / primary)

> README utama. versi bahasa Bali ada di `README_BAL.md`.
> versi inggris ada di `README_EN.md`.

## apa itu dewata?

dewata (ᬤᭂᬯᬢ, "dewa-dewa" — para dewa) adalah protokol komputer untuk
pencatatan, pensahan, dan pelestarian upacara adat bali.

proyek ini dirancangkan untuk **banjar, pura, dan desa adat bali** —
bukan untuk turis. kami mencatat *nyepi* dan *odalan*, bukan *what's
closed for traffic*.

## apa saja yang bisa dicatat

- piodalan (ulang tahun pura, 210 hari)
- odalan utama dan madya
- melasti (prosesi ke pantai atau mata air)
- ngaben dan pelebon
- paruman (rapat desa adat)
- ngayah (kewajiban gotong royong)
- kerama

## apa yang tidak boleh kami catat

- wewenang adat (bendesa adat yang lebih tahu)
- keputusan pribadi pemangku
- tanggal yang kami usulkan sendiri (kami hanya menulis ulang apa yang banjar sudah tetapkan)
- rekomendasi bisnis atau catatan iklan

## instalasi

```bash
pip install -e phase-1/
python -m dewatacalendar ruleset
python -m dewatacalendar date 2026-09-13
```

## arsip conformance

disimpan di `phase-1/conformance/`. 75k+ vectors dihasilkan dari engine,
beberapa ribu tambahan datang dari sumber yang telah diterbitkan
(cunningham, igarashi). setiap vector membawa catatan asal
(`source`, `page`).

## ada masalah dengan tanggal yang kami catat?

lihat `docs/runbook/disputes.json`. kami mencatat semua perbedaan
dengan sumber yang dipublikasikan — beberapa adalah epoch-offset,
beberapa adalah variants regional yang disengaja, beberapa adalah bugs.

## struktur proyek

```
ARCHITECTURE.md         rencana engineering
phase-1/                engine kalender + api
phase-1/conformance/    vectors kalibrasi (75k+)
phase-1/src/dewatacalendar/
                        paket python utama
phase-1/docs/           handbook + runbook
deploy/                 dns cli + scaffolding
registry/               banjar/pura/dataset registry tsv
scripts/                verify.sh, dll
.github/workflows/      CI test workflow
```

## menghubungi kami

lihat `bci.dewata.org/connect` setelah deploy ke publik.
wa, ussd, dan surel semuanya tersedia untuk banjar / pura / individu
yang ingin mendaftarkan upacaranya.

## lisensi & sitiran akademis

MIT, dengan **ayat perlindungan kedaulatan adat**. untuk sitiran
akademis, lihat `CITATION.cff`.

---

tim dewata, bali
