"""ceremony API routes.

mounted under `/ceremony/v0.1/`:

  GET    /ceremony/v0.1/visibility-tiers
        -> list of {value,label,description} for the 5 visibility tiers

  GET    /ceremony/v0.1/ceremonies?banjar_id=&limit=&offset=
        -> list of public-tier ceremonies (no auth)

  GET    /ceremony/v0.1/ceremonies/{id}
        -> fetch one ceremony, projection per visibility tier

  POST   /ceremony/v0.1/ceremonies
        -> create one ceremony (auth required, scope:ceremony:create)

  POST   /ceremony/v0.1/ceremonies/{id}/state
        -> append an append-only state transition

  GET    /ceremony/v0.1/ceremonies/{id}/provenance
        -> list authority links (configurable visibility)

this module is intentionally small.  the repository owns visibility-tier
logic (`repo.fetch_one_redacted`).  routes only map url+method to
repository calls and translate exceptions to error envelopes.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from ..observability.errors import (
    BadRequest, Forbidden, NotFound, TooManyRequests, Unauthorized,
    error_response,
)
from ..auth.jwt import JwtIdentity, verify_token
from .repo import CeremonyRepo, CeremonyListPage


log = logging.getLogger(__name__)
router = APIRouter(prefix="/ceremony/v0.1", tags=["ceremony"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# request/response shapes (pydantic for fastapi, not the db layer)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CeremonyCreateBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    ceremony_class: str = Field(..., alias="class")  # `class` is python keyword
    banjar_id: str
    pura_id: Optional[str] = None
    scheduled_for: Optional[str] = None
    visibility: str = "banjar"
    external_handle: Optional[str] = None

    class Config:
        populate_by_name = True


class StateTransitionBody(BaseModel):
    state: str
    reason: Optional[str] = None
    source_url: Optional[str] = None
    evidence_blob_id: Optional[str] = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# dependency injection
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def repo_dep(request: Request) -> CeremonyRepo:
    """return the ceremony repo wired against the request's db session."""
    conn = request.app.state.db_connection
    return CeremonyRepo(conn)


def _bearer_token(authorization: Optional[str]) -> Optional[str]:
    """extract a token from `Authorization: Bearer <token>`."""
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None


def identity_dep(
    authorization: Optional[str] = Header(default=None),
) -> Optional[JwtIdentity]:
    """verify the JWT (if any) and return the identity.

    unauthenticated requests resolve to `None`.  this enables public
    endpoints without forcing the whole api behind auth.
    """
    token = _bearer_token(authorization)
    if not token:
        return None
    try:
        return verify_token(token)
    except Unauthorized:
        # bubble up as 401 to the caller
        raise


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# public routes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/visibility-tiers")
def list_visibility_tiers() -> dict:
    """return the canonical visibility tier set.

    this is a *public* document — no auth required.  clients use it
    to display tier descriptors consistently.
    """
    from dewatacalendar.security import VisibilityTier
    return {
        "tiers": [
            {
                "value": tier.value,
                "label": tier.value.replace("_", " ").title(),
                "description": _tier_description(tier),
                "policy_marker": "provisional",
            }
            for tier in VisibilityTier
        ],
        "policy_marker": "provisional",
    }


def _tier_description(tier) -> str:
    descriptions = {
        "public": "visible to everyone; no auth required.",
        "banjar": "visible to members of the banjar.",
        "desa_adat": "visible to desa-adat members and banjar chairs.",
        "restricted": "visible to authorised roles only.",
        "private": "metadata only; body not serialised.",
    }
    return descriptions.get(
        tier.value, f"visibility tier {tier.value} (no description)."
    )


@router.get("/ceremonies")
def list_ceremonies(
    *,
    banjar_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    repo: CeremonyRepo = Depends(repo_dep),
) -> dict:
    """list public-tier ceremonies.

    unauthenticated.  filtered by visibility=public at the db level;
    higher-tier rows are not returned in this list.
    """
    if limit < 1 or limit > 200:
        raise BadRequest("limit must be in 1..200", details={"limit": limit})
    if offset < 0:
        raise BadRequest("offset must be >= 0", details={"offset": offset})
    page: CeremonyListPage = repo.list_public(
        limit=limit, offset=offset, banjar_id=banjar_id,
    )
    return {
        "items": page.items,
        "total": page.total,
        "limit": limit,
        "offset": offset,
        "next_offset": page.next_offset,
    }


@router.get("/ceremonies/{ceremony_id}")
def get_ceremony(
    ceremony_id: str,
    *,
    repo: CeremonyRepo = Depends(repo_dep),
    identity: Optional[JwtIdentity] = Depends(identity_dep),
) -> dict:
    """fetch one ceremony, projection per visibility tier."""
    try:
        cid = uuid.UUID(ceremony_id)
    except ValueError:
        raise BadRequest("ceremony_id must be a uuid", details={"id": ceremony_id})
    viewer_banjar_id = None
    viewer_roles: tuple[str, ...] = ()
    if identity is not None:
        viewer_roles = identity.roles
        # identity.actor_id could encode a banjar membership; out of scope
        # for v0.1 (production would resolve this via a side-table)
    projection = repo.fetch_one_redacted(
        cid, viewer_banjar_id=viewer_banjar_id, viewer_roles=viewer_roles,
    )
    if projection is None:
        raise NotFound(
            "ceremony not found or not visible",
            details={"id": ceremony_id},
        )
    return projection


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# authenticated routes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _require_scope(identity: Optional[JwtIdentity], scope: str) -> JwtIdentity:
    if identity is None:
        raise Unauthorized("authentication required", details={"scope": scope})
    if scope not in identity.scope:
        raise Forbidden(
            f"scope={scope!r} required",
            details={"scope": scope, "have": list(identity.scope)},
        )
    return identity


@router.post("/ceremonies")
def create_ceremony(
    body: CeremonyCreateBody,
    *,
    repo: CeremonyRepo = Depends(repo_dep),
    identity: Optional[JwtIdentity] = Depends(identity_dep),
) -> dict:
    """create one ceremony (auth required)."""
    _require_scope(identity, "ceremony:create")
    if identity is None:
        raise Unauthorized("authentication required")  # unreachable
    # name-shadowed the python keyword
    ceremony_class = body.ceremony_class
    # FK checks
    try:
        banjar_uuid = uuid.UUID(body.banjar_id)
    except ValueError:
        raise BadRequest("banjar_id must be a uuid", details={"banjar_id": body.banjar_id})
    try:
        actor_uuid = uuid.UUID(identity.actor_id)
    except ValueError:
        # for tests actor_id is a string; the api stores it as-is.
        actor_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, identity.actor_id)
    try:
        pura_uuid = uuid.UUID(body.pura_id) if body.pura_id else None
    except ValueError:
        raise BadRequest("pura_id must be a uuid", details={"pura_id": body.pura_id})
    new_id = repo.insert_ceremony(
        banjar_id=banjar_uuid,
        pura_id=pura_uuid,
        class_=ceremony_class,
        title=body.title,
        external_handle=body.external_handle or _default_handle(body),
        visibility=body.visibility,
        scheduled_for=body.scheduled_for,
        created_by_actor_id=actor_uuid,
    )
    return {"id": str(new_id), "created": True}


def _default_handle(body: CeremonyCreateBody) -> str:
    """fallback handle: nanoid-shaped (caller should supply one)."""
    suffix = uuid.uuid4().hex[:8]
    return f"CR-AUTO-{suffix}"


@router.post("/ceremonies/{ceremony_id}/state")
def append_ceremony_state(
    ceremony_id: str,
    body: StateTransitionBody,
    *,
    repo: CeremonyRepo = Depends(repo_dep),
    identity: Optional[JwtIdentity] = Depends(identity_dep),
) -> dict:
    """append-only state transition."""
    _require_scope(identity, "ceremony:transition")
    try:
        cid = uuid.UUID(ceremony_id)
    except ValueError:
        raise BadRequest("ceremony_id must be a uuid", details={"id": ceremony_id})
    try:
        actor_uuid = uuid.UUID(identity.actor_id)
    except ValueError:
        actor_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, identity.actor_id)
    try:
        evidence_uuid = uuid.UUID(body.evidence_blob_id) if body.evidence_blob_id else None
    except ValueError:
        raise BadRequest("evidence_blob_id must be a uuid", details={"id": body.evidence_blob_id})
    new_id = repo.append_state(
        ceremony_id=cid,
        state=body.state,
        reason=body.reason,
        actor_id=actor_uuid,
        source_url=body.source_url,
        evidence_blob_id=evidence_uuid,
    )
    return {"id": str(new_id), "appended": True}


@router.get("/ceremonies/{ceremony_id}/provenance")
def list_provenance(
    ceremony_id: str,
    *,
    repo: CeremonyRepo = Depends(repo_dep),
    identity: Optional[JwtIdentity] = Depends(identity_dep),
) -> dict:
    """list authority links.  config-driven visibility."""
    _require_scope(identity, "ceremony:provenance")
    try:
        cid = uuid.UUID(ceremony_id)
    except ValueError:
        raise BadRequest("ceremony_id must be a uuid", details={"id": ceremony_id})
    rows = repo.list_authority_links(cid)
    return {"ceremony_id": str(cid), "links": rows}


__all__ = ["router"]
