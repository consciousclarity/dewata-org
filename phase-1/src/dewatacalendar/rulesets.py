"""ruleset version lock + metadata.

The engine ships with ruleset v0.1, frozen. bumps require a new conformance
corpus pass and a new ruleset id.
"""

from __future__ import annotations

RULESET_VERSION = "pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0"

# A separate identity for development artifacts that change observable
# output without bumping RULESET_VERSION. The corrections follow-up to
# PR #15 (Codex F2) separated these two so altered output cannot be
# published under an indistinguishable old ruleset identity.
#
# Per Codex review: "candidate_id changes when observable output
# diverges; do not publish altered output under an indistinguishable old
# identity." Every emitted CalendarDay and CLI artefact carries both
# the frozen RULESET_VERSION and the CANDIDATE_ID.
CANDIDATE_ID = "candidate-2026-09-20-strip-corrections-r2"

# Runtime-of-record list of rahinan ids the engine actually emits. Per
# Codex F3 the prior `named_days=24` claim and `purnama_counted=True` /
# `tilem_counted=True` flags contradicted what the engine emits. The
# IMPLEMENTED_RAHINAN_IDS list is asserted by a 210-day scan test
# (phase-1/tests/test_saka_strip.py).
IMPLEMENTED_RAHINAN_IDS: tuple[str, ...] = (
    "buda_wage",
    "buda_kliwon",
    "saniscara_umanis",
    "tumpek_landep",
    "anggara_kliwon",
    "redite_paing",
    "saraswati",
    "galungan",
    "kuningan",
)
# Rahinan ids whose emission depended on the removed lunar fields
# (`lunar_tithi`, `is_purnama`, `is_tilem`, `is_pangunalatri`) and which
# the engine therefore never emits. Each is a real Balinese cultural
# term; the wiki pages describing them are kept and marked as
# unimplemented surfaces.
UNIMPLEMENTED_RAHINAN_IDS: tuple[str, ...] = ("purnama", "tilem", "nyepi")

RULESET_METADATA: dict[str, dict[str, object]] = {
    "pawukon": {
        "version": "v0.4.1",
        "epoch": "1981-08-23",
        "epoch_pawukon_day": 1,
        "epoch_wuku_index": 1,  # Sinta on day 1
        "reference": "Dershowitz & Reingold, Calendrical Calculations, ch. 11",
    },
    "saka": {
        "version": "saka-bali-v0.2.3",
        "epoch_gregorian": "1979-03-29",
        "epoch_saka_year": 1901,
        # pangunalatri is NOT implemented. the 63-day cycle and its
        # `is_pangunalatri` flag were removed from saka.py as unvalidated
        # arithmetic: the flag was a plain modulo over days-since-epoch and
        # no eligible source establishes the period. the declared figure is
        # kept here as a record of what v0.2.3 claims -- deliberately not
        # under an active-parameter name -- so `dewatacalendar ruleset`
        # reports the claim and reports that the engine does not honor it.
        "pangunalatri_implemented": False,
        "pangunalatri_days_declared": 63,
        # nampih: what the engine computes and what the ruleset declared are
        # two different rules. the engine applies a single uncited
        # `saka_year % 3 == 0` test; the declared Tilem Kapitu rule has never
        # been implemented, `nampih_threshold_months` is read by no code, and
        # since the strip removed tilem from the engine the declared predicate
        # can no longer be evaluated at all. GAP_ANALYSIS_v1.0 Finding 3
        # classifies this gap as blocking for saka_sasih, Phase 0 and
        # ruleset_promotion, and notes the engine does not model the 1993-2003
        # nampih regimes that Peradnya/Rust/TS gate on.
        #
        # Per Codex review F4: the `nampih_rule_actual` field name falsely
        # endorsed what the loop computes as the cultural rule. Renamed to
        # `nampih_rule_observed` and the named intercalary sasih made
        # explicit (the loop names index 13 'Nampih Sada', not 'Nampih
        # Desta' as the prior comment claimed; the synthetic-year
        # accumulator inside `_sasih_index_at_offset` is independent of the
        # returned `saka_year`).
        "nampih_rule_observed": (
            "synthetic_year % 3 == 0 in loop -> 13 sasih, 395-day year; "
            "index 13 named 'Nampih Sada'; uncited; the engine does not "
            "endorse either Desta or Sada as the cultural convention"
        ),
        "nampih_rule_declared": "prevent Tilem Kapitu from falling in gregorian December",
        "nampih_declared_rule_implemented": False,
        "nampih_threshold_months_declared": (12, 11),
        "nampih_observed_sasih_index": 13,
        "nampih_observed_sasih_name": "Nampih Sada",
        "reference": "Igarashi bali saka calculation; Cunningham 1994",
        # Per Codex F1: public `saka_year` field is None because the
        # January-rollover arithmetic is not customary-validated. The
        # diagnostic field exposes the raw formula output for the harness
        # and dispute packet.
        "public_saka_year_returned": False,
        "saka_year_diagnostic_field": "saka_year_diagnostic_january_rollover",
    },
    "wewaran": {
        "version": "v0.3.0",
        "urip_5_day": (9, 7, 4, 8, 5),
        "urip_7_day": (5, 4, 3, 7, 8, 6, 9),
        "urip_10_day": (5, 2, 8, 6, 4, 7, 10, 3, 9, 1),
        "reference": "Wikipedia Pawukon, Dershowitz & Reingold",
    },
    "rahinan": {
        "version": "v0.2.0",
        # Per Codex F3: the prior `named_days=24` and
        # `purnama_counted=True` / `tilem_counted=True` contradicted what
        # the engine emits. `named_days` is now the runtime-of-record
        # count (len(IMPLEMENTED_RAHINAN_IDS)). The previously claimed
        # `purnama`/`tilem`/`nyepi` ids are tracked separately as
        # `*_counted=False` and `unimplemented_rahinan_ids`.
        "named_days": len(IMPLEMENTED_RAHINAN_IDS),
        "purnama_counted": False,
        "tilem_counted": False,
        "nyepi_counted": False,
        "implemented_rahinan_ids": list(IMPLEMENTED_RAHINAN_IDS),
        "unimplemented_rahinan_ids": list(UNIMPLEMENTED_RAHINAN_IDS),
        "reference": "Eiseman 1989, Bali handbook",
    },
}
