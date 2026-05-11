# KVTC V7 Integration

This repository now includes an **optional** local KVTC V7 compression path for deterministic demos and synthetic benchmarks. The existing `IndustrialKVTCStrategy` remains the default strategy for the main API pipeline and is not replaced.

## Why V7 is optional

KVTC V7 is integrated as a comparison strategy so reviewers can benchmark a dependency-light V7-style frame against the current Industrial KVTC approach without changing production-facing behavior. Keeping it optional reduces rollout risk and preserves all existing `/compress`, `/analyze`, and showcase routes.

## IndustrialKVTCStrategy vs KVTCV7Strategy

| Strategy | Role | Frame style | Payload policy |
| --- | --- | --- | --- |
| `IndustrialKVTCStrategy` | Existing Daimler experiment default | Industrial K/V/T/C layers and header/middle/window zones | Existing behavior |
| `KVTCV7Strategy` | Optional V7 benchmark/demo path | Deterministic JSON `micro-frame` or `sandwich-frame` | No raw lines; stores counts, categories, fingerprints, and safe metadata |

`KVTCV7Strategy` wraps the local V7 engine and maps its result into the existing `KVTCResult` shape: `original_tokens`, `compressed_tokens`, `token_reduction_pct`, `frame`, `checksum`, and `latency_ms`.

## Relationship to ProfRandom92/Comptextv7

The feature branch attempted to inspect `ProfRandom92/Comptextv7` from the sandbox, but GitHub access was unavailable in this environment. The local implementation therefore adapts the requested V7 concepts directly in this repository: `KVTCV7Engine`, `StructuredLogEvent`, deterministic fingerprints, severity counts, micro-frame handling, and sandwich-frame summaries.

## New API routes

- `POST /compress/v7` compresses caller-provided text through `KVTCV7Strategy` and returns the same public response fields as `/compress`.
- `GET /benchmark/v7` runs V7 against built-in synthetic fixtures only.
- `GET /benchmark/compare` runs both `IndustrialKVTCStrategy` and `KVTCV7Strategy` on the same built-in synthetic fixtures.

The original `POST /compress` route remains unchanged and continues to use the Industrial strategy.

## Benchmark comparison semantics

`GET /benchmark/compare` returns a `cases` array with Industrial metrics, V7 metrics, V7 frame metadata, and a conservative `decision`:

- `pass`: structured synthetic coverage is adequate for a directional comparison.
- `warn`: the input is very short, high-level, or has low structured-signal coverage.
- `fail`: reserved for future validation failures; the endpoint is designed to avoid network and data dependencies.

Every case includes a `caveat`. Deltas compare token-reduction percentages only; they do not claim production accuracy or model quality.

## Synthetic-data-only policy

V7 benchmark endpoints use only synthetic fixtures embedded in the code. Do not add real Daimler data, secrets, raw production logs, proprietary customer payloads, cookies, tokens, or private customer identifiers to the tests, docs, or benchmark fixtures.

The V7 frame intentionally excludes raw lines and stores safe metadata such as hashes, event counts, severity counts, and signal counts.

## What V7 proves

- The optional V7 path is deterministic for identical input.
- A dependency-light Python 3.11+ engine can generate stable JSON frames.
- Diagnostic-like synthetic logs expose useful metadata such as severity counts and event counts.
- The API/dashboard can benchmark V7 next to the Industrial strategy without network access.

## What V7 does not prove

- It does not prove production Daimler compression performance.
- It does not validate behavior on real customer data.
- It does not replace the existing Industrial strategy.
- It does not require or demonstrate external API/model access.

## Dashboard compatibility

Future dashboard work can consume `GET /benchmark/compare` to populate a comparison table in the Benchmark Evidence Center. The route is stable, synthetic-only, and returns both Industrial and V7 metrics per case, so no large UI rewrite is needed in this integration PR.
