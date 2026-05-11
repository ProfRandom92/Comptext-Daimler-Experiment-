"""Render entrypoint that serves the FastAPI API and built React showcase.

The main API stays in api.py. This wrapper is used by Render/Docker so the
single web service can expose both API routes and the static showcase built into
showcase/dist by the Dockerfile.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from api import app

ROOT = Path(__file__).resolve().parent
DIST_DIR = ROOT / "showcase" / "dist"
ASSETS_DIR = DIST_DIR / "assets"
INDEX_HTML = DIST_DIR / "index.html"

RESERVED_PREFIXES = (
    "api/",
    "v1/",
    "batch/",
    "docs",
    "redoc",
    "openapi.json",
    "health",
    "stats",
    "benchmark",
    "compress",
    "triage",
    "analyze",
)

if ASSETS_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="showcase-assets")


def _showcase_unavailable() -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "status": "showcase unavailable",
            "detail": "React showcase build artifact was not found.",
            "expected_path": "showcase/dist/index.html",
            "recovery_hint": "Run `cd showcase && npm ci && npm run build` before starting render_app:app.",
        },
    )


def _serve_index() -> Response:
    if INDEX_HTML.is_file():
        return FileResponse(INDEX_HTML)
    return _showcase_unavailable()


@app.get("/", include_in_schema=False, response_model=None)
def showcase_root() -> Response:
    """Serve the built React showcase at the service root."""
    return _serve_index()


@app.get("/{full_path:path}", include_in_schema=False, response_model=None)
def showcase_spa_fallback(full_path: str) -> Response:
    """Serve static showcase files or fall back to index.html for SPA routes.

    API-like paths are left as 404s so missing backend endpoints do not get
    masked by the React fallback.
    """
    normalized = full_path.strip("/")
    if not normalized:
        return _serve_index()
    if normalized.startswith(RESERVED_PREFIXES):
        raise HTTPException(status_code=404, detail="Not found")

    target = (DIST_DIR / normalized).resolve()
    try:
        target.relative_to(DIST_DIR.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Not found") from exc

    if target.is_file():
        return FileResponse(target)
    return _serve_index()
