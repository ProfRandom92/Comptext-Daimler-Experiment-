# Render showcase deployment

The Render web service uses a single Docker image to serve both:

- the FastAPI API endpoints from `api.py`
- the built React showcase from `showcase/dist`

## Entrypoint

Render starts:

```bash
uvicorn render_app:app --host 0.0.0.0 --port $PORT --workers 2
```

`render_app.py` imports the existing FastAPI app from `api.py`, mounts built Vite assets from `showcase/dist/assets`, serves the React app at `/`, and falls back to `index.html` for non-API SPA routes.

API-like paths such as `/api/*`, `/v1/*`, `/health`, `/docs`, `/openapi.json`, `/analyze`, `/compress`, and `/triage` are not masked by the SPA fallback. Missing API routes still return `404`.

## Docker build

The Dockerfile is multi-stage:

1. Node stage:
   - runs `npm ci` in `showcase/`
   - runs `npm run build`
   - produces `showcase/dist`
2. Python runtime stage:
   - installs Python dependencies
   - copies the repository
   - copies the built showcase into `showcase/dist`
   - runs `uvicorn render_app:app`

## Validation

GitHub Actions validates:

```bash
cd showcase && npm ci && npm run build
python - <<'PY'
from pathlib import Path
from fastapi.testclient import TestClient
import render_app

assert Path('showcase/dist/index.html').is_file()
client = TestClient(render_app.app)
assert client.get('/').status_code == 200
assert client.get('/health').status_code == 200
assert client.get('/api/does-not-exist').status_code == 404
PY
docker build -t comptext-daimler:ci .
```

## Safety

- No real Daimler data is required.
- No secrets are committed.
- `TINYBIRD_TOKEN` is configured as `sync: false` in `render.yaml`.
- The showcase is built from repository-local static assets only.
