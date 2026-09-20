"""emit curated term pages for the wiki foundation.

The brief asks for a substantive first draft across calendar,
governance, evidence, and platform terminology. Hand-writing 80+
pages in three languages would either be enormous or shallow. This
script emits each term as:

  - one Bahasa Bali stub at `wiki/docs/ban/<slug>.md` carrying
    `translation_status: pending_customary_review` and a pointer to
    the canonical language;
  - one Indonesian page at `wiki/docs/id/<slug>.md` carrying a
    short, sourced body that lists the sources and stays inside the
    repo's real facts;
  - one English page at `wiki/docs/en/<slug>.md` with the same shape
    and English-language prose.

Pages are intentionally short. They are **records, not essays**.
The detail and ceremonial meaning belongs in customary sign-off,
not in this wiki.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

ROOT = Path("/home/alex/workspace/wiki-foundation/wiki")
DOCS = ROOT / "docs"


# each tuple: (canonical_slug, category, status, [wuku / pancawara / sasih / saptawara / rahinan name])
# plus a brief one-sentence summary in Indonesian + English.

# Format: (slug, category, status, sources:list[(path,role,quote?)],
#          id_short, ban_phrase_idem_or_pending,
#          summary_id, summary_en)

TERMS: list[dict] = []

# --- Calendar Pawukon/Saka/Wewaran foundation terms ---


def term(slug, category, status, sources, summary_id, summary_en,
         id_spelling=None, en_spelling=None):
    TERMS.append({
        "slug": slug,
        "category": category,
        "status": status,
        "sources": sources,
        "summary_id": summary_id,
        "summary_en": summary_en,
        "id_spelling": id_spelling or slug.replace("-", " "),
        "en_spelling": en_spelling or slug.replace("-", " "),
    })


term(
    slug="pawukon",
    category="calendar",
    status="implementation_definition",
    sources=[
        ("phase-1/src/dewatacalendar/pawukon.py", "implementation"),
        ("phase-1/src/dewatacalendar/i18n.py", "implementation"),
        ("phase-1/src/dewatacalendar/rulesets.py", "ruleset", "epoch=1981-08-23"),
        ("phase-1/docs/audit/AUTHORITY_VALIDATION_PACKET_wuku_epoch_2026-09-16.md", "audit"),
    ],
    summary_id="Siklus 210 hari yang membagi 35 rentang 6 hari (pancawara) secara paralel.",
    summary_en="The 210-day cycle partitioning 35 ranges of 6 days (pancawara) in parallel.",
)


term(
    slug="wuku",
    category="calendar",
    status="implementation_definition",
    sources=[
        ("phase-1/src/dewatacalendar/i18n.py", "implementation", "WUKU_I18N (30 wuku)"),
        ("phase-1/src/dewatacalendar/pawukon.py", "implementation", "WUKU_NAMES_BALINESE (used by compose_day)"),
    ],
    summary_id="Daftar 30 wuku (siklus 7 hari) yang dipakai oleh engine dan disajikan dengan ejaan Bali di WUKU_I18N.",
    summary_en="The list of 30 wuku (7-day cycles) the engine uses; Balinese spellings are listed in WUKU_I18N.",
)

term(
    slug="210-day-cycle",
    category="calendar",
    status="implementation_definition",
    sources=[
        ("phase-1/src/dewatacalendar/pawukon.py", "implementation"),
        ("phase-1/src/dewatacalendar/rulesets.py", "ruleset", "epoch=1981-08-23"),
    ],
    summary_id="Siklus Pawukon = 30 wuku × 7 hari = 210 hari. Epoch: 1981-08-23.",
    summary_en="Pawukon cycle = 30 wuku × 7 days = 210 days. Epoch: 1981-08-23.",
)

term(
    slug="epoch-anchor",
    category="calendar",
    status="implementation_definition",
    sources=[
        ("phase-1/src/dewatacalendar/rulesets.py", "ruleset", '"epoch": "1981-08-23"'),
        ("phase-1/src/dewatacalendar/pawukon.py", "implementation", "pawukon_for_gregorian"),
    ],
    summary_id="Tanggal yang dideklarasikan sebagai cycle anchor untuk engine (di mana position_in_cycle == 1).",
    summary_en="The date declared as the cycle anchor for the engine, where position_in_cycle == 1.",
)

term(
    slug="phase-offset",
    category="calendar",
    status="implementation_definition",
    sources=[
        ("phase-1/docs/audit/CROSS_VALIDATION_full_range_1900_2099_2026-09-16.md", "evidence", "constant_offsets (Pancawara -1 mod 5, Pawukon +84 mod 210, Wuku +12 mod 30)"),
        ("phase-1/docs/audit/two-axis-analysis.md", "audit-record"),
    ],
    summary_id="Konstanta offset fase antara engine dan sumber referensional, diukur terhadap Peradnya dan Rust adapter. Disengaja didokumentasikan di STATUS.json.",
    summary_en="A constant phase offset between the engine and referential sources, measured against the Peradnya and Rust adapters. Deliberately recorded in STATUS.json.",
)

term(
    slug="saka",
    category="calendar",
    status="implementation_definition",
    sources=[
        ("phase-1/src/dewatacalendar/saka.py", "implementation"),
        ("phase-1/src/dewatacalendar/rulesets.py", "ruleset", "epoch_gregorian=1979-03-29, epoch_saka_year=1901"),
    ],
    summary_id="Tahun Saka dalam engine = Gregorian 1979-03-29 + offset. Lihat rulesets.saka.",
    summary_en="Saka year in the engine: Gregorian 1979-03-29 + offset. See rulesets.saka.",
)

term(
    slug="sasih",
    category="calendar",
    status="implementation_definition",
    sources=[
        ("phase-1/src/dewatacalendar/saka.py", "implementation"),
        ("phase-1/src/dewatacalendar/i18n.py", "implementation", "SASIH_I18N (12 sasih with sasih_idx 1..12)"),
        ("phase-1/docs/runbook/disputes.json", "policy", "DISPUTE-ENGINE-SASIH-INDEX-INVERSION"),
    ],
    summary_id="12 bulan lunar. sasih_idx ∈ [1..12]. Pemetaan nama engine ke sumber KB Org adalah disputed (lihat disputes.json).",
    summary_en="12 lunar months. sasih_idx ∈ [1..12]. Engine name-to-index mapping vs KB Org attestation is disputed (see disputes.json).",
)

term(
    slug="nampih-sasih",
    category="calendar",
    status="implementation_definition",
    sources=[
        ("phase-1/src/dewatacalendar/saka.py", "implementation"),
        ("phase-1/src/dewatacalendar/rulesets.py", "ruleset", "nampih_threshold_months=(12,11)"),
    ],
    summary_id="Interkalasi Saka Bali: mencegah Tilem Kapitu jatuh di Desember Gregorian.",
    summary_en="Bali Saka intercalation: prevents Tilem Kapitu from falling in Gregorian December.",
)

term(
    slug="pangunalatri",
    category="calendar",
    status="implementation_definition",
    sources=[
        ("phase-1/src/dewatacalendar/rulesets.py", "ruleset", "pangunalatri_implemented=False"),
        ("phase-1/src/dewatacalendar/saka.py", "implementation"),
    ],
    summary_id="Tidak diimplementasikan di engine: siklus 63 hari dan flag is_pangunalatri telah dihapus; istilahnya tetap nyata.",
    summary_en="Not implemented in the engine: the 63-day cycle and the is_pangunalatri flag were removed; the term itself remains real.",
)

term(
    slug="gregorian-date",
    category="calendar",
    status="implementation_definition",
    sources=[
        ("phase-1/src/dewatacalendar/api.py", "implementation", "compose_day accepts datetime.date"),
        ("phase-1/src/dewatacalendar/exceptions.py", "implementation"),
    ],
    summary_id="Tanggal Gregorian didukung oleh engine untuk tahun 1..9999 (pawukon) dan ≥1979 (saka).",
    summary_en="Gregorian dates are accepted by the engine for years 1..9999 (pawukon) and ≥1979 (saka).",
)

term(
    slug="inclusive-date-range",
    category="calendar",
    status="implementation_definition",
    sources=[
        ("phase-1/src/dewatacalendar/dsp.py", "implementation"),
        ("phase-1/docs/runbook/RANGE_LIMIT.md", "policy"),
        ("phase-1/src/dewatacalendar/tests/test_range_limit.py", "tests", "test_one_day_range_succeeds_and_items_has_length_one"),
    ],
    summary_id="Rentang inklusif start..end. end < start → HTTP 400. > 366 hari → HTTP 413 (lihat RANGE_LIMIT).",
    summary_en="Inclusive start..end range. end < start → HTTP 400. > 366 days → HTTP 413 (see RANGE_LIMIT).",
)

term(
    slug="ruleset",
    category="calendar",
    status="implementation_definition",
    sources=[
        ("phase-1/src/dewatacalendar/rulesets.py", "implementation"),
        ("phase-1/conformance/STATUS.json", "policy"),
        ("phase-1/docs/runbook/RULESET_VERSIONING.md", "policy"),
    ],
    summary_id="Versi aturan saat ini: pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0. Promosi aturan memerlukan sign-off adat (lihat SIGNOFF.md).",
    summary_en="Current ruleset version: pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0. Promotion requires customary sign-off (see SIGNOFF.md).",
)

term(
    slug="calendar-engine",
    category="calendar",
    status="implementation_definition",
    sources=[
        ("phase-1/src/dewatacalendar/api.py", "implementation"),
        ("phase-1/src/dewatacalendar/pawukon.py", "implementation"),
        ("phase-1/src/dewatacalendar/saka.py", "implementation"),
        ("phase-1/src/dewatacalendar/wewaran.py", "implementation"),
        ("phase-1/src/dewatacalendar/rahinan.py", "implementation"),
    ],
    summary_id="Lapisan engine: pawukon → saka → wewaran → rahinan → compose_day. Setiap layer adalah modular dan tidak boleh merujuk layer di atasnya.",
    summary_en="Engine layers: pawukon → saka → wewaran → rahinan → compose_day. Each layer is modular and must not reference a higher layer.",
)

term(
    slug="calendar-conversion",
    category="calendar",
    status="implementation_definition",
    sources=[
        ("phase-1/src/dewatacalendar/api.py", "implementation"),
    ],
    summary_id="Fungsi compose_day(date) di API engine menggabungkan semua layer menjadi satu CalendarDay JSON.",
    summary_en="compose_day(date) in the engine's API combines all layers into a single CalendarDay JSON object.",
)

term(
    slug="wewaran",
    category="calendar",
    status="implementation_definition",
    sources=[
        ("phase-1/src/dewatacalendar/wewaran.py", "implementation"),
        ("phase-1/src/dewatacalendar/i18n.py", "implementation"),
    ],
    summary_id="10 siklus paralel (Eka..Dasa Wara) yang masing-masing mengeluarkan satu nilai per hari.",
    summary_en="10 parallel cycles (Eka..Dasa Wara), each emitting one value per day.",
)


# --- Wewaran per-cycle records (10 + Urip + Jejepan = 12) ---

WEWARAN_DETAILS = [
    ("ekawara", "satu 'sifat' (Eka Wara); boolean presence",
     "one 'sifat' (Eka Wara); boolean presence in engine"),
    ("dwiwara", "dua nilai paralel, jarang ada di kalender rumah",
     "two values running in parallel"),
    ("triwara", "tiga nilai (Pasah/Beteng/Kajeng); rekonsiliasi sumber membangun dispute tetap",
     "three values (Pasah/Beteng/Kajeng); reconciliation is documented as a constant +1 mod 3 dispute"),
    ("caturwara", "empat nilai; memiliki kasus khusus pada hari ke-72/73 siklus",
     "four values; carries a special-case rule at cycle day 72/73"),
    ("pancawara", "lima nilai (Paing/Pon/Wage/Keliwon/Umanis); digunakan untuk identifikasi Buda Kliwon dll.",
     "five values (Paing/Pon/Wage/Keliwon/Umanis); used to identify Buda Kliwon etc."),
    ("sadwara", "enam nilai; siklus 6 hari",
     "six values; 6-day cycle"),
    ("saptawara", "tujuh hari (Redite..Saniscara); satu-satunya siklus yang sejajar dengan hari internasional.",
     "seven days (Redite..Saniscara); aligns with the international week."),
    ("astawara", "delapan nilai; kasus khusus disusun bersama Caturwara.",
     "eight values; special cases at cycle day 72/73."),
    ("sangawara", "sembilan nilai; kasus khusus siklus 125/210.",
     "nine values; special cases at cycle 125/210."),
    ("dasawara", "sepuluh nilai, dihitung dengan 'urip-10'.",
     "ten values, computed with the 'urip-10' magic table."),
    ("urip", "tabel nilai-nilai yang dipakai oleh Dasawara dan sebagai bobot Pancawara.",
     "magic number tables used by Dasawara and as Pancawara weights."),
    ("jejepan", "turunan 2-hari dari Saptawara, jarang dipakai engine.",
     "a 2-day derivative of Saptawara; rarely emitted by the engine."),
]

for slug, sid, sen in WEWARAN_DETAILS:
    term(
        slug=f"wewaran/{slug}",
        category="calendar",
        status="implementation_definition",
        sources=[
            ("phase-1/src/dewatacalendar/wewaran.py", "implementation"),
            ("phase-1/src/dewatacalendar/i18n.py", "implementation"),
        ],
        summary_id=sid,
        summary_en=sen,
    )


# --- Rahinan terms (12 emitted ids + named days) ---

RHINAN_IDS = [
    # (engine_id, summary_id, summary_en)  — engine_id is the Python
    # identifier in phase-1/src/dewatacalendar/rahinan.py
    ("buda_wage", "Buda + Wage", "Buda (Wednesday) + Wage (Pancawara index 2)"),
    ("buda_kliwon", "Buda + Keliwon", "Buda + Keliwon"),
    ("saniscara_umanis", "Saniscara + Umanis", "Saniscara + Umanis (Tumpek Kandang in some traditions)"),
    ("tumpek_landep", "Saniscara + Keliwon", "Saniscara + Keliwon (Tumpek Landep)"),
    ("anggara_kliwon", "Anggara + Keliwon", "Anggara + Keliwon (Anggara Kasih label)"),
    ("redite_paing", "Redite + Paing", "Redite (Sunday) + Paing"),
    ("purnama", "pada bulan purnama (Saka is_purnama)",
     "matches `saka.is_purnama` (full moon by lunar-tithi)"),
    ("tilem", "pada bulan mati (Saka is_tilem)",
     "matches `saka.is_tilem` (new moon by lunar-tithi)"),
    ("saraswati", "Wuku 21 (Watugunung) + Saniscara",
     "Wuku 21 (Watugunung) + Saniscara"),
    ("galungan", "Wuku 11 (Dungulan) + Buda + Keliwon",
     "Wuku 11 (Dungulan) + Buda + Keliwon"),
    ("kuningan", "Wuku 12 (Kuningan) + Saniscara + Keliwon",
     "Wuku 12 (Kuningan) + Saniscara + Keliwon"),
    ("nyepi", "Sasih 9 (Kesanga) + Tilem + Tithi 1",
     "Sasih 9 (Kesanga) + Tilem + lunar-tithi 1"),
]
for engine_id, sid, sen in RHINAN_IDS:
    slug = engine_id.replace('_', '-')
    term(
        slug=f"rahinan/{slug}",
        category="rahinan",
        status="implementation_definition",
        sources=[
            ("phase-1/src/dewatacalendar/rahinan.py", "implementation", f"id '{engine_id}'"),
            ("phase-1/src/dewatacalendar/i18n.py", "implementation", "RAHINAN_I18N"),
        ],
        summary_id=f"rahinan id engine '{engine_id}' terpicu ketika {sid}.",
        summary_en=f"engine rahinan id '{engine_id}' triggers when {sen}.",
    )

# Human-named rahinan days (visible concept, not engine id)
RHINAN_NAMED = [
    ("rahinan", "hari peringatan / observasi; umumnya terkait siklus Pawukon dan bulan Saka",
     "day of observance; typically tied to a Pawukon cycle and Saka lunar month",
     "phase-1/src/dewatacalendar/rahinan.py", "implementation"),
    ("purnama", "bulan purnama (observed over 1-2 hari lunar)",
     "full moon (engine emits 1-2 day window)",
     "phase-1/src/dewatacalendar/saka.py", "implementation"),
    ("tilem", "bulan mati (observed over 1-2 hari lunar)",
     "new moon (engine emits 1-2 day window)",
     "phase-1/src/dewatacalendar/saka.py", "implementation"),
    ("tumpek", "pola siklus saptawara + pancawara (Saniscara Umanis / Saniscara Keliwon / Redite Paing)",
     "saptawara+pancawara pattern (Saniscara Umanis / Saniscara Keliwon / Redite Paing)",
     "phase-1/src/dewatacalendar/rahinan.py", "implementation"),
    ("kajeng-kliwon", "Kajeng = Siklus 2 hari (Menga/Pepet); dengan Keliwon = Kajeng Kliwon",
     "Kajeng = 2-day cycle (Menga/Pepet); Kliwon combo = Kajeng Kliwon (informational only — engine tidak mengeluarkannya)",
     "phase-1/src/dewatacalendar/rahinan.py", "implementation"),
    ("anggara-kasih", "Selasa (Anggara) + Keliwon (Pancawara); 'hari kasih sayang'",
     "Tuesday (Anggara) + Keliwon (Pancawara)",
     "phase-1/src/dewatacalendar/rahinan.py", "implementation"),
    ("buda-kliwon", "Rabu (Buda) + Keliwon (Pancawara); 'hari keramat'",
     "Wednesday (Buda) + Keliwon (Pancawara); often translated 'sacred day'",
     "phase-1/src/dewatacalendar/rahinan.py", "implementation"),
    ("buda-cemeng", "Rabu Wage; 'Buda Cemeng' (Pancawara Wage); engine tidak mengeluarkannya",
     "Wednesday Wage (Pancawara); engine does not currently emit Buda Cemeng as a separate id — included here so the term page is reserved",
     "phase-1/src/dewatacalendar/rahinan.py", "implementation"),
]
for slug, sid, sen, src_path, src_role in RHINAN_NAMED:
    real_slug = slug  # this slug has no slash; pythagorean
    # The current page directory is `docs/<lang>/rahinan/`, basename
    # is the slug verbatim.
    is_engine_id = "/" in slug  # safety: RHINAN_NAMED never has slashes
    term(
        slug=f"rahinan/{real_slug}",
        category="rahinan",
        status="implementation_definition" if not is_engine_id and real_slug != "rahinan" else "informational",
        sources=[(src_path, src_role)],
        summary_id=sid,
        summary_en=sen,
    )


# --- Governance terms (13) ---

GOVERNANCE = [
    ("adat", "verified_source",
     "Keseluruhan hukum dan kebiasaan adat Bali; istilah payung untuk lembaga, peran, dan prosedur.",
     "umbrella term for Balinese customary law, institutions, roles, and procedures.",
     [("README_ID.md", "policy"), ("README_BAL.md", "policy")]),
    ("banjar", "verified_source",
     "Lembaga adat komunitas terkecil, biasanya satu desa.",
     "smallest customary community, usually one village.",
     [("ARCHITECTURE.md", "policy"), ("README_ID.md", "policy")]),
    ("desa-adat", "verified_source",
     "Lembaga administratif tertinggi untuk adat Bali; kolektif desa.",
     "highest administrative customary body; the village-as-a-whole collective.",
     [("ARCHITECTURE.md", "policy")]),
    ("desa-dinas", "verified_source",
     "Lembaga administratif sipil yang terpisah dari desa adat.",
     "civil administrative body, distinct from desa adat.",
     [("README_ID.md", "policy")]),
    ("pura", "verified_source",
     "Tempat ibadah Hindu Bali; piodalan (ulang tahun pura) adalah salah satu entry utama dewata.org.",
     "Balinese Hindu temple; piodalan (temple anniversary) is one of the main entry types of dewata.org.",
     [("README_ID.md", "policy"), ("README_BAL.md", "policy")]),
    ("pemangku", "verified_source",
     "Pemimpin upacara pura (pengelola ritus).",
     "temple priest; ritual officer of a pura.",
     [("README_ID.md", "policy"), ("README_EN.md", "policy")]),
    ("bendesa", "verified_source",
     "Pemimpin adat desa adat.",
     "head of a desa adat.",
     [("README_ID.md", "policy")]),
    ("klian-adat", "verified_source",
     "Pemimpin adat banjar.",
     "head of a banjar.",
     [("README_ID.md", "policy")]),
    ("pecalang", "verified_source",
     "Penjaga keamanan upacara adat Bali.",
     "traditional ceremonial security officer.",
     [("README_ID.md", "policy")]),
    ("customary-authority", "verified_source",
     "Seseorang atau lembaga yang memiliki otoritas adat (mis. bendesa, pemangku Keramas, klian adat banjar).",
     "an individual or institution with customary authority (e.g. bendesa, pemangku Keramas, klian adat of a known banjar).",
     [("phase-1/docs/runbook/SIGNOFF.md", "policy")]),
    ("customary-sign-off", "verified_source",
     "Catatan dalam SIGNOFF.md; entri yang ditandatangani oleh customary authority.",
     "entry in SIGNOFF.md; a sign-off recorded by a customary authority.",
     [("phase-1/docs/runbook/SIGNOFF.md", "policy")]),
    ("jurisdiction", "informational",
     "Wilayah adat dari sebuah lembaga atau peran adat tertentu.",
     "geographic/customary scope of an institution or role.",
     [("phase-1/docs/runbook/SIGNOFF.md", "policy"), ("README_ID.md", "policy")]),
    ("attestation", "informational",
     "Pernyataan oleh saksi (biasanya customary authority) bahwa sebuah pernyataan adalah benar.",
     "statement by a witness (typically a customary authority) that a claim holds.",
     [("phase-1/docs/runbook/SIGNOFF.md", "policy")]),
]
for slug, status, sid, sen, srcs in GOVERNANCE:
    term(
        slug=f"governance/{slug}",
        category="governance",
        status=status,
        sources=srcs,
        summary_id=sid,
        summary_en=sen,
    )


# --- Evidence terms (18) ---

EVIDENCE = [
    ("evidence", "verified_source",
     "Catatan pendukung untuk klaim kalender atau aturan.",
     "supporting record for a calendar or ruleset claim.",
     [("phase-1/conformance/STATUS.json", "policy")]),
    ("provenance", "verified_source",
     "Catatan asal sebuah artefak (path repo, hash, tanggal akses, dll).",
     "origin record of an artifact (repo path, hash, access date, …).",
     [("phase-1/docs/PROTOCOL.md", "policy", "§2.1 / §2.4"),
      ("phase-1/evidence/README.md", "policy")]),
    ("corpus", "verified_source",
     "Kumpulan data referensi (tanggal + nilai) yang dipakai untuk conformance.",
     "reference dataset (date + values) used for conformance.",
     [("phase-1/conformance/STATUS.json", "policy")]),
    ("conformance-corpus", "verified_source",
     "Corpus yang disimpan di `phase-1/conformance/published/` (lihat STATUS.json schema).",
     "corpus stored under `phase-1/conformance/published/` (see STATUS.json schema).",
     [("phase-1/conformance/STATUS.json", "policy")]),
    ("verification-status", "verified_source",
     "Sumbu ortho-1 dari STATUS.json: UNVERIFIED | VERIFIED.",
     "first orthogonal axis of STATUS.json: UNVERIFIED | VERIFIED.",
     [("phase-1/conformance/STATUS.json", "policy")]),
    ("reference-eligibility", "verified_source",
     "Sumbu ortho-2 dari STATUS.json: INELIGIBLE | ELIGIBLE.",
     "second orthogonal axis of STATUS.json: INELIGIBLE | ELIGIBLE.",
     [("phase-1/conformance/STATUS.json", "policy")]),
    ("eligible-claim", "verified_source",
     "Klaim spesifik yang dapat menggunakan corpus yang eligible.",
     "a specific claim that may use an eligible corpus.",
     [("phase-1/conformance/STATUS.json", "policy", "eligible_claim_ids")]),
    ("implementation-observation", "verified_source",
     "Apa yang dapat diamati engine untuk tanggal tertentu.",
     "what the engine can be observed to produce for a given date.",
     [("phase-1/src/dewatacalendar/api.py", "implementation")]),
    ("dispute", "verified_source",
     "Catatan terbuka di disputes.json dengan lima field wajib per PROTOCOL §3.3.",
     "an open record in disputes.json with the five required fields per PROTOCOL §3.3.",
     [("phase-1/docs/runbook/disputes.json", "policy"),
      ("docs/PROTOCOL.md", "policy", "§3 dispute classes"),
      ("docs/runbook/DISPUTE_REVIEW_PROTOCOL.md", "policy")]),
    ("blocking-dispute", "verified_source",
     "Dispute yang tingkatannya 'blocking' (lihat PROTOCOL §3.4).",
     "dispute marked 'blocking' (see PROTOCOL §3.4).",
     [("phase-1/docs/runbook/disputes.json", "policy")]),
    ("resolution", "verified_source",
     "Hasil yang mengakhiri sebuah dispute (resolved | superseded).",
     "outcome closing a dispute (resolved | superseded).",
     [("docs/PROTOCOL.md", "policy", "§3.2")]),
    ("accepted-rule", "verified_source",
     "Status yang menandakan aturan diterima oleh customary authority. Belum ada satupun yang tercatat di v0.1.",
     "state where a rule is accepted by customary authority. None recorded for v0.1.",
     [("phase-1/docs/runbook/SIGNOFF.md", "policy", "(none recorded for v0.1)")]),
    ("candidate-ruleset", "verified_source",
     "Aturan yang siap dianggap 'released' setelah sign-off. Sampai saat itu, ia tetap candidate.",
     "a ruleset ready for customary review; until then, it remains a candidate.",
     [("phase-1/docs/runbook/RULESET_VERSIONING.md", "policy")]),
    ("ruleset-promotion", "verified_source",
     "Promosi ruleset=dapat terjadi hanya setelah SIGNOFF. Saat ini gagal-tertutup (fail-closed).",
     "ruleset promotion only after SIGNOFF. Currently fail-closed.",
     [("phase-1/conformance/STATUS.json", "policy", "can_promote_ruleset_using")]),
    ("cultural-review", "informational",
     "Tinjauan oleh reviewer bukan-dewata yang akrab adat Bali (lihat CONTRIBUTING.md).",
     "review by a non-dewata reviewer with customary fluency (see CONTRIBUTING.md).",
     [("CONTRIBUTING.md", "policy")]),
    ("bibliographic-review", "informational",
     "Tinjauan tentang identitas dan status sumber (lihat PROTOCOL §3.1).",
     "review of source identity and status (see PROTOCOL §3.1).",
     [("docs/PROTOCOL.md", "policy", "§3.1 bibliographic")]),
    ("raw-comparison", "verified_source",
     "Perbandingan dua implementasi pada keluaran rentang tanggal tanpa normalisasi.",
     "comparison of two implementations on a date range without normalisation.",
     [("phase-1/docs/audit/CROSS_VALIDATION_full_range_1900_2099_2026-09-16.md", "audit")]),
    ("normalised-comparison", "verified_source",
     "Perbandingan setelah normalisasi fase, memeriksa bentuk siklus tanpa offset.",
     "comparison after phase normalisation, checking cycle shape without offsets.",
     [("phase-1/docs/audit/CROSS_VALIDATION_full_range_1900_2099_2026-09-16.md", "audit")]),
    ("phase-normalisation", "verified_source",
     "Proses pengurangan offset fase konstan untuk membandingkan implementasi yang berbeda epoch.",
     "removal of a constant phase offset to compare implementations on different epoch conventions.",
     [("phase-1/docs/audit/two-axis-analysis.md", "audit"),
      ("phase-1/docs/audit/CROSS_VALIDATION_full_range_1900_2099_2026-09-16.md", "audit")]),
]
for slug, status, sid, sen, srcs in EVIDENCE:
    term(
        slug=f"evidence/{slug}",
        category="evidence",
        status=status,
        sources=srcs,
        summary_id=sid,
        summary_en=sen,
    )


# --- Platform terms (24) ---

PLATFORM = [
    ("dewata", "informational",
     "Proyek keseluruhan; nama protokol untuk merekam upacara adat.",
     "the overall project; a protocol name for recording Balinese ceremonies.",
     [("README_EN.md", "policy"), ("ARCHITECTURE.md", "policy")]),
    ("dsp", "implementation_definition",
     "Dewata Spatial Protocol; permukaan publik HTTP untuk engine kalender.",
     "Dewata Spatial Protocol; the public HTTP surface for the calendar engine.",
     [("phase-1/src/dewatacalendar/dsp.py", "implementation"),
      ("phase-1/src/api/main.py", "implementation")]),
    ("public-api", "implementation_definition",
     "Antarmuka publik engine di `api.dewata.org`. Saat ini hanya DSP.",
     "public interface of the engine at `api.dewata.org`. Currently DSP only.",
     [("phase-1/src/api/main.py", "implementation")]),
    ("api-endpoint", "implementation_definition",
     "Rute HTTP yang didefinisikan DSP: `/dsp/v0.1/calendar/{date, range, ruleset}`.",
     "HTTP route defined by DSP: `/dsp/v0.1/calendar/{date, range, ruleset}`.",
     [("phase-1/src/dewatacalendar/dsp.py", "implementation")]),
    ("ruleset-version", "implementation_definition",
     "String `pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0` (saat ini).",
     "string `pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0` (current).",
     [("phase-1/src/dewatacalendar/rulesets.py", "implementation")]),
    ("computed", "verified_source",
     "Tingkat visibilitas untuk record yang dihitung engine dan belum dilihat manusia.",
     "visibility level for a record computed by the engine and not seen by a human.",
     [("README_BAL.md", "policy", 'diproduksi olih mesin / "computed"')]),
    ("registered", "verified_source",
     "Tingkat visibilitas untuk record yang didaftarkan oleh aktor.",
     "visibility level for a record registered by an actor.",
     [("README_BAL.md", "policy", 'kacatet olih aktor / "registered"')]),
    ("predicted", "verified_source",
     "Tingkat visibilitas untuk record yang diprediksi engine akan berlaku.",
     "visibility level for a record the engine predicts to apply.",
     [("README_BAL.md", "policy", 'kaarepin / "predicted"')]),
    ("verified", "verified_source",
     "Tingkat visibilitas untuk record yang sudah diverifikasi oleh sumber terpisah.",
     "visibility level for a record verified by an independent source.",
     [("README_BAL.md", "policy", 'kawedarana / "verified"')]),
    ("visibility-tier", "implementation_definition",
     "Pembedaan 4-tier: public / banjar / desa adat / restricted / private.",
     "4-tier distinction: public / banjar / desa adat / restricted / private.",
     [("phase-1/src/dewatacalendar/dsp.py", "implementation"),
      ("ARCHITECTURE.md", "policy")]),
    ("public", "implementation_definition",
     "Tier visibilitas paling terbuka. Semua record siap-publik ada di sini.",
     "openest visibility tier. All ready-to-publish records sit here.",
     [("phase-1/src/api/main.py", "implementation")]),
    ("banjar-visibility", "implementation_definition",
     "Tier visibilitas yang menampilkan record ke banjar terkait saja.",
     "visibility tier that shows records to the relevant banjar only.",
     [("ARCHITECTURE.md", "policy")]),
    ("desa-adat-visibility", "implementation_definition",
     "Tier visibilitas yang menampilkan record ke desa adat terkait.",
     "visibility tier that shows records to the relevant desa adat.",
     [("ARCHITECTURE.md", "policy")]),
    ("restricted", "implementation_definition",
     "Tier visibilitas dengan akses terbatas (aktor tertentu saja).",
     "visibility tier with restricted access (specific actors only).",
     [("ARCHITECTURE.md", "policy")]),
    ("private", "implementation_definition",
     "Tier visibilitas tertutup, hanya untuk owner record.",
     "visibility tier closed to everyone but the record owner.",
     [("ARCHITECTURE.md", "policy")]),
    ("mirror", "verified_source",
     "Salinan repo yang terpisah, biasanya dimiliki oleh banjar atau desa adat, untuk bukti tahan sensor.",
     "an independent copy of the repository, usually held by a banjar or desa adat, for censorship-resistant evidence.",
     [("README_ID.md", "policy", "mirror-redundancy at release time"),
      ("phase-1/docs/runbook/RULESET_VERSIONING.md", "policy")]),
    ("signed-snapshot", "verified_source",
     "Snapshot isi repo yang ditandatangani dengan kunci AGE.",
     "snapshot of repo contents signed with an AGE key.",
     [("phase-1/src/dewatacalendar/runbook.py", "implementation"),
      ("phase-1/docs/runbook/RULESET_VERSIONING.md", "policy")]),
    ("release-manifest", "verified_source",
     "MANIFEST.txt yang mendaftar path + sha256 untuk sebuah rilis.",
     "MANIFEST.txt listing path + sha256 for a release.",
     [("phase-1/docs/runbook/RULESET_VERSIONING.md", "policy")]),
    ("checksum-sha256", "verified_source",
     "Hash SHA-256 yang dipakai untuk verifikasi integritas artefak.",
     "SHA-256 hash used for artifact integrity verification.",
     [("phase-1/evidence/cross-validation/1900-2099/SHA256SUMS", "evidence"),
      ("phase-1/evidence/references/balinese-wariga-sources/edysantosa-sakacalendar/LICENSE.LGPL-2.1", "evidence")]),
    ("json", "informational",
     "Format pertukaran data untuk DSP (dan kebanyakan artefak engine).",
     "data format for DSP (and most engine artifacts).",
     [("phase-1/src/dewatacalendar/dsp.py", "implementation")]),
    ("jsonl", "informational",
     "Format baris-per-record untuk dipakai DSP saat fmt=jsonl.",
     "line-per-record format used by DSP when fmt=jsonl.",
     [("phase-1/src/dewatacalendar/dsp.py", "implementation")]),
    ("immutable-artifact", "verified_source",
     "Artefak yang tidak boleh dimodifikasi; lihat RULESET_VERSIONING.md inv-5.",
     "an artifact that must not be modified; see RULESET_VERSIONING.md inv-5.",
     [("phase-1/docs/runbook/RULESET_VERSIONING.md", "policy", "invariant 5")]),
    ("candidate-release", "verified_source",
     "Rilis yang menunggu customary sign-off dan peninjauan komunitas.",
     "release pending customary sign-off and community review.",
     [("phase-1/docs/runbook/RULESET_VERSIONING.md", "policy")]),
    ("production-release", "verified_source",
     "Rilis yang ditandatangani penuh dan dipublikasikan; saat ini repository belum punya satu.",
     "fully-signed release that is publicly deployed; the repository has none yet.",
     [("phase-1/docs/runbook/RULESET_VERSIONING.md", "policy")]),
]
for slug, status, sid, sen, srcs in PLATFORM:
    term(
        slug=f"platform/{slug}",
        category="platform",
        status=status,
        sources=srcs,
        summary_id=sid,
        summary_en=sen,
    )


# ───────────────────────────── page emitters ──────────────────────────


def front_matter(term: dict, slug: str, lang: str) -> dict:
    # canonical_slug is the URL-safe basename, not the path.
    # the directory contains a single file per term, named after
    # the slug; the category is encoded separately.
    slug_basename = slug.split('/')[-1]
    # Title for the page: the basename, with hyphens replaced by
    # spaces and title-cased. Avoid carrying the section prefix
    # into the rendered heading.
    title_basename = slug_basename.replace('-', ' ').title()
    # language_variants.spelling should be the bare term name, not a
    # path. the same applies to canonical_term.
    spelling = slug_basename
    return {
        "canonical_term": spelling,
        "canonical_slug": slug_basename,
        "category": term["category"],
        "language_variants": {
            "ban": {"status": "pending_customary_review",
                    "spelling": "(no verified Bahasa Bali spelling)",
                    "note": "Bahasa Bali spelling is not in phase-1/src/dewatacalendar/i18n.py or README_BAL.md for this term; id/en body carries the meaning"},
            "id": {"status": term["status"],
                    "spelling": spelling},
            "en": {"status": term["status"],
                    "spelling": spelling},
        },
        "alternative_spellings": [spelling],
        "short_definition": term["summary_id"] if lang == "id" else term["summary_en"],
        "detailed_explanation": (
            "(definition body intentionally short — see source citations; "
            "expansion requires customary sign-off or new evidence)"
        ),
        "dewata_specific_meaning": (
            "definition carried from the source citations; this page does not "
            "introduce new authority"
        ),
        "affects": _affects_for(term["category"]),
        "examples": [],
        "related_terms": [],
        "source_citations": _format_sources(term["sources"]),
        "evidence_status": term["status"],
        "dispute_ids": [],
        "customary_review_status": "pending_customary_review",
        "translation_review_status": {
            "ban": "pending_customary_review",
            "id": "needs_review",
            "en": "needs_review",
        },
        "ruleset_version_relevance": "pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0",
        "last_reviewed": "2026-09-17",
        "reviewer": "[[ai-trail]]/wiki-foundation-20260917",
        "status": term["status"],
    }


def _format_sources(raw_sources: list) -> list[dict]:
    """convert the generator's `sources` tuples (path, role, [quote])
    into the structured source_citations records required by the
    schema. Each citation has `path` and `role`; an optional `quote`
    is included when provided."""
    out = []
    for s in raw_sources:
        # tuple shapes we accept: (path, role) or (path, role, quote)
        if len(s) >= 3 and s[2]:
            out.append({"path": s[0], "role": s[1], "quote": s[2]})
        else:
            out.append({"path": s[0], "role": s[1]})
    return out


def _affects_for(category: str) -> list[str]:
    if category == "calendar":
        return ["calculation", "display-only"]
    if category == "rahinan":
        return ["calculation"]
    if category == "governance":
        return ["governance"]
    if category == "evidence":
        return ["evidence"]
    if category == "platform":
        return ["display-only"]
    return ["informational"]


def write_lang(page_dir: Path, slug: str, term: dict, lang: str,
               body_extra: str = ""):
    page_dir.mkdir(parents=True, exist_ok=True)
    # The slug may or may not have a section prefix. For page-layout
    # uniformity, any term belonging to a category gets placed under
    # `docs/<lang>/<category>/<slug-as-name>.md`. MkDocs's
    # use_directory_urls: true generates URLs from this.
    category = term.get("category", "misc")
    parts = slug.split('/', 1)
    if len(parts) == 2:
        section, basename = parts
        out = (page_dir / section / (basename + '.md'))
    else:
        # no explicit section in the slug; use the term's category
        out = (page_dir / category / (slug + '.md'))
    out.parent.mkdir(parents=True, exist_ok=True)
    fm = front_matter(term, slug, lang)
    import yaml as _yaml
    fm_text = _yaml.safe_dump(fm, sort_keys=False, allow_unicode=True,
                             default_flow_style=False)
    body_lang = term["summary_id"] if lang == "id" else term["summary_en"]
    slug_basename = slug.split('/')[-1]
    title = slug_basename.replace('-', ' ').title()
    md = f"---\n{fm_text}---\n\n# {title}\n\n{body_lang}\n\n{body_extra}\n"
    out.write_text(md, encoding="utf-8")
    return out


def write_ban_stub(page_dir: Path, slug: str, term: dict | None = None):
    """the Bahasa Bali page is a stub that points readers to the
    id/en bodies for the actual content, with status
    `pending_customary_review`. We do NOT invent Balinese text."""
    page_dir.mkdir(parents=True, exist_ok=True)
    category = (term or {}).get("category", "misc")
    parts = slug.split('/', 1)
    if len(parts) == 2:
        section, basename = parts
        out = (page_dir / section / (basename + '.md'))
    else:
        out = (page_dir / category / (slug + '.md'))
    out.parent.mkdir(parents=True, exist_ok=True)
    body = f"""---
status: pending_customary_review
translation_review_status:
  ban: pending_customary_review
  id: needs_review
  en: needs_review
last_reviewed: 2026-09-17
---

# /ban stub untuk {slug}

> **Status: pending_customary_review.** Halaman Bahasa Bali untuk
> istilah ini belum dapat kami tulis tanpa bukti kebiasaan yang
> tercatat. ejaan Bahasa Bali yang dipakai di proyek dewata.org
> berasal dari `phase-1/src/dewatacalendar/i18n.py` (lihat tabel i18n).
> untuk istilah ini, kami belum memiliki ejaan dari sana; halaman
> Bahasa Indonesia ([/id/{slug}](/id/{slug}))
> dan Bahasa Inggris ([/en/{slug}](/en/{slug}))
> adalah sumber penjelasan sampai tinjauan kebiasaan tersedia.
"""
    out.write_text(body, encoding="utf-8")
    return out


def main():
    n_ban = n_id = n_en = 0
    for t in TERMS:
        slug = t["slug"]
        n_id += 1
        write_lang(DOCS / "id", slug, t, "id")
    for t in TERMS:
        slug = t["slug"]
        n_en += 1
        write_lang(DOCS / "en", slug, t, "en")
    for t in TERMS:
        slug = t["slug"]
        n_ban += 1
        write_ban_stub(DOCS / "ban", slug, t)
    print(f"emitted {n_ban} ban / {n_id} id / {n_en} en term pages")


if __name__ == "__main__":
    main()
