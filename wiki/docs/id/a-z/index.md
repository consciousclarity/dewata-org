---
status: informational
translation_review_status:
  id: needs_review
  ban: pending_customary_review
  en: needs_review
last_reviewed: 2026-09-17
---

# Daftar A–Z istilah dewata.org

Indeks lengkap istilah yang dipakai di proyek dewata.org. Setiap
entri adalah satu halaman; halaman diurut berdasarkan
`canonical_slug`.

Catatan: indeks ini dihasilkan oleh
[`scripts/build_coverage_report.py`](../../scripts/build_coverage_report.py)
dan disimpan ke
[`build-artifacts/coverage.json`](../../build-artifacts/coverage.json)
setiap build. Halaman root ini adalah representasi markdown dari
laporan cakupan, dengan hyperlink ke setiap istilah.

## Cara membaca

- Tiap baris mencantumkan `canonical_term`, kategori, dan status.
- Tiap istilah merujuk ke tiga halaman terjemahan:
  `/<lang>/<slug>/...`
- Status `verified_source` berarti halaman berasal dari dokumen
  repository yang ada.
- Status `disputed` berarti halaman merujuk id dispute aktif di
  `phase-1/docs/runbook/disputes.json`.
- Status `implementation_definition` berarti halaman menjelaskan
  perilaku `phase-1/src/dewatacalendar/`, bukan kebiasaan.
- Status `pending_customary_review` berarti halaman butuh
  tinjauan kebiasaan sebelum status final.

## Status ringkasan

lihat coverage.json (output dari build).

## Bagian menurut kategori

- [Kalender bali](/id/calendar/) — Pawukon, Saka, Wewaran, Rahinan
- [Tata kelola adat](/id/governance/) — Banjar, Pura, Pemangku, dst.
- [Bukti dan tata kelola](/id/evidence/) — STATUS.json, dispute
- [Platform dewata](/id/platform/) — DSP, API, rilis

<!--
end of A-Z index — pages link back to /id/, /en/, /ban/ indexes.
-->
