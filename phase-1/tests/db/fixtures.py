"""synthetic fixture factories for the dewata schema.

these functions create *clearly fictional* records, suitable for
disposable test databases and CI.  nothing here references a real
institution, person, or location.

the values chosen are intentionally generic so they cannot be
mistaken for real-world bali entities.  if you need real data,
you must source it through a customary-ratified onboarding flow.
see `phase-1/docs/runbook/SIGNOFF.md` for the ratify-and-collect path.

design note: the schema in `db/migrations/0001_initial_schema.sql`
uses:
  - kabupaten primary key = column `code` (text, e.g. 'gbxx' for a
    fictional kabupaten; 'gianyar'-style codes will be added **only**
    by a customary-ratified onboarding flow; this fixture uses
    placeholders).
  - actor.handle and actor.display_name (no "external_handle_kind"
    subcolumn).
  - pura.pura_kind (free text, since the schema's `pura_kind` is
    free-text) not `pura_class`.
  - ceremony.class (the schema's reserved-word sanitisation: column
    is `class`, type is `ceremony_class` enum).
  - ceremony.visibility (column name) of type `visibility_tier` enum.
"""

from __future__ import annotations

import uuid
from typing import Any

import psycopg


# ─────────────── pure-python fixture values ───────────────

FICTIONAL_KABUPATEN_CODES = ["gbxx", "gaau"]
FICTIONAL_BANJAR_HANDLES = [
    "bjr-fkt-000001",
    "bjr-fkt-000002",
    "bjr-fkt-000003",
]


# ─────────────── multi-statement SQL splitter ───────────────

def _split_sql_statements(sql: str) -> list[str]:
    """split a multi-statement SQL file on top-level `;`.

    handles `-- comment` lines and Dollar-Quoted Strings (`$$…$$`).
    naive split but enough for our migrations (which we control).
    """
    out: list[str] = []
    buf: list[str] = []
    in_dollar = False
    for line in sql.splitlines():
        if in_dollar:
            buf.append(line)
            if "$$" in line:
                in_dollar = False
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        if "$$" in line:
            in_dollar = True
            buf.append(line)
            count = line.count("$$")
            if count >= 2:
                in_dollar = False
            continue
        buf.append(line)
        if stripped.endswith(";"):
            stmt = "\n".join(buf).strip().rstrip(";").strip()
            if stmt:
                out.append(stmt)
            buf = []
    if buf:
        stmt = "\n".join(buf).strip().rstrip(";").strip()
        if stmt:
            out.append(stmt)
    return out


# ─────────────── migration runner ───────────────

def bootstrap_test_database(conn: psycopg.Connection) -> None:
    """apply 0001 to the connected test database.

    does NOT call `commit()` inside the loop; callers control the
    transaction.  also records the applied migration so that the
    `dewatacalendar.db.status()` helper returns proper results.
    """
    from pathlib import Path
    sql_path = Path(__file__).resolve().parent.parent.parent / "db" / "migrations" / "0001_initial_schema.sql"
    if not sql_path.exists():
        raise FileNotFoundError(sql_path)
    with conn.cursor() as c:
        c.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    statements = _split_sql_statements(sql_path.read_text(encoding="utf-8"))
    for stmt in statements:
        try:
            with conn.cursor() as c:
                c.execute(stmt)
        except Exception as e:
            print(f"migration statement failed: {type(e).__name__}: {str(e)[:200]}")
            print("statement (first 400):", stmt[:400])
            raise
    # record the migration so tests that use status() work consistently
    import hashlib
    sql_text = sql_path.read_text(encoding="utf-8")
    checksum = hashlib.sha256(sql_text.encode("utf-8")).hexdigest()
    with conn.cursor() as c:
        c.execute(
            "INSERT INTO schema_migrations (version, description, checksum, rollback_present) "
            "VALUES ('0001', 'initial_schema', %s, true) "
            "ON CONFLICT (version) DO NOTHING",
            (checksum,),
        )
    conn.commit()


# ─────────────── build helpers ───────────────

def insert_kabupaten(conn: psycopg.Connection) -> list[str]:
    """insert two clearly-fictional kabupaten.  returns their codes."""
    with conn.cursor() as c:
        for code, name in [
            ("gbxx", "Fictional Kabupaten A"),
            ("gaau", "Fictional Kabupaten B"),
        ]:
            c.execute(
                "INSERT INTO kabupaten (code, name) VALUES (%s, %s) "
                "ON CONFLICT (code) DO NOTHING",
                (code, name),
            )
    conn.commit()
    return list(FICTIONAL_KABUPATEN_CODES)


def insert_one_synthetic_actor(conn: psycopg.Connection, *,
                               handle: str = "fixture-actor",
                               role: str = "banjar_operator",
                               display_name: str = "Fixture Actor",
                               kind: str = "person") -> uuid.UUID:
    with conn.cursor() as c:
        c.execute(
            "INSERT INTO actor (handle, kind, role, display_name) "
            "VALUES (%s, %s, %s::authority_role, %s) RETURNING id",
            (handle, kind, role, display_name),
        )
        actor_id = c.fetchone()[0]
    conn.commit()
    return actor_id


def insert_one_synthetic_desa(conn: psycopg.Connection, *,
                              kabupaten_code: str,
                              handle: str = "dsa-fkt-000001",
                              display_name: str = "Fictional Desa Adat") -> uuid.UUID:
    with conn.cursor() as c:
        c.execute(
            "INSERT INTO desa_adat (kabupaten_code, handle, display_name) "
            "VALUES (%s, %s, %s) RETURNING id",
            (kabupaten_code, handle, display_name),
        )
        desa_id = c.fetchone()[0]
    conn.commit()
    return desa_id


def insert_one_synthetic_banjar(conn: psycopg.Connection, *,
                                kabupaten_code: str,
                                desa_adat_id,
                                handle: str = "bjr-fkt-000001",
                                display_name: str = "Fictional Banjar") -> uuid.UUID:
    with conn.cursor() as c:
        c.execute(
            "INSERT INTO banjar (kabupaten_code, desa_adat_id, handle, display_name) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (kabupaten_code, desa_adat_id, handle, display_name),
        )
        banjar_id = c.fetchone()[0]
    conn.commit()
    return banjar_id


def insert_one_synthetic_pura(conn: psycopg.Connection, *,
                              kabupaten_code: str,
                              banjar_id=None,
                              handle: str = "pua-fkt-000001",
                              display_name: str = "Fictional Pura") -> uuid.UUID:
    with conn.cursor() as c:
        c.execute(
            "INSERT INTO pura (kabupaten_code, banjar_id, handle, display_name) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (kabupaten_code, banjar_id, handle, display_name),
        )
        pura_id = c.fetchone()[0]
    conn.commit()
    return pura_id


def insert_one_synthetic_ceremony(conn: psycopg.Connection, *,
                                  banjar_id,
                                  author_id,
                                  title: str = "Fictional Ceremony",
                                  ceremony_class: str = "piodalan",
                                  visibility: str = "banjar",
                                  external_handle: str = "CR-FKT-000001") -> uuid.UUID:
    with conn.cursor() as c:
        c.execute(
            "INSERT INTO ceremony ("
            "  banjar_id, class, visibility, title, external_handle,"
            "  scheduled_for, created_by_actor_id"
            ") VALUES ("
            "  %s, %s::ceremony_class, %s::visibility_tier,"
            "  %s, %s, current_date + 7, %s"
            ") RETURNING id",
            (banjar_id, ceremony_class, visibility, title, external_handle, author_id),
        )
        ceremony_id = c.fetchone()[0]
    conn.commit()
    return ceremony_id


def insert_one_ceremony_state(conn: psycopg.Connection, *,
                              ceremony_id,
                              state: str = "predicted",
                              actor_id=None) -> uuid.UUID:
    """append a row to the append-only ceremony_state table.

    this exists to test the append-only trigger.
    """
    with conn.cursor() as c:
        c.execute(
            "INSERT INTO ceremony_state (ceremony_id, state, actor_id) "
            "VALUES (%s, %s::ceremony_phase, %s) RETURNING id",
            (ceremony_id, state, actor_id),
        )
        cid = c.fetchone()[0]
    conn.commit()
    return cid
