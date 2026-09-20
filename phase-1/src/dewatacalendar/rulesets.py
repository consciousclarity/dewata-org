"""ruleset version lock + metadata.

The engine ships with ruleset v0.1, frozen. bumps require a new conformance
corpus pass and a new ruleset id.
"""

from __future__ import annotations

RULESET_VERSION = "pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0"

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
        "nampih_rule_actual": "saka_year % 3 == 0 -> nampih Desta (13 sasih, 395-day year); uncited",
        "nampih_rule_declared": "prevent Tilem Kapitu from falling in gregorian December",
        "nampih_declared_rule_implemented": False,
        "nampih_threshold_months_declared": (12, 11),
        "reference": "Igarashi bali saka calculation; Cunningham 1994",
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
        "named_days": 24,
        "purnama_counted": True,
        "tilem_counted": True,
        "reference": "Eiseman 1989, Bali handbook",
    },
}
