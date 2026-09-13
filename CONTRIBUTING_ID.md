# contributing (indonesian)

dewata.org berkembang dari sumbangan banjar-banjar. kontribusi paling
berharga bukan kode, melainkan:

  - **catatan piodalan** untuk pura anda
  - **koreksi** jika kalender kami salah
  - **i18n**: istilah bali yang lebih sesuai
  - **conformance vector**: tanggal yang telah dikonfirmasi oleh pemangku

## panduan singkat

### dari banjar / pura / individu (non-teknis)

cara paling sederhana: kirim pesan lewat wa/ussd ke operator kami. lihat
`bci.dewata.org/connect` (akan diumumkan setelah deploy).

yang operator kami butuhkan dari anda:
- satu catatan (contoh: "piodalan pura saraswati setiap wuku sinta, buda wage, mulai 14:00 s/d 18:00 WITA")
- tangkap layar atau foto kalenderanda (kalau ada)
- nama dan wewenang anda — operator kami akan memverifikasi terlebih dahulu lewat telepon

### dari kontributor teknis

- baca `docs/runbook/RULESET_VERSIONING.md`
- untuk corrections kalender: kirim dispute vector via PR atau lewat wa, jelaskan aturannya
- untuk perubahan kode: pastikan `python -m pytest phase-1/tests/ -q` lulus, dan catatankan klaim perubahan budaya di `docs/runbook/CHANGELOG.md`
- aturan versioning: "ruleset bump must have customary sign-off in `SIGNOFF.md` first" — tidak bisa ditawar

### untuk akademisi

- hindari perubahan yang dimaksudkan untuk "improve the calendar" berdasarkan interpretasi sendiri. kalau anda tidak yakin -- **taruh sebagai cross-validation dispute** di `docs/runbook/disputes.json`, bukan sebagai patch kode
- untuk penelitian lanjutan, gunakan dataset snapshot di `datasets.dewata.org/{YYYY-MM-DD}.tar.zst` (akan dipublikasi)
- untuk akses ke lintas-ruleset view, buka PR dengan label "academic"

### proses review (cultural + technical)

setiap PR melewati dua review:

1. **technical review**: pytest + dewatacalendar test lulus, tidak ada merge-conflict
2. **cultural review**: reviewer yang berbicara bali/indonesia (non-dewata affiliation) memverifikasi:
   - tidak ada istilah adat yang salah diterapkan
   - tidak ada rekor yang dipromosikan melintasi tingkatan akses tanpa deklarasi
   - tidak ada klaim "ini lebih akurat dari Cunningham/Igarashi" tanpa rujukan

kami menunda PR bukan karena kami tidak menghargainya. kami menunda PR demi adat dan masa depan arsip.

### privasi

jangan commit:
- nama keluarga yang sedang menjalani ngaben tanpa izin
- dokumen desa adat internal
- foto pemangku yang belum ada consent
- nomor phone yang belum punya consent

---

kalau anda ingin membantu tapi tidak yakin cara contributing:

baca `docs/handbook/HANDBOOK_ID.md` atau `docs/handbook/HANDBOOK_BAL.md` untuk
konteks proyek — itu bagian-bagian yang ditulis untuk pemangku dan
bendesa, bukan hanya untuk engineer.

kontak operasional: `bci.dewata.org/connect` setelah live.
waktu respon: kirim sebelum pukul 21:00 WITA, dibalas sebelum pagi.

---

Tim Dewata, bali
