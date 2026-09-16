"""documentation-integrity regression tests.

These tests prevent specific contradictions from returning after
the 2026-09-16 documentation consistency pass:

- STATUS.schema.md must not contain obsolete v2 semantics
- STATUS.json must not claim "VERIFIED + ELIGIBLE" alone is sufficient
  for the reference gate (must also require explicit claim_id)
- STATUS.json must not claim "may_satisfy_validation_gate" or
  "may_be_described_as_ground_truth" as source-level booleans
- STATUS.json top-level policy must not contradict the executable
  implementation (must not claim the gate is "VERIFIED + ELIGIBLE"
  alone)
- STATUS.schema.md must not have "schema_version": "2.0"
- STATUS.json schema_version must be "3.0"
- evidence manifest must not present /tmp/refs/ as durable storage
  (only as transient retrieval space)

These tests are intentionally narrow and read-only; they only assert
absence of specific stale strings.
"""

import json
import re
from pathlib import Path

import pytest


CONFORMANCE = Path("/opt/dw-phase2/phase-1/conformance")
STATUS_JSON = CONFORMANCE / "STATUS.json"
STATUS_SCHEMA = CONFORMANCE / "STATUS.schema.md"

EVIDENCE_README = Path("/opt/dw-phase2/phase-1/evidence/README.md")
WARIGA_DIR = Path(
    "/opt/dw-phase2/phase-1/evidence/references/balinese-wariga-sources"
)
WARIGA_MANIFEST = WARIGA_DIR / "MANIFEST.md"


# obsolete v2 language that must NOT appear in STATUS.schema.md

OBSOLETE_V2_STRINGS = [
    # the four-gates-are-identical rule (must be replaced by the four
    # distinct gates with their own semantics)
    (
        '"can_satisfy_validation_gate": "verification_status == '
        "'VERIFIED' AND reference_eligibility == 'ELIGIBLE' "
        '(fail-closed otherwise)"'
    ),
    (
        '"can_promote_ruleset_using": "verification_status == '
        "'VERIFIED' AND reference_eligibility == 'ELIGIBLE'"
    ),
    (
        '"can_be_described_as_ground_truth": "verification_status == '
        "'VERIFIED' AND reference_eligibility == 'ELIGIBLE'"
    ),
    (
        '"can_be_silently_copied_to_authoritative_fixture": '
        "'verification_status == 'VERIFIED' AND reference_eligibility == "
        "'ELIGIBLE'"
    ),
]


def test_status_schema_md_no_obsolete_v2_gate_predicates():
    """STATUS.schema.md must not contain the obsolete v2 four-gates-
    are-identical rule. The four gates have distinct semantics."""
    text = STATUS_SCHEMA.read_text(encoding="utf-8")
    for obsolete in OBSOLETE_V2_STRINGS:
        assert obsolete not in text, (
            f"STATUS.schema.md contains obsolete v2 gate predicate: "
            f"{obsolete!r}"
        )


def test_status_schema_md_has_explicit_claim_scoped_rule():
    """STATUS.schema.md must document that the reference gate is
    claim-scoped: explicit claim_id is required; unscoped fails
    closed."""
    text = STATUS_SCHEMA.read_text(encoding="utf-8")
    # claim_id must appear as a required argument
    assert "claim_id" in text, (
        "STATUS.schema.md must document the claim_id requirement"
    )
    # the explicit fail-closed language for unscoped must appear
    assert "Unscoped" in text or "unscoped" in text, (
        "STATUS.schema.md must document that unscoped queries fail closed"
    )


def test_status_json_schema_version_is_3_0():
    """STATUS.json schema_version must be 3.0."""
    s = json.loads(STATUS_JSON.read_text(encoding="utf-8"))
    assert s["schema_version"] == "3.0", (
        f"STATUS.json schema_version is {s['schema_version']!r}, "
        f"expected '3.0'"
    )


def test_status_json_top_level_policy_not_misleading():
    """STATUS.json top-level policy must not claim the gate is
    VERIFIED + ELIGIBLE alone. The actual gate also requires an
    explicit matching claim_id in structured eligible_claim_ids."""
    s = json.loads(STATUS_JSON.read_text(encoding="utf-8"))
    policy = s["policy"]
    # the old single-axis assertion
    assert "The gate requires VERIFIED + ELIGIBLE" not in policy, (
        f"STATUS.json policy still says 'The gate requires "
        f"VERIFIED + ELIGIBLE': {policy!r}"
    )
    # the new policy must distinguish axes vs gate
    assert "claim_id" in policy, (
        f"STATUS.json policy must mention claim_id requirement"
    )


def test_status_json_no_source_level_validation_boolean():
    """STATUS.json must not contain the obsolete source-level
    may_satisfy_validation_gate boolean on any corpus entry."""
    s = json.loads(STATUS_JSON.read_text(encoding="utf-8"))
    for name, entry in s["corpora"].items():
        assert "may_satisfy_validation_gate" not in entry, (
            f"corpus {name!r} still has source-level "
            f"may_satisfy_validation_gate boolean"
        )
        assert "may_be_described_as_ground_truth" not in entry, (
            f"corpus {name!r} still has source-level "
            f"may_be_described_as_ground_truth boolean"
        )


def test_status_json_kemendikbud_licensing_is_not_open_content():
    """the Kemendikbud entry's reason must explicitly say it is NOT
    an open-content license and that explicit redistribution
    permission was not identified."""
    s = json.loads(STATUS_JSON.read_text(encoding="utf-8"))
    entry = s["corpora"]["wariga_kemendikbud_hindu_bs_kls_ix_2022"]
    reason = entry["reason"]
    assert "NOT Creative Commons" in reason or "NOT open-content" in reason, (
        f"Kemendikbud reason does not say 'NOT Creative Commons' or "
        f"'NOT open-content': {reason!r}"
    )
    assert "redistribution permission was not identified" in reason or \
           "explicit redistribution permission" in reason, (
        f"Kemendikbud reason does not say 'explicit redistribution "
        f"permission was not identified'"
    )


def test_status_json_babadbali_record_marks_external_url_not_tmp():
    """the babadbali.com entry's scope_limitations must include at
    least one string that marks the pages as publicly retrievable
    at the canonical URL, NOT as 'held at /tmp/refs/...'."""
    s = json.loads(STATUS_JSON.read_text(encoding="utf-8"))
    entry = s["corpora"]["wariga_babadbali_com"]
    # at least one scope_limitation must mention canonical URL or
    # publicly retrievable, AND no scope_limitation may reference
    # /tmp/refs/ as a durable storage location.
    has_canonical = False
    for limit in entry.get("scope_limitations", []):
        assert "/tmp/refs/" not in limit, (
            f"babadbali.com scope_limitations still references "
            f"/tmp/refs/: {limit!r}"
        )
        if "publicly retrievable" in limit or "canonical URL" in limit:
            has_canonical = True
    assert has_canonical, (
        f"babadbali.com scope_limitations must include at least one "
        f"mention of canonical URL or publicly retrievable"
    )


def test_evidence_readme_documents_tmp_refs_policy():
    """phase-1/evidence/README.md must document the /tmp/refs/ policy
    that /tmp/ is scratch space and /tmp/refs/ is not durable
    evidence storage."""
    text = EVIDENCE_README.read_text(encoding="utf-8")
    assert "scratch space" in text or "noncanonical" in text or "transient" in text, (
        f"phase-1/evidence/README.md must document the /tmp/refs/ "
        f"policy"
    )


def test_wariga_manifest_documents_tmp_refs_policy():
    """the Wariga manifest must document the /tmp/refs/ policy that
    /tmp/ is scratch space and /tmp/refs/ is not durable evidence
    storage."""
    text = WARIGA_MANIFEST.read_text(encoding="utf-8")
    assert "scratch space" in text or "noncanonical" in text or "transient" in text, (
        f"Wariga MANIFEST.md must document the /tmp/refs/ policy"
    )


def test_no_persistent_tmp_refs_assertions_in_permanent_artifacts():
    """permanent artifacts (STATUS.json, STATUS.schema.md, evidence
    README, Wariga MANIFEST, integration manifest) must not assert
    that /tmp/refs/ is the canonical evidence archive. /tmp/refs/
    may only be mentioned as transient/noncanonical.

    This test allows /tmp/refs/ mentions that are explicitly framed
    as transient (e.g. "transient retrieval copy was used",
    "noncanonical", "/tmp/ is scratch space only"). All other
    mentions are flagged.
    """
    permanent_paths = [
        "/opt/dw-phase2/phase-1/conformance/STATUS.json",
        "/opt/dw-phase2/phase-1/conformance/STATUS.schema.md",
        "/opt/dw-phase2/phase-1/evidence/README.md",
        "/opt/dw-phase2/phase-1/evidence/references/"
        "balinese-wariga-sources/MANIFEST.md",
        "/opt/dw-phase2/phase-1/docs/audit/"
        "INTEGRATION_GOVERNANCE_EVIDENCE_2026-09-16.md",
        "/opt/dw-phase2/phase-1/evidence/references/"
        "balinese-wariga-sources/kemendikbud-hindu-bs-kls-ix/"
        "minimum-evidence-quotes.md",
        "/opt/dw-phase2/phase-1/evidence/references/"
        "balinese-wariga-sources/kemendikbud-hindu-bs-kls-ix/"
        "pages-37-40-extracted.txt",
    ]
    transient_phrases = [
        "scratch space",
        "transient retrieval",
        "transient",
        "noncanonical",
        "transient retrieval copy",
        "policy",
        "/tmp/refs/ policy",
    ]
    for path in permanent_paths:
        if not Path(path).exists():
            continue
        text = Path(path).read_text(encoding="utf-8")
        # use lowercase comparison for transient phrases
        text_lower = text.lower()
        for line in text.splitlines():
            if "/tmp/refs" in line:
                # only allow if the line is explicitly framed as
                # transient/noncanonical/policy. also check the
                # previous line because policy documentation may
                # span multiple physical lines.
                idx = text.find(line)
                preceding = text[max(0, idx - 200):idx]
                context = (preceding + "\n" + line).lower()
                if not any(phrase in context for phrase in transient_phrases):
                    pytest.fail(
                        f"{path!r} contains /tmp/refs/ assertion that "
                        f"is not framed as transient/policy: {line!r}"
                    )


def test_status_schema_md_canonical_event_listing_mentions_all_four_gates():
    """STATUS.schema.md must list all four gates with their distinct
    semantics — not collapse them into a single VERIFIED + ELIGIBLE
    rule."""
    text = STATUS_SCHEMA.read_text(encoding="utf-8")
    # all four gates must appear with their explicit name
    for gate_name in [
        "can_satisfy_validation_gate",
        "can_promote_ruleset_using",
        "can_be_described_as_ground_truth",
        "can_be_silently_copied_to_authoritative_fixture",
    ]:
        assert gate_name in text, (
            f"STATUS.schema.md must document gate: {gate_name!r}"
        )
    # the four gates must each have explicit distinct semantics
    # described (not just a single VERIFIED + ELIGIBLE rule)
    # the schema describes promotion/ground-truth/fixture-copying as
    # returning False unconditionally (case-insensitive)
    assert "returns false unconditionally" in text.lower(), (
        "STATUS.schema.md must document that promotion, ground-truth, "
        "and fixture-copying all return False unconditionally"
    )


def test_status_schema_md_no_stale_top_level_example_showing_v2_fields():
    """the STATUS.schema.md example for a corpus entry must NOT show
    obsolete fields like may_satisfy_validation_gate or
    may_be_described_as_ground_truth."""
    text = STATUS_SCHEMA.read_text(encoding="utf-8")
    # find the example block (between ```json and ```)
    import re
    examples = re.findall(r"```json\n(.*?)\n```", text, re.DOTALL)
    for example in examples:
        # the example should not show these obsolete fields
        assert '"may_satisfy_validation_gate"' not in example, (
            f"STATUS.schema.md JSON example shows obsolete "
            f"may_satisfy_validation_gate"
        )
        assert '"may_be_described_as_ground_truth"' not in example, (
            f"STATUS.schema.md JSON example shows obsolete "
            f"may_be_described_as_ground_truth"
        )


def test_status_schema_md_top_level_example_shows_v3_0():
    """the STATUS.schema.md top-level example must show
    schema_version: 3.0."""
    text = STATUS_SCHEMA.read_text(encoding="utf-8")
    # find the top-level example (the one near the schema_version
    # discussion)
    assert '"schema_version": "3.0"' in text, (
        f"STATUS.schema.md must contain schema_version 3.0 example"
    )
    # and not v2.0
    assert '"schema_version": "2.0"' not in text, (
        f"STATUS.schema.md must not contain schema_version 2.0 example"
    )


def test_status_json_kemendikbud_licensing_is_correct_in_reason_field():
    """the Kemendikbud entry must NOT assert it IS an 'open-content'
    license — that statement is obsolete and contradicted by the
    2026-09-16 license verification.

    legitimate phrasing includes: 'NOT Creative Commons or any
    open-content license' or 'NOT open-content license' or
    'redistribution permission was not identified'. these are
    explicit negations of open-content status, not assertions of
    it.
    """
    import re
    s = json.loads(STATUS_JSON.read_text(encoding="utf-8"))
    entry = s["corpora"]["wariga_kemendikbud_hindu_bs_kls_ix_2022"]
    reason = entry["reason"]
    # the reason must explicitly negate open-content status
    assert "NOT" in reason and "open-content" in reason, (
        f"Kemendikbud reason must explicitly negate open-content "
        f"status: {reason!r}"
    )
    # find any "open-content license" NOT preceded by NOT within 50 chars
    matches = list(re.finditer(r"open-content license", reason))
    for m in matches:
        preceding = reason[max(0, m.start() - 50):m.start()]
        assert "NOT" in preceding[-50:] or "no " in preceding[-50:].lower(), (
            f"Kemendikbud reason has unnegated 'open-content license' "
            f"claim: {reason!r}"
        )
    # the reason must explicitly say 'redistribution permission was
    # not identified'
    assert "redistribution permission was not identified" in reason or \
           "explicit redistribution permission" in reason, (
        f"Kemendikbud reason must say 'redistribution permission was "
        f"not identified'"
    )


def test_status_schema_md_explains_legacy_attested_deprecation():
    """STATUS.schema.md must document the legacy CorpusStatus enum
    as deprecated and explicitly say ATTESTED must NEVER satisfy a
    modern gate."""
    text = STATUS_SCHEMA.read_text(encoding="utf-8")
    assert "deprecated" in text.lower() or "DEPRECATED" in text, (
        "STATUS.schema.md must document legacy enum deprecation"
    )
    assert "ATTESTED" in text, (
        "STATUS.schema.md must document ATTESTED"
    )
    assert "MUST NOT" in text or "must NEVER" in text, (
        "STATUS.schema.md must document explicit prohibition on legacy "
        "enum authorizing modern gates"
    )
