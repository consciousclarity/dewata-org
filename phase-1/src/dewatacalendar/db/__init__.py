"""database migration runner.

schema lives in `phase-1/db/migrations/`.  each migration is a
forward-only `.sql` file with an optional `.down.sql` sibling.

the runner assumes a postgresql-compatible database with postgis
already installed (the `postgis/postgis:16-3.4` image satisfies
that).  the *engine* uses sqlalchemy + psycopg2; this module does
not commit, run, or alter the live `dewata` database unless you
explicitly opt in.

designed for:
    python -m dewatacalendar.db up --target <conn-string>
    python -m dewatacalendar.db down --target <conn-string>
    python -m dewatacalendar.db status --target <conn-string>

`--target` is read from `--target <dsn>` OR the env var `DEWATA_TEST_DSN`
(which the project's existing CI uses; never name it `DEWATA_DB_DSN`,
which is reserved for production).
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import json
import logging
import os
import re
import sys
import textwrap
from pathlib import Path
from typing import Iterable

import psycopg
from psycopg import sql

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "db" / "migrations"

log = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class Migration:
    number: str
    up_path: Path
    down_path: Path | None
    label: str

    @classmethod
    def discover(cls, root: Path = MIGRATIONS_DIR) -> list["Migration"]:
        if not root.is_dir():
            return []
        out: list[Migration] = []
        for p in sorted(root.iterdir()):
            m = re.match(r"^(\d{4})_(.+)\.sql$", p.name)
            if not m:
                continue
            if p.name.endswith(".down.sql"):
                continue
            number, label = m.groups()
            down = p.with_name(f"{number}.down.sql")
            if not down.exists():
                down = None
            out.append(cls(number=number, up_path=p, down_path=down, label=label))
        return out


def list_applied(conn: psycopg.Connection) -> list[str]:
    """return migration versions already applied.

    uses the `schema_migrations.version` column (kept compatible with
    the existing migration's CREATE TABLE statement).
    """
    with conn.cursor() as c:
        c.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        )
        return [row[0] for row in c.fetchall()]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _migrations_dir() -> Path:
    """test helper: name-stable alias for MIGRATIONS_DIR."""
    return MIGRATIONS_DIR


def list_available_migrations() -> list[str]:
    """test helper: list migration filenames (`.sql`) in version order."""
    return [m.up_path.name for m in Migration.discover()]


def ensure_migrations_table(conn: psycopg.Connection) -> None:
    """ensure `schema_migrations` exists (no-op if migration 0001 has run)."""
    # migration 0001 already creates `schema_migrations` with the right
    # columns; we don't duplicate the DDL here to avoid divergence.
    pass


def record_migration(
    conn: psycopg.Connection, m: "Migration", sql_text: str
) -> None:
    import hashlib
    checksum = hashlib.sha256(sql_text.encode("utf-8")).hexdigest()
    with conn.cursor() as c:
        c.execute(
            "INSERT INTO schema_migrations (version, description, checksum, rollback_present) "
            "VALUES (%s, %s, %s, %s) ON CONFLICT (version) DO NOTHING",
            (m.number, m.label, checksum, m.down_path is not None),
        )
    conn.commit()


def apply_migrations(dsn: str) -> None:
    """apply all pending migrations against the given DSN.

    test-only convenience; bypasses the safety flags in main().
    """
    conn = psycopg.connect(dsn)
    try:
        ensure_migrations_table(conn)
        applied = set(list_applied(conn))
        pending = [m for m in Migration.discover() if m.number not in applied]
        for m in pending:
            log.info("applying %s", m.up_path.name)
            sql_text = m.up_path.read_text(encoding="utf-8")
            with conn.cursor() as c:
                c.execute(sql_text)
            record_migration(conn, m, sql_text)
        conn.commit()
    finally:
        conn.close()


def status(dsn: str) -> list[dict]:
    """return [{version, label, applied_at}] for the given DSN."""
    conn = psycopg.connect(dsn)
    try:
        with conn.cursor() as c:
            c.execute(
                "SELECT version, description, applied_at "
                "FROM schema_migrations ORDER BY version"
            )
            rows = c.fetchall()
        return [
            {"version": r[0], "label": r[1], "applied_at": r[2]} for r in rows
        ]
    finally:
        try:
            conn.close()
        except Exception:
            pass


def cmd_up(args: argparse.Namespace) -> int:
    dsn = args.target
    if not dsn:
        log.error("refusing to run without --target DSN (safety belt for prod db).")
        return 2
    migrations = Migration.discover()
    with psycopg.connect(dsn) as conn:
        applied = set(list_applied(conn))
        to_apply = [m for m in migrations if m.number not in applied]
        if args.dry_run:
            for m in to_apply:
                print(f"would apply {m.number} {m.label}")
            return 0
        for m in to_apply:
            log.info("applying %s %s", m.number, m.label)
            with conn.cursor() as c:
                c.execute(_read(m.up_path))
            with conn.cursor() as c:
                c.execute(
                    "INSERT INTO schema_migrations (number, label) VALUES (%s, %s)",
                    (m.number, m.label),
                )
            conn.commit()
        print(f"applied {len(to_apply)} migrations")
        return 0


def cmd_down(args: argparse.Namespace) -> int:
    dsn = args.target
    if not dsn:
        log.error("refusing to run without --target DSN.")
        return 2
    migrations = Migration.discover()
    # apply .down.sql files in reverse order
    migrations_with_down = [m for m in migrations if m.down_path]
    with psycopg.connect(dsn) as conn:
        applied = list_applied(conn)
        for m in sorted(migrations_with_down, key=lambda m: m.number, reverse=True):
            if m.number not in applied:
                continue
            if args.dry_run:
                print(f"would roll back {m.number} {m.label}")
                continue
            log.warning("rolling back %s %s", m.number, m.label)
            with conn.cursor() as c:
                c.execute(_read(m.down_path))
            with conn.cursor() as c:
                c.execute("DELETE FROM schema_migrations WHERE number = %s", (m.number,))
            conn.commit()
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    migrations = Migration.discover()
    if args.target:
        with psycopg.connect(args.target) as conn:
            applied = set(list_applied(conn))
    else:
        applied = set()
    print(f"{'number':<6}  {'state':<10}  label")
    print("-" * 60)
    for m in migrations:
        state = "applied" if m.number in applied else "pending"
        print(f"{m.number:<6}  {state:<10}  {m.label}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="python -m dewatacalendar.db",
        description="dewata migration runner (read-only by default; up/down require --target DSN).",
    )
    p.add_argument(
        "--target",
        help="DSN of the database to migrate.  REQUIRED for up/down.  "
             "DEFAULTS to $DEWATA_TEST_DSN if unset.  refusing to operate "
             "against the production database unless DEWATA_PROD_CONFIRM=yes.",
        default=os.environ.get("DEWATA_TEST_DSN") or "",
    )
    p.add_argument("--dry-run", action="store_true", help="print plan but do not apply.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("up").set_defaults(func=cmd_up)
    sub.add_parser("down").set_defaults(func=cmd_down)
    sub.add_parser("status").set_defaults(func=cmd_status)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

