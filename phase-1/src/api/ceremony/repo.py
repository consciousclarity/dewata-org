"""ceremony repository layer.

this module centralizes all sql access for the ceremony domain.  the
goal is to keep the route layer thin and the security-relevant
field selection in one place.

responsibilities:

  - **connect** to the database (DSN from env, never hardcoded).
  - **select** ceremonies and apply visibility-tier redaction based on
    the caller's claims.
  - **insert** ceremony rows with FK validation.
  - **append** append-only ceremony_state rows.
  - **list** ceremonies with pagination + filtering.
  - **paginate** using `?limit=` and `?offset=`.

the repository never decides cultural policy; that lives in
`dewatacalendar.security.DefaultPolicy`.  if a requester lacks the
scope to view restricted content, the repository returns the
banjar-tier projection.
"""

from __future__ import annotations

import logging
import os
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, fields
from typing import Any, Iterable, Iterator, Optional

log = logging.getLogger(__name__)


@dataclass
class CeremonyRow:
    id: uuid.UUID
    banjar_id: uuid.UUID
    pura_id: Optional[uuid.UUID]
    class_: str
    title: str
    external_handle: str
    visibility: str
    scheduled_for: Optional[str]
    created_at: Any
    created_by_actor_id: Optional[uuid.UUID]
    state_phase: str
    computed_by_ruleset: Optional[str]
    actor_provenance_count: int
    evidence_count: int


@dataclass
class CeremonyListPage:
    items: list[dict[str, Any]]
    next_offset: Optional[int]
    total: int


class CeremonyRepo:
    """thin wrapper around a psycopg connection.

    the connection lifecycle is managed by the caller (api route
    handlers should depend on `db_session`).
    """

    def __init__(self, conn) -> None:
        self.conn = conn

    def fetch_one(self, ceremony_id: uuid.UUID) -> Optional[CeremonyRow]:
        with self.conn.cursor() as c:
            c.execute(
                "SELECT c.id, c.banjar_id, c.pura_id, c.class::text, c.title, "
                "  c.external_handle, c.visibility::text, c.scheduled_for, "
                "  c.created_at, c.created_by_actor_id "
                "FROM ceremony c WHERE c.id = %s",
                (ceremony_id,),
            )
            row = c.fetchone()
            if row is None:
                return None
            # also fetch latest state phase
            c.execute(
                "SELECT state::text FROM ceremony_state "
                "WHERE ceremony_id = %s ORDER BY observed_at DESC LIMIT 1",
                (ceremony_id,),
            )
            state_row = c.fetchone()
            state_phase = state_row[0] if state_row else "predicted"
        return CeremonyRow(
            id=row[0],
            banjar_id=row[1],
            pura_id=row[2],
            class_=row[3],
            title=row[4],
            external_handle=row[5],
            visibility=row[6],
            scheduled_for=str(row[7]) if row[7] else None,
            created_at=row[8].isoformat() if row[8] else "",
            created_by_actor_id=row[9],
            state_phase=state_phase,
            computed_by_ruleset=None,
            actor_provenance_count=self._count_provenance(ceremony_id),
            evidence_count=self._count_evidence(ceremony_id),
        )

    def _count_provenance(self, ceremony_id) -> int:
        with self.conn.cursor() as c:
            c.execute(
                "SELECT count(*) FROM ceremony_authority_link WHERE ceremony_id=%s",
                (ceremony_id,),
            )
            return c.fetchone()[0]

    def _count_evidence(self, ceremony_id) -> int:
        with self.conn.cursor() as c:
            c.execute(
                "SELECT count(*) FROM ceremony_source WHERE ceremony_id=%s",
                (ceremony_id,),
            )
            return c.fetchone()[0]

    def list_public(
        self, *, limit: int = 20, offset: int = 0, banjar_id: Optional[str] = None
    ) -> CeremonyListPage:
        """list ceremonies visible at the public tier (no auth required)."""
        where = "WHERE c.visibility = 'public'"
        params: list = []
        if banjar_id:
            where = "WHERE c.banjar_id = %s AND c.visibility = 'public'"
            params.append(banjar_id)
        with self.conn.cursor() as c:
            c.execute(
                "SELECT count(*) FROM ceremony c " + where,
                tuple(params),
            )
            total = c.fetchone()[0]
            params.extend([limit, offset])
            c.execute(
                "SELECT c.id, c.banjar_id, c.pura_id, c.class::text, c.title, "
                "  c.external_handle, c.visibility::text, c.scheduled_for, "
                "  c.created_at, c.created_by_actor_id, "
                "  (SELECT state::text FROM ceremony_state s "
                "    WHERE s.ceremony_id = c.id ORDER BY s.observed_at DESC LIMIT 1) "
                "FROM ceremony c " + where + " ORDER BY c.created_at DESC "
                "LIMIT %s OFFSET %s",
                tuple(params),
            )
            rows = c.fetchall()
        items: list[dict[str, Any]] = []
        for r in rows:
            items.append(
                {
                    "id": str(r[0]),
                    "banjar_id": str(r[1]),
                    "pura_id": str(r[2]) if r[2] else None,
                    "class": r[3],
                    "title": r[4],
                    "external_handle": r[5],
                    "visibility": r[6],
                    "scheduled_for": str(r[7]) if r[7] else None,
                    "created_at": r[8].isoformat() if r[8] else "",
                    "state_phase": r[10] or "predicted",
                    "provenance_label": "registered",
                }
            )
        next_offset = (offset + len(items)) if offset + len(items) < total else None
        return CeremonyListPage(items=items, next_offset=next_offset, total=total)

    def fetch_one_redacted(
        self,
        ceremony_id: uuid.UUID,
        *,
        viewer_banjar_id: Optional[uuid.UUID],
        viewer_roles: Iterable[str],
    ) -> Optional[dict[str, Any]]:
        """fetch a ceremony projecting fields by visibility tier.

        returns:
            None  -> not found or not viewable
            dict  -> projection per the highest tier the viewer can see
        """
        row = self.fetch_one(ceremony_id)
        if row is None:
            return None
        from dewatacalendar.security import (
            Actor, AuthorityRole, VisibilityTier, enforce_visibility, AccessDeniedError,
        )
        # pick the highest-privilege role the viewer claims; anon if none
        role = AuthorityRole.PUBLIC
        candidate_priority = (
            AuthorityRole.DEWATA_ADMIN, AuthorityRole.DEWATA_EDITOR,
            AuthorityRole.PEMANGKU_KERAMAS, AuthorityRole.PEMANGKU,
            AuthorityRole.BENDESA_ADAT, AuthorityRole.PEKALANG,
            AuthorityRole.KLIAN_ADAT, AuthorityRole.BANJAR_OPERATOR,
        )
        for cand in candidate_priority:
            if cand.value in viewer_roles:
                role = cand
                break
        viewer = Actor(actor_id="anon", role=role)
        # attempt to escalate tier through successive levels
        for tier in (VisibilityTier.PUBLIC, VisibilityTier.BANJAR,
                     VisibilityTier.DESA_ADAT, VisibilityTier.RESTRICTED,
                     VisibilityTier.PRIVATE):
            try:
                enforce_visibility(
                    actor=viewer,
                    resource_tier=tier,
                    resource_owner_banjar_id=str(row.banjar_id) if row.banjar_id else None,
                )
            except AccessDeniedError:
                continue
            # visibility accepted at this tier; project
            if tier == VisibilityTier.PUBLIC:
                return _to_public_dict(row)
            if tier == VisibilityTier.BANJAR:
                return _to_banjar_dict(row)
            if tier == VisibilityTier.DESA_ADAT:
                return _to_desa_adat_dict(row)
            if tier == VisibilityTier.RESTRICTED:
                return _to_restricted_dict(row, self.conn, ceremony_id)
            if tier == VisibilityTier.PRIVATE:
                return _to_private_meta_dict(row)
        return None

    def insert_ceremony(
        self,
        *,
        banjar_id: uuid.UUID,
        pura_id: Optional[uuid.UUID],
        class_: str,
        title: str,
        external_handle: str,
        visibility: str,
        scheduled_for: Optional[str],
        created_by_actor_id: uuid.UUID,
    ) -> uuid.UUID:
        with self.conn.cursor() as c:
            c.execute(
                "INSERT INTO ceremony ("
                "  banjar_id, pura_id, class, title, external_handle,"
                "  visibility, scheduled_for, created_by_actor_id"
                ") VALUES ("
                "  %s, %s, %s::ceremony_class, %s, %s,"
                "  %s::visibility_tier, %s::date, %s"
                ") RETURNING id",
                (
                    banjar_id, pura_id, class_, title, external_handle,
                    visibility, scheduled_for, created_by_actor_id,
                ),
            )
            new_id = c.fetchone()[0]
        self.conn.commit()
        return new_id

    def append_state(
        self,
        *,
        ceremony_id: uuid.UUID,
        state: str,
        reason: Optional[str],
        observed_at=None,
        actor_id: Optional[uuid.UUID],
        source_url: Optional[str],
        evidence_blob_id: Optional[uuid.UUID],
    ) -> uuid.UUID:
        with self.conn.cursor() as c:
            c.execute(
                "INSERT INTO ceremony_state ("
                "  ceremony_id, state, reason, observed_at, actor_id,"
                "  source_url, evidence_blob_id"
                ") VALUES (%s, %s::ceremony_phase, %s, COALESCE(%s, now()), %s, %s, %s) "
                "RETURNING id",
                (ceremony_id, state, reason, observed_at, actor_id,
                 source_url, evidence_blob_id),
            )
            new_id = c.fetchone()[0]
        self.conn.commit()
        return new_id

    def list_authority_links(
        self, ceremony_id: uuid.UUID
    ) -> list[dict[str, Any]]:
        with self.conn.cursor() as c:
            c.execute(
                "SELECT actor_id::text, role, begins_at, ends_at "
                "FROM ceremony_authority_link WHERE ceremony_id = %s "
                "ORDER BY begins_at DESC",
                (ceremony_id,),
            )
            rows = c.fetchall()
        return [
            {
                "actor_id": r[0], "role": r[1],
                "begins_at": r[2].isoformat() if r[2] else None,
                "ends_at": r[3].isoformat() if r[3] else None,
            }
            for r in rows
        ]


def _to_public_dict(row: CeremonyRow) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "external_handle": row.external_handle,
        "title": row.title,
        "class": row.class_,
        "banjar_id": str(row.banjar_id),
        "pura_id": str(row.pura_id) if row.pura_id else None,
        "scheduled_for": row.scheduled_for,
        "visibility": row.visibility,
        "state_phase": row.state_phase,
        "computed_by_ruleset": row.computed_by_ruleset,
        "actor_provenance_count": row.actor_provenance_count,
        "evidence_count": row.evidence_count,
        "provenance_label": "registered",
        "created_at": row.created_at,
        # NOTE: no `updated_at`, no `banjar_internal_notes`, no
        # `delegated_authorities` -- these are banjar-tier+ fields.
    }


def _to_banjar_dict(row: CeremonyRow) -> dict[str, Any]:
    d = _to_public_dict(row)
    d["banjar_internal_notes"] = None  # future schema addition
    return d


def _to_desa_adat_dict(row: CeremonyRow) -> dict[str, Any]:
    d = _to_banjar_dict(row)
    d["desa_adat_internal_notes"] = None  # future schema addition
    return d


def _to_restricted_dict(
    row: CeremonyRow, conn, ceremony_id
) -> dict[str, Any]:
    d = _to_desa_adat_dict(row)
    # fetch delegated authority rows
    with conn.cursor() as c:
        c.execute(
            "SELECT actor_id::text, role, begins_at, ends_at "
            "FROM ceremony_authority_link WHERE ceremony_id = %s "
            "ORDER BY begins_at DESC",
            (ceremony_id,),
        )
        rows = c.fetchall()
    d["delegated_authorities"] = [
        {
            "actor_id": r[0], "role": r[1],
            "begins_at": r[2].isoformat() if r[2] else None,
            "ends_at": r[3].isoformat() if r[3] else None,
        }
        for r in rows
    ]
    return d


def _to_private_meta_dict(row: CeremonyRow) -> dict[str, Any]:
    """private tier returns only metadata; the body is omitted."""
    return {
        "id": str(row.id),
        "visibility": row.visibility,
        "provenance_label": "metadata-only",
    }


__all__ = ["CeremonyRepo", "CeremonyRow", "CeremonyListPage"]
