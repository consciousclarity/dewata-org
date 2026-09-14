"""ceremony API domain types.

these pydantic-like dataclasses (built without pydantic so the
schema layer stays small and explicit; we use stdlib dataclasses
with `asdict` instead).

the schema here is a *redacted* view of the underlying db.  the
redaction is enforced by the repo layer (`ceremony/repo.py`) which
filters fields based on the visibility tier and the requester's
claims.

visibility:
  - public:   only the row's projection to a public-domain-safe subset
  - banjar:   plus banjar-internal notes
  - desa_adat: plus regional admin notes
  - restricted: full record with authz-required confirmation
  - private:  only metadata, never the body
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class CeremonyPublic:
    id: str
    external_handle: str
    title: str
    class_: str   # `class` is reserved in python; renamed
    banjar_id: str
    pura_id: Optional[str] = None
    scheduled_for: Optional[str] = None
    visibility: str = "banjar"
    state_phase: str = "predicted"
    computed_by_ruleset: Optional[str] = None
    actor_provenance_count: int = 0
    evidence_count: int = 0
    # explicit "provenance label" so consumers can flag this as
    # computed, registered, predicted, provisional, or verified.
    # never synthesize the wrong label.
    provenance_label: str = "registered"
    created_at: str = ""
    updated_at: str = ""


@dataclass
class CeremonyBanjar(CeremonyPublic):
    """banjar-tier projection: adds banjar-internal notes."""
    banjar_internal_notes: Optional[str] = None


@dataclass
class CeremonyRestricted(CeremonyBanjar):
    """restricted-tier projection: adds delegated authority row."""
    delegated_authorities: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class CeremonyCreate:
    """request body for `POST /ceremony`.

    validation:
      - `class_` must be one of the schema's ceremony_class enum values
      - `scheduled_for` parses as ISO date or raises 400
    """
    title: str
    class_: str
    banjar_id: str
    pura_id: Optional[str] = None
    scheduled_for: Optional[str] = None
    visibility: str = "banjar"
    external_handle: Optional[str] = None


@dataclass
class CeremonyStateTransition:
    """request body for `POST /ceremony/{id}/state`.

    append-only.  state transitions are validated against the state
    machine in `dewatacalendar.security` (configurable).
    """
    state: str
    reason: Optional[str] = None
    source_url: Optional[str] = None
    evidence_blob_id: Optional[str] = None


__all__ = [
    "CeremonyPublic", "CeremonyBanjar", "CeremonyRestricted",
    "CeremonyCreate", "CeremonyStateTransition",
]
