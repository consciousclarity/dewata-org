# dispute review protocol

> indonesian-language operational protocol for the daily review of
> `docs/runbook/disputes.json`. geared for the operator who keeps the
> project running week-to-week.

## apa itu "dispute"?

sebuah *dispute* adalah catatan resmi yang disimpan di
`docs/runbook/disputes.json` setiap kali:

- vector conformance dari sumber diterbitkan (Cunningham, Igarashi,
  dll) **tidak cocok** dengan engine, atau
- banjar / operator / akademik mengirim rekaman tanggal yang tidak
  cocok dengan aturan kalender engine, atau
- sebuah aturan baru diajukan untuk dimasukkan ke corpus

setiap dispute disimpan dengan penjelasan, klasifikasi, dan asal
informasi. tidak ada yang "dihapus secara diam-diam".

## siklus hidup

| status        | artinya                                              | waktu          |
|---------------|------------------------------------------------------|----------------|
| `pending`     | fresh (baru dicatat), belum ditinjau                 | 0-30 hari      |
| `matured`     | belum ditinjau selama lebih dari 30 hari              | 30-89 hari     |
| `expired`     | belum ditinjau selama lebih dari 90 hari              | >= 90 hari     |
| `accepted`    | dispute dikenali engine salah, aturan dibetulkan       | anytime        |
| `rejected`    | dispute dikenali varian regional atau kesalahan input | anytime        |
| `variant`     | sengketa bukan bug, didokumentasikan sebagai varian  | anytime        |

## siapa yang meninjau

tiap dispute diberi tiga attribut di awal:

1. **classification** (`epoch_offset`, `rule_drift`, `calendar_variant`,
   `transcription`) — disetel otomatis, manusia boleh menindaknya
2. **reviewer** — orang yang menandatangani resolusi (pemangku / klian
   / bendesa, atau akademisi yang sesuai)
3. **resolution** — status tertinggi (`accepted` / `rejected` /
   `variant`) + tanggal

## cara pakai

### 1. harian (cron, 02:00 WITA)

jalankan cron harian ini:

```bash
# di /opt/dewata.online, oleh user cron
cd /opt/dewata.online
python -m dewatacalendar disputes --refresh > /var/log/dewata/disputes.log 2>&1
```

cron automatikalinya refresh dispute registry. tulis log ke
`/var/log/dewata/`.

### 2. mingguan — review yang matang

tiap minggu, operator menjalankan:

```bash
cd /opt/dewata.online
python -m dewatacalendar disputes                # print report
git diff docs/runbook/disputes.json             # check new disputes
```

untuk setiap `matured`:

1. baca catatan di file
2. cek apakah sudah punya bukti rujukan (Cunningham / Igarashi / nota
   bendesa)
3. putuskan klasifikasi final (`accepted` / `rejected` / `variant`)
4. update recordnya dengan resolver date dan reviewer name

untuk setiap `expired`:

1. escalate ke reviewer senior (bukan penulis kode)
2. kalau tidak ada resolusi yang mungkin didokumentasikan,
   tandakan `variant` (rezim peringatan akan berhenti berteriak)

### 3. triwulanan (90 hari)

snapshot statistik:

```bash
python -m dewatacalendar disputes --report > disputes_quarterly_report.txt
```

di-post sebagai summary di `docs/runbook/drafts/`. tidak di-tag ke
public API sampai customary review selesai.

## eskalasi otomatis via cron

tambahkan cron:

```
0 2 * * *  cd /opt/dewata.online && python -m dewatacalendar disputes --refresh
```

ini akan menambahkan /memperbarui `disputes.json` tanpa interaksi
manusia. manusia perlu komitmen untuk meresolusi secara berkala.

## kenapa 30/90 hari?

- **30 hari**: cukup waktu untuk melintasi siklus piodalan / minggu
  budaya — memberi banjar satu siklus budaya untuk merespons.
- **90 hari**: lewat batas hak budaya. kalau dispute masih belum
  resolv setelah 90 hari, kita perlu dokumentasikan varian atau
  membuat kesalahan eksplisit terhadap aturan.

kita tidak pernah **menghapus** dispute (lihat audit). kita hanya **mark
as variant** atau **accepted** atau **rejected**.

## audit trail

untuk setiap dispute yang sudah resolv, log di file
`docs/runbook/SIGNOFF.md` di bawah "Dispute Resolutions". entry:

```
YYYY-MM-DD    dispute_date        classification        resolved_as        reviewer_role           reviewer_name
1981-08-23    2026-09-14          epoch_offset           variant              akademisi kalender   i wayan ...
```

## apa yang TIDAK kami lakukan

- tidak pernah secara otomatis menerima dispute tanpa review manusia
- tidak pernah menghapus dispute (kami hanya menambah status)
- tidak pernah "force resolution" karena terburu-buru — budaya
  butuh waktu
- tidak pernah menampilkan dispute `pending` di UI publik — UI
  menunggu sampai dispute menjadi `variant` atau `accepted`

---

protokol ini di-revisi setiap 6 bulan sekali.

tim dewata, bali.
