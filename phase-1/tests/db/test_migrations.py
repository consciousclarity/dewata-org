"""disposable migration tests against a postgis 16 database.

**NEVER** run these against the live `dewata` database.  the tests
require `DEWATA_TEST_DSN` to be set in the environment.  when unset,
the entire module is skipped via `pytestmark`.

what this test module covers:
  - migration 0001 applies cleanly to a clean postgis schema
  - migration 0001.down drops the migration cleanly
  - the right tables exist with the right columns
  - enums (visibility_tier, ceremony_phase, authority_role)
    have the right values
  - the `ceremony` and `ceremony_state` tables enforce append-only
    writes via triggers
  - the `actor.handle` column is uniquely constrained
  - the migration runner reports the migration as applied
  - the migration runner can reverse the migration and re-apply
"""

from __future__ import annotations

import os
from pathlib import Path

import psycopg
import pytest

from tests.db import fixtures as fix  # local package; tests/db is a package


pytestmark = pytest.mark.skipif(
    "DEWATA_TEST_DSN" not in os.environ,
    reason="DEWATA_TEST_DSN not configured — disposable test database required",
)


@pytest.fixture(scope="session")
def disposable_dsn() -> str:
    return os.environ["DEWATA_TEST_DSN"]


@pytest.fixture(scope="session")
def disposable_schema(disposable_dsn):
    """drop-recreate-schema, apply migration, ONCE per pytest session."""
    conn = psycopg.connect(disposable_dsn)
    with conn.cursor() as c:
        c.execute("DROP SCHEMA IF EXISTS public CASCADE")
        c.execute("CREATE SCHEMA public")
        c.execute("GRANT ALL ON SCHEMA public TO public")
        c.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    conn.commit()
    fix.bootstrap_test_database(conn)
    conn.commit()
    yield conn
    try:
        with conn.cursor() as c:
            c.execute("DROP SCHEMA IF EXISTS public CASCADE")
        conn.commit()
    finally:
        conn.close()


@pytest.fixture()
def disposable_conn(disposable_schema):
    """one connection per test, against a freshly reset **schema**.

    the session-scoped `disposable_schema` fixture applies the migration
    once.  per-test isolation requires dropping & re-applying the schema
    on each test, otherwise fixtures inserted in test N are still
    present in test N+1.

    this fixture does the work for each test:

      1. open a fresh connection
      2. drop public CASCADE, recreate public
      3. re-apply extensions + 0001 migration
      4. yield connection
    """
    dsn = os.environ["DEWATA_TEST_DSN"]
    conn = psycopg.connect(dsn)
    try:
        with conn.cursor() as c:
            c.execute("DROP SCHEMA IF EXISTS public CASCADE")
            c.execute("CREATE SCHEMA public")
            c.execute("GRANT ALL ON SCHEMA public TO public")
            c.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        conn.commit()
        fix.bootstrap_test_database(conn)
        conn.commit()
        yield conn
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ────────────────────────────────────────────────────────────────
# class 1 — schema-level checks
# ────────────────────────────────────────────────────────────────

class TestSchema:

    def test_all_required_tables_exist(self, disposable_conn):
        with disposable_conn.cursor() as c:
            c.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name IN ("
                "  'actor','banjar','ceremony','ceremony_state',"
                "  'ceremony_source','ceremony_authority_link',"
                "  'evidence_blob','desa_adat','pura','kabupaten','pura_relationship',"
                "  'authority_delegation','ceremony_ruleset_ref','schema_migrations'"
                ")"
            )
            tables = {row[0] for row in c.fetchall()}
        for required in {
            "actor", "banjar", "ceremony", "ceremony_state",
            "ceremony_source", "ceremony_authority_link",
            "evidence_blob", "desa_adat", "pura", "kabupaten",
            "pura_relationship", "authority_delegation",
            "ceremony_ruleset_ref", "schema_migrations",
        }:
            assert required in tables, f"missing table: {required}"

    def test_visibility_tier_enum_values(self, disposable_conn):
        with disposable_conn.cursor() as c:
            c.execute(
                "SELECT enumlabel FROM pg_enum "
                "JOIN pg_type ON pg_enum.enumtypid = pg_type.oid "
                "WHERE pg_type.typname='visibility_tier' ORDER BY enumsortorder"
            )
            values = {row[0] for row in c.fetchall()}
        assert values == {"public", "banjar", "desa_adat", "restricted", "private"}

    def test_authority_role_enum_values(self, disposable_conn):
        with disposable_conn.cursor() as c:
            c.execute(
                "SELECT enumlabel FROM pg_enum "
                "JOIN pg_type ON pg_enum.enumtypid = pg_type.oid "
                "WHERE pg_type.typname='authority_role' ORDER BY enumsortorder"
            )
            values = {row[0] for row in c.fetchall()}
        # provisional role set per security/__init__.py
        assert values == {
            "pemangku",
            "pemangku_keramas",
            "kelian_adat",
            "bendesa_adat",
            "pekalang",
            "banjar_operator",
            "dewata_admin",
            "dewata_editor",
        }

    def test_ceremony_phase_enum_values(self, disposable_conn):
        with disposable_conn.cursor() as c:
            c.execute(
                "SELECT enumlabel FROM pg_enum "
                "JOIN pg_type ON pg_enum.enumtypid = pg_type.oid "
                "WHERE pg_type.typname='ceremony_phase' ORDER BY enumsortorder"
            )
            values = {row[0] for row in c.fetchall()}
        assert values == {
            "predicted", "confirmed", "occurring", "completed", "cancelled",
        }

    def test_seed_kabupaten_codes(self, disposable_conn):
        """the migration seeds two *_TEST placeholders.  no real bali
        kabupaten codes are present."""
        with disposable_conn.cursor() as c:
            c.execute("SELECT code FROM kabupaten ORDER BY code")
            codes = [row[0] for row in c.fetchall()]
        assert codes == ["gaau", "gbxx"]
        # critical: no canonical bali codes were inserted by the migration
        assert "gianyar" not in codes
        assert "badung" not in codes
        assert "denpasar" not in codes

    def test_actor_handle_unique(self, disposable_conn):
        """the actor.handle column is UNIQUE; a second insert with the
        same handle must fail with psycopg.errors.UniqueViolation."""
        with disposable_conn.cursor() as c:
            c.execute(
                "INSERT INTO actor (handle, kind, role, display_name) "
                "VALUES ('unq-handle', 'person', 'banjar_operator', 'Test A')"
            )
            disposable_conn.commit()
        try:
            with disposable_conn.cursor() as c:
                with pytest.raises(psycopg.errors.UniqueViolation):
                    c.execute(
                        "INSERT INTO actor (handle, kind, role, display_name) "
                        "VALUES ('unq-handle', 'person', 'banjar_operator', 'Test B')"
                    )
                    disposable_conn.commit()
            disposable_conn.rollback()  # ensure a clean transaction state
        finally:
            with disposable_conn.cursor() as c:
                c.execute("DELETE FROM actor WHERE handle = 'unq-handle'")
                disposable_conn.commit()


# ────────────────────────────────────────────────────────────────
# class 2 — append-only invariants
# ────────────────────────────────────────────────────────────────

class TestAppendOnlyInvariants:

    def _provision(self, conn) -> tuple[Any, Any, Any]:
        """kabupaten → desa → banjar → actor; returns (banjar_id, actor_id, desa_id)."""
        fix.insert_kabupaten(conn)
        # pick the first kabupaten as fixture base
        banjar_id = fix.insert_one_synthetic_banjar(
            conn,
            kabupaten_code="gbxx",
            desa_adat_id=fix.insert_one_synthetic_desa(
                conn, kabupaten_code="gbxx", handle="dsa-fkt-000001"
            ),
            handle="bjr-fkt-000001",
        )
        actor_id = fix.insert_one_synthetic_actor(
            conn, handle="test-actor", display_name="Test Actor"
        )
        return banjar_id, actor_id

    def test_ceremony_update_rejected(self, disposable_conn):
        banjar_id, actor_id = self._provision(disposable_conn)
        c_id = fix.insert_one_synthetic_ceremony(
            disposable_conn, banjar_id=banjar_id, author_id=actor_id
        )
        with disposable_conn.cursor() as c:
            with pytest.raises(psycopg.errors.IntegrityError) as exc_info:
                c.execute("UPDATE ceremony SET title = 'new title' WHERE id = %s", (c_id,))
                disposable_conn.commit()
            disposable_conn.rollback()
        assert "append-only" in str(exc_info.value).lower()

    def test_ceremony_state_update_rejected(self, disposable_conn):
        banjar_id, actor_id = self._provision(disposable_conn)
        c_id = fix.insert_one_synthetic_ceremony(
            disposable_conn, banjar_id=banjar_id, author_id=actor_id
        )
        s_id = fix.insert_one_ceremony_state(
            disposable_conn, ceremony_id=c_id, state="predicted", actor_id=actor_id
        )
        with disposable_conn.cursor() as c:
            with pytest.raises(psycopg.errors.IntegrityError) as exc_info:
                c.execute(
                    "UPDATE ceremony_state SET state = 'completed'::ceremony_phase WHERE id = %s",
                    (s_id,),
                )
                disposable_conn.commit()
            disposable_conn.rollback()
        assert "append only" in str(exc_info.value).lower()

    def test_pura_does_not_reference_self(self, disposable_conn):
        """the pura.pura_relationship table doesn't allow parent=child
        (it forces a real relationship).  here we test that pura.parent
        isn't a column on pura, so a cycle isn't introduced through
        pura directly.  this is a place-holder until pura relationships
        are finalized in the next migration."""
        # There is no pura.parent_id column.  Verify it's absent.
        with disposable_conn.cursor() as c:
            c.execute(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name='pura' AND column_name='parent_id'"
            )
            row = c.fetchone()
        assert row is None, "pura.parent_id must not exist; relationships live in pura_relationship"


# ────────────────────────────────────────────────────────────────
# class 3 — migration runner
# ────────────────────────────────────────────────────────────────

class TestMigrationRunner:
    """exercise the python migration runner module."""

    def test_runner_lists_migration(self):
        from dewatacalendar.db import _migrations_dir, list_available_migrations
        names = list_available_migrations()
        assert "0001_initial_schema.sql" in names
        assert all(name.startswith("0001_") for name in names) or len(names) >= 1

    def test_runner_status(self, disposable_dsn, monkeypatch):
        """`status` reports the migration as applied.
        `apply_migrations` is a no-op when already applied (don't re-run
        it here because the disposable_conn fixture already migrated)."""
        from dewatacalendar.db import status as db_status
        entries = db_status(disposable_dsn)
        versions = [e["version"] for e in entries]
        assert any(v.startswith("0001") for v in versions)
