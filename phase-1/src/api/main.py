"""fastapi app entry — exposes DSP endpoints + health + openapi."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from dewatacalendar.dsp import router as calendar_router
from dewatacalendar.rulesets import RULESET_VERSION


def create_app() -> FastAPI:
    app = FastAPI(
        title="Dewata Spatial Protocol (DSP) v0.1",
        version="0.1.0",
        description="Balinese calendrical engine + DSP endpoints (read-only v0.1).",
    )
    app.include_router(calendar_router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "ruleset": RULESET_VERSION}

    @app.get("/")
    def root() -> JSONResponse:
        return JSONResponse({
            "name": "dewata-api",
            "version": "0.1.0",
            "ruleset": RULESET_VERSION,
            "endpoints": [
                "/health",
                "/dsp/v0.1/calendar/ruleset",
                "/dsp/v0.1/calendar/date/{YYYY-MM-DD}",
                "/dsp/v0.1/calendar/range?start=&end=&fmt=",
            ],
        })

    return app


app = create_app()
