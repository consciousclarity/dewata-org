# Operator Handbook — budaya bali

> panduan singkat untuk pemangku dan bendesa adat yang ingin menggunakan
> dewata.org untuk mencatat upacara adat.

## Apa itu dewata?

Dewata adalah protokol komputer untuk **mencatat, mensahkan, dan
melestarikan** catatan upacara adat bali. proyek ini dipimpin dengan
mematuhi adat dan wewenang yang berlaku — bukan membangun sistem
teknologi yang menggantikan adat.

apa yang **dewata.org lakukan**:
- menyimpan catatan piodalan pura
- menyimpan catatan odalan besar dan kecil
- menyimpan catatan paruman dan keputusan
- menyimpan catatan melasti, ngaben, dan nyepi
- mempublikasikan catatan sesuai tingkatan akses (lihat "siapa yang
  boleh lihat")

apa yang **dewata.org tidak lakukan**:
- tidak menggantikan wewenang adat
- tidak mengusulkan tanggal untuk pemangku
- tidak menggantikan keputusan bendesa
- tidak menampilkan iklan atau rekomendasi bisnis
- tidak membagikan nama keluarga yang sedang menjalani ngaben tanpa
  izin mereka

## Cara pertama: hubungi dahulu

pemangku dan bendesa yang ingin mulai mendaftarkan pura atau banjar
anda:

1. **wa** ke nomor yang akan diberikan di `bci.dewata.org/connect`
   (untuk operator yang terlatih; kami akan mengirim pesan verifikasi
   suara)
2. atau **ussd**: `*888*xxxx#` (untuk pemangku tanpa smartphone,
   instruksi lewat panggilan suara dalam bahasa bali)
3. atau hubungi **klian adat** di banjar anda, yang akan menjadi
   rekan pertama kami

proses ini akan:
- memverifikasi wewenang lewat telepon ke no. rumah pemangku keramas
- mendaftarkan kunci penandatangan (signing key) pura atau banjar anda
- memandu cara pertama menulis satu piodalan di platform

## Cara kedua: catat satu piodalan pertama

anda akan dibantu operator kami untuk:

1. buka aplikasi konsol (`bci.dewata.org/operator` — memerlukan
   one-time pin jika dari perangkat baru)
2. pilih pura anda dari daftar
3. pilih class: `piodalan` (default)
4. tulis tanggal piodalan (atau lihat tanggal prediksi otomatis dari
   kalender pawukon)
5. tulis nama Indonesian / bali acara
6. tulis daftar peserta (klian, pemangku, dll)
7. tandatangani (one-time pin ke no. hp anda)

ini menjadi **catatan pertama** untuk pura anda, tersimpan dengan
tanda tangan saka-bali-v0.2.3, dan terlihat di `bci.dewata.org/<kab>/<pura>`
untuk umum (tingkatan akses default `banjar`).

## Cara ketiga: lanjutkan

untuk pura yang aktif, anda akan menerima:
- notifikasi sebelum piodalan berikutnya (prediksi otomatis)
- formulir one-tap "ya, piodalan tanggal ini"
- formulir "tidak, tanggal berbeda karena alasan: ________"
- formulir "selesai, ini foto dokumentasi"

## Siapa yang boleh lihat

ada 5 tingkatan akses:
- **`public`** — semua orang (contoh: informasi "piodalan berikutnya
  di pura saraswati")
- **`banjar`** — anggota banjar default
- **`desa_adat`** — khusus desa adat
- **`restricted`** — keluarga / pemangku
- **`private`** — hanya anda sendiri

ada tiga hal yang tidak pernah dilakukan dewata:
1. dewata tidak pernah mempromosikan catatan ke tingkatan yang lebih
   luas tanpa izin sumber
2. dewata tidak pernah meminta nama keluarga untuk ngaben tanpa izin
3. dewata tidak pernah membocorkan catatan `restricted` ke pencarian
   publik

## Pertanyaan yang sering diajukan

**Q:** apakah pemangku dan bendesa harus hadir di pelatihan teknologi?
**A:** tidak. operator kami akan datang ke pura. anda hanya perlu
menandatangani dengan satu ketukan di ponsel.

**Q:** jika saya salah tanggal, apa dampaknya?
**A:** catatan tidak dihapus. kami menambahkan catatan revisi yang
mencatat perubahan. sejarah berubah dengan rapi.

**Q:** apa yang terjadi kalau dewata.org tidak bisa diakses (misal
listrik mati di gianyar selama seminggu)?
**A:** setiap pura dan banjar punya minimal 1 mirror. catatan tetap
tersimpan di tempat lain. jika anda menggunakan whatsapp, anda masih
bisa mengirim catatan yang akan diproses ketika jaringan pulih.

**Q:** apakah saya bisa melarang catatan tertentu ditampilkan di
google?
**A:** ya. semua catatan yang bukan `public` tidak diindeks oleh mesin
pencari. untuk catatan `public` sekalipun, halaman publik dewata.org
tidak mendorong untuk ditemukan di luar bali; protokol ini bukan
pariwisata.

## Bahasa yang digunakan

- **bali**: teks utama untuk antarmuka dan dokumen.
- **indonesia**: tersedia sebagai fallback.
- **english**: disediakan untuk akademisi; tidak muncul di UI publik.

## Jika anda ingin mundur

anda bisa memutuskan untuk tidak terdaftar kapanpun. caranya: kirim "STOP"
lewat aplikasi atau ucapkan "puput" (Bahasa Bali untuk "selesai") kepada
operator kami lewat wa. catatan yang sudah diterbitkan tetap tercatat
untuk arsip budaya, tapi anda bisa berhenti membuat catatan baru.

---

Kontak operasional: lihat `bci.dewata.org/connect`
Waktu respon: kirim sebelum pukul 21:00 WITA, dibalas sebelum pagi

— Tim Dewata, bali
