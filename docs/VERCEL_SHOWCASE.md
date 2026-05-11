# Vercel showcase deployment

Vercel is the preferred target for the high-end benchmark showcase frontend. Render can remain the FastAPI/Docker backend while Vercel serves the React UI from the edge.

## Recommended Vercel project settings

Create a new Vercel project from this repository with:

| Setting | Value |
| --- | --- |
| Framework Preset | Vite |
| Root Directory | `showcase` |
| Install Command | `npm ci` |
| Build Command | `npm run build` |
| Output Directory | `dist` |

`showcase/vercel.json` also documents the build command, output directory, and SPA rewrite.

## API backend

Set this Vercel environment variable when the FastAPI backend is hosted elsewhere:

```text
VITE_API_BASE_URL=https://comptext-daimler-api-jules.onrender.com
```

If `VITE_API_BASE_URL` is unset, the showcase uses same-origin paths such as `/analyze`, `/health`, and `/benchmark`. That mode is useful when the frontend is bundled into the Docker/FastAPI service.

## Why Vercel for the showcase

- Better static frontend hosting than a sleeping free Docker service.
- Faster global edge delivery for reviewer-facing UI.
- Cleaner preview deployments per pull request.
- Frontend can evolve independently from the FastAPI backend.
- Render can remain a backend-only API target if needed.

## Safety

- No secrets are required for the static showcase.
- The frontend uses synthetic default payloads only.
- No real Daimler data, raw production logs, tokens, cookies, or proprietary documents are included.
- API URLs must be configured as environment variables, not hard-coded secrets.
