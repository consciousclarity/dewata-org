"""Round-trip preservation tests for the wiki term-page generator (round 2).

What this test verifies (and what it does NOT):

  - VERIFIED: the manually-maintained pages for `purnama`, `tilem`,
    and `nyepi` (six files: en/rahinan/, id/rahinan/) are not
    overwritten when the writer runs. We compare the bytes of each
    file before and after the writer runs against a temp copy of
    wiki/docs. Any difference fails the test. This is the
    "smallest reliable approach" (Codex finding 3) -- the writer
    is forbidden from rewriting these pages.

  - VERIFIED: the writer's main() reports the skip count in its
    output, and the slug list is exposed as
    `MANUALLY_MAINTAINED_SLUGS` for callers to inspect.

  - VERIFIED: the writer still produces the engine-emitted pages
    (e.g. galungan, saraswati) with structured metadata. These pages
    are NOT manually maintained; the writer owns them.

  - NOT VERIFIED here: byte stability of non-maintained pages.
    Those pages may legitimately change when the writer is updated
    to emit different metadata. A separate test would be needed if
    we wanted to lock down their content too.

  - NOT VERIFIED here: that the generator and the manually-edited
    pages would produce identical output if the generator were
    extended to author the unimplemented surfaces. That is a future
    work item, not a current requirement.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GENERATOR = REPO_ROOT / "wiki" / "scripts" / "emit_term_pages.py"


@pytest.fixture(scope="module")
def gen():
    spec = importlib.util.spec_from_file_location("emit_term_pages", GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generator_loads(gen):
    assert hasattr(gen, "TERMS")
    assert isinstance(gen.TERMS, list)
    assert len(gen.TERMS) > 0


def test_manually_maintained_slugs_declared(gen):
    """The generator must declare which pages are off-limits to overwrite.

    Currently purnama, tilem, nyepi -- the unimplemented rahinan
    surfaces that were manually edited in the merged wiki.
    """
    assert hasattr(gen, "MANUALLY_MAINTAINED_SLUGS")
    expected = {"rahinan/purnama", "rahinan/tilem", "rahinan/nyepi"}
    assert set(gen.MANUALLY_MAINTAINED_SLUGS) == expected, (
        f"manually-maintained slug set must be {expected}; "
        f"got {set(gen.MANUALLY_MAINTAINED_SLUGS)}"
    )


def test_rhinan_ids_excludes_purnama_tilem_nyepi(gen):
    """RHINAN_IDS (engine-emitted) must NOT include the unimplemented terms."""
    assert hasattr(gen, "RHINAN_IDS")
    emitted = {entry[0] for entry in gen.RHINAN_IDS}
    assert "purnama" not in emitted
    assert "tilem" not in emitted
    assert "nyepi" not in emitted


def test_rhinan_unemitted_includes_purnama_tilem_nyepi(gen):
    """RHINAN_UNEMITTED must include the three unimplemented terms."""
    assert hasattr(gen, "RHINAN_UNEMITTED")
    unemitted = {entry[0] for entry in gen.RHINAN_UNEMITTED}
    assert "purnama" in unemitted
    assert "tilem" in unemitted
    assert "nyepi" in unemitted


def test_rhinan_named_no_longer_claims_engine_emits(gen):
    """The named-day entries for purnama/tilem must be removed."""
    assert hasattr(gen, "RHINAN_NAMED")
    named = {entry[0] for entry in gen.RHINAN_NAMED}
    assert "purnama" not in named
    assert "tilem" not in named


def test_writer_preserves_manually_maintained_pages_byte_for_byte(gen):
    """Round-trip preservation (round 2): the writer must NOT
    overwrite the manually-maintained pages. We compare bytes
    before and after the writer runs against a temp copy of
    wiki/docs. Any difference fails.

    This is the byte-stability guarantee Codex asked for: the
    manually-maintained pages retain their full content,
    structured fields, and front-matter metadata.
    """
    import shutil
    import tempfile

    wiki_docs = REPO_ROOT / "wiki" / "docs"
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        shutil.copytree(wiki_docs, tmp_root / "docs")

        # Snapshot the manually-maintained pages' bytes BEFORE the
        # writer runs. Use exact byte equality, not any substring
        # check -- this is the round-2 requirement.
        before_bytes: dict[Path, bytes] = {}
        for lang in ("en", "id"):
            for term in ("purnama", "tilem", "nyepi"):
                p = tmp_root / "docs" / lang / "rahinan" / f"{term}.md"
                assert p.exists(), (
                    f"manually-maintained page {p} must exist before "
                    f"writer runs"
                )
                before_bytes[p] = p.read_bytes()

        # Run the writer against the temp copy.
        original_docs = gen.DOCS
        gen.DOCS = tmp_root / "docs"
        try:
            gen.main()
        finally:
            gen.DOCS = original_docs

        # Compare bytes.
        for p, expected_bytes in before_bytes.items():
            actual_bytes = p.read_bytes()
            assert actual_bytes == expected_bytes, (
                f"manually-maintained page {p.name} was overwritten by "
                f"the writer. Expected {len(expected_bytes)} bytes; "
                f"got {len(actual_bytes)} bytes. First 200 bytes of diff:\n"
                f"  before: {expected_bytes[:200]!r}\n"
                f"  after:  {actual_bytes[:200]!r}"
            )


def test_writer_still_produces_engine_emitted_pages(gen):
    """Round-trip preservation (round 2): the writer still produces
    pages for the engine-emitted rahinan ids (e.g. galungan,
    saraswati) with structured metadata. These are NOT manually
    maintained; the generator owns them.
    """
    import shutil
    import tempfile

    wiki_docs = REPO_ROOT / "wiki" / "docs"
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        shutil.copytree(wiki_docs, tmp_root / "docs")
        original_docs = gen.DOCS
        gen.DOCS = tmp_root / "docs"
        try:
            gen.main()
        finally:
            gen.DOCS = original_docs

        # Engine-emitted pages exist in the temp tree.
        for lang in ("en", "id"):
            for term in ("galungan", "saraswati"):
                p = tmp_root / "docs" / lang / "rahinan" / f"{term}.md"
                assert p.exists(), (
                    f"writer should produce {p} (engine-emitted rahinan)"
                )
                text = p.read_text()
                # Has front matter (starts with ---).
                assert text.startswith("---\n")
                # Has the rahinan id in the body or front matter.
                assert "rahinan" in text.lower()


def test_writer_output_reports_skip_count(capsys, gen):
    """The writer's stdout must include the skip count so operators
    can verify pages were preserved at runtime, not just in tests.
    """
    import shutil
    import tempfile

    wiki_docs = REPO_ROOT / "wiki" / "docs"
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        shutil.copytree(wiki_docs, tmp_root / "docs")
        original_docs = gen.DOCS
        gen.DOCS = tmp_root / "docs"
        try:
            gen.main()
        finally:
            gen.DOCS = original_docs
        captured = capsys.readouterr()
        assert "manually-maintained" in captured.out, (
            f"writer stdout must mention manually-maintained skip "
            f"count; got {captured.out!r}"
        )
        assert "preserved" in captured.out, (
            f"writer stdout must say preserved; got {captured.out!r}"
        )


def test_manually_maintained_pages_have_structured_evidence(gen):
    """Round 2: the manually-maintained pages must carry the structured
    fields that the generator does not produce. Codex finding 3:
    "Mentioning dispute identifiers in prose is not sufficient." The
    pages must have `dispute_ids`, `customary_review_status`, source
    citations, and translation review status -- the structured
    evidence required for dispute routing.
    """
    import yaml

    wiki_docs = REPO_ROOT / "wiki" / "docs"
    expected_dispute_ids = {
        "DISPUTE-SASAH-KAPAT-KATIGA-BOUNDARY-2026-09",
        "DISPUTE-SASAH-JAVA-VS-PERADNYA-OFFSET",
        "DISPUTE-ENGINE-SASIH-INDEX-INVERSION",
    }
    for lang in ("en", "id"):
        for term in ("purnama", "tilem", "nyepi"):
            path = wiki_docs / lang / "rahinan" / f"{term}.md"
            assert path.exists(), (
                f"manually-maintained page missing: {path}"
            )
            text = path.read_text()
            fm = text.split("---", 2)[1]
            data = yaml.safe_load(fm)

            # 1. Structured dispute_ids must be present and equal to
            # the three open sasih_index_drift disputes.
            assert "dispute_ids" in data, (
                f"finding 3: {path} missing structured dispute_ids"
            )
            assert set(data["dispute_ids"]) == expected_dispute_ids, (
                f"finding 3: {path} dispute_ids must equal "
                f"{expected_dispute_ids}; got {set(data['dispute_ids'])}"
            )

            # 2. customary_review_status with status and note.
            assert "customary_review_status" in data, (
                f"finding 3: {path} missing customary_review_status"
            )
            crs = data["customary_review_status"]
            assert crs.get("status") == "pending_customary_review", (
                f"finding 3: {path} customary_review_status.status "
                f"should be pending_customary_review; got {crs.get('status')!r}"
            )
            assert crs.get("note"), (
                f"finding 3: {path} customary_review_status.note "
                f"must be a non-empty string"
            )

            # 3. source_citations pointing at real engine source files.
            citations = data.get("source_citations", [])
            assert citations, (
                f"finding 3: {path} missing source_citations"
            )
            for c in citations:
                assert "path" in c, (
                    f"finding 3: {path} source_citation missing path: {c!r}"
                )
                # Verify the cited path actually exists in the repo.
                cited = REPO_ROOT / c["path"]
                assert cited.exists(), (
                    f"finding 3: {path} cites {c['path']!r} which does "
                    f"not exist on disk"
                )

            # 4. translation_review_status with ban/id/en.
            trs = data.get("translation_review_status", {})
            for required_lang in ("ban", "id", "en"):
                assert required_lang in trs, (
                    f"finding 3: {path} translation_review_status "
                    f"missing {required_lang}"
                )

            # 5. short_definition explicitly marks unimplemented.
            short_def = data.get("short_definition", "")
            assert "unimplemented" in short_def.lower() or (
                "belum diimplementasikan" in short_def.lower()
            ), (
                f"finding 3: {path} short_definition must mark "
                f"unimplemented status"
            )


def test_manually_maintained_pages_match_en_and_id(gen):
    """Round 2: the same three terms must be manually maintained in
    BOTH en and id. The writer preserves both languages; the test
    enforces parity.
    """
    en_dir = REPO_ROOT / "wiki" / "docs" / "en" / "rahinan"
    id_dir = REPO_ROOT / "wiki" / "docs" / "id" / "rahinan"
    for term in ("purnama", "tilem", "nyepi"):
        assert (en_dir / f"{term}.md").exists(), (
            f"manually-maintained en page missing: {term}.md"
        )
        assert (id_dir / f"{term}.md").exists(), (
            f"manually-maintained id page missing: {term}.md"
        )
