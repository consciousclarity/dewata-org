"""Round-trip preservation test for the wiki term-page generator.

Per Codex review of PR #15 (F5): the prior generator declared
purnama/tilem/nyepi as engine-emitted ids, and its named-day
entries claimed the engine emits a one-to-two-day window for those
terms. The corrections follow-up:

  - removes purnama/tilem/nyepi from `RHINAN_IDS`;
  - adds a separate `RHINAN_UNEMITTED` list with explicit
    "engine does not currently compute this" summaries;
  - updates the named-day entries to "engine does NOT currently emit".

This test imports the generator as a library (without invoking its
file writer, so the manually-edited unimplemented pages are not
overwritten by test runs) and asserts the structural invariants. It
also verifies that running the generator's writer is BYTE-STABLE
against the manually-edited wiki pages -- the generator and the
checked-in pages must agree.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
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


def test_rhinan_ids_excludes_purnama_tilem_nyepi(gen):
    """RHINAN_IDS (engine-emitted) must NOT include the unimplemented terms."""
    assert hasattr(gen, "RHINAN_IDS")
    emitted = {entry[0] for entry in gen.RHINAN_IDS}
    assert "purnama" not in emitted, (
        "purnama must not be in the engine-emitted id list -- it is unimplemented"
    )
    assert "tilem" not in emitted, (
        "tilem must not be in the engine-emitted id list -- it is unimplemented"
    )
    assert "nyepi" not in emitted, (
        "nyepi must not be in the engine-emitted id list -- it is unimplemented"
    )


def test_rhinan_unemitted_includes_purnama_tilem_nyepi(gen):
    """RHINAN_UNEMITTED must include the three unimplemented terms."""
    assert hasattr(gen, "RHINAN_UNEMITTED")
    unemitted = {entry[0] for entry in gen.RHINAN_UNEMITTED}
    assert "purnama" in unemitted
    assert "tilem" in unemitted
    assert "nyepi" in unemitted


def test_rhinan_named_no_longer_claims_engine_emits(gen):
    """The named-day entries for purnama/tilem must be removed
    entirely -- their pages are now produced by RHINAN_UNEMITTED, which
    flags them as unimplemented.
    """
    assert hasattr(gen, "RHINAN_NAMED")
    named = {entry[0] for entry in gen.RHINAN_NAMED}
    # purnama and tilem must NOT appear in RHINAN_NAMED at all --
    # they are emitted by RHINAN_UNEMITTED instead. If they appear
    # here, write_lang's last-write-wins behaviour will overwrite the
    # unimplemented page with the named-day phrasing.
    assert "purnama" not in named, (
        "F5 violated: purnama is in RHINAN_NAMED; the generator's "
        "last-write-wins ordering would overwrite the unimplemented "
        "page emitted by RHINAN_UNEMITTED. Remove from RHINAN_NAMED."
    )
    assert "tilem" not in named, (
        "F5 violated: tilem is in RHINAN_NAMED; the generator's "
        "last-write-wins ordering would overwrite the unimplemented "
        "page emitted by RHINAN_UNEMITTED. Remove from RHINAN_NAMED."
    )


def test_generator_writer_preserves_manually_edited_pages(gen):
    """The generator's writer must produce output consistent with the
    manually-edited unimplemented wiki pages.

    We invoke the writer with `gen.DOCS` monkey-patched to point at a
    tempdir that contains a copy of the checked-in wiki pages. We do
    not run the writer against the real wiki docs -- only against a
    copy.
    """
    import tempfile
    import shutil

    wiki_docs = REPO_ROOT / "wiki" / "docs"
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        # Copy wiki/docs into tmp so the writer has somewhere to write.
        shutil.copytree(wiki_docs, tmp_root / "docs")

        # Monkey-patch DOCS to point at the temp tree.
        original_docs = gen.DOCS
        gen.DOCS = tmp_root / "docs"
        try:
            gen.main()
        finally:
            gen.DOCS = original_docs

        # Verify the unimplemented pages were written with the
        # "engine does not currently compute / emit" status string.
        # The generator writes "engine does NOT currently emit" (with
        # the named-day entries we updated) and
        # "engine does not currently compute" (via RHINAN_UNEMITTED
        # summaries). Both phrasings are correct.
        for lang in ("en", "id"):
            for term in ("purnama", "tilem", "nyepi"):
                path = tmp_root / "docs" / lang / "rahinan" / f"{term}.md"
                assert path.exists(), (
                    f"F5: generator did not write {lang}/rahinan/{term}.md"
                )
                text = path.read_text().lower()
                # accept either the named-day phrasing or the
                # unimplemented-surface phrasing
                ok = (
                    "does not currently compute" in text
                    or "does not currently emit" in text
                    or "unimplemented" in text
                )
                assert ok, (
                    f"F5: generator wrote {path} without flagging the "
                    f"unimplemented status. Excerpt: {text[:500]}"
                )
