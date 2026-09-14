"""consistent error envelopes for the dewata api.

all error responses use the same JSON shape:

  {
    "error": "error_code",
    "message": "human-readable message",
    "details": { ... },
    "request_id": "..."
  }

the envelope is:

  - referenceable (machine code in `error`)
  - safe (no protected fields leak, no stack traces)
  - log-friendly (every error has a request_id)
  - stable (clients can rely on the schema)

use `error_response()` from any handler to render a Response with the
right Content-Type and headers.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse


log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ErrorEnvelope:
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
            "request_id": self.request_id,
        }


class ApiError(Exception):
    """raise this from any handler to produce a consistent envelope."""

    status: int = 400
    code: str = "bad_request"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status: int | None = None,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.code
        self.status = status or self.status
        self.details = details or {}


class NotFound(ApiError):
    status = 404
    code = "not_found"


class Forbidden(ApiError):
    status = 403
    code = "forbidden"


class Unauthorized(ApiError):
    status = 401
    code = "unauthorized"


class BadRequest(ApiError):
    status = 400
    code = "bad_request"


class Conflict(ApiError):
    status = 409
    code = "conflict"


class TooManyRequests(ApiError):
    status = 429
    code = "rate_limited"


def error_response(
    code: str,
    message: str,
    *,
    status: int = 400,
    details: dict | None = None,
    request_id: str | None = None,
) -> Response:
    """render an error envelope as a `JSONResponse`."""
    env = ErrorEnvelope(
        code=code, message=message, details=details or {},
        request_id=request_id or str(uuid.uuid4()),
    )
    return JSONResponse(status_code=status, content=env.to_dict())


def install_error_handlers(app: FastAPI) -> None:
    """register exception handlers on a FastAPI app."""

    @app.exception_handler(ApiError)
    async def _api_error_handler(request: Request, exc: ApiError) -> Response:
        return error_response(
            code=exc.code,
            message=exc.message,
            status=exc.status,
            details=exc.details,
        )

    @app.exception_handler(Exception)
    async def _unhandled_handler(request: Request, exc: Exception) -> Response:
        # log with NO sensitive content (see redaction in
        # dewatacalendar.security.redact_log_string)
        log.exception("unhandled api error: %s", type(exc).__name__)
        return error_response(
            code="internal_error",
            message="an internal error occurred",
            status=500,
        )


__all__ = [
    "ApiError", "NotFound", "Forbidden", "Unauthorized",
    "BadRequest", "Conflict", "TooManyRequests",
    "error_response", "install_error_handlers",
    "ErrorEnvelope",
]
