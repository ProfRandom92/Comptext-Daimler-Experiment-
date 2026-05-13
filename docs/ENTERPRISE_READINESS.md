# Enterprise Readiness Notes

This document separates implemented engineering evidence from work that would still be required before production deployment.

## Evidence already present

| Area | Evidence |
|---|---|
| API contracts | FastAPI request/response models and endpoint tests |
| Determinism | mock backend and deterministic triage path |
| Privacy boundary | intake-layer masking and telemetry allow-listing |
| Reproducibility | benchmark, regression, sanitization, and contract-validation scripts |
| CI | Python lint/tests/coverage, React build, Docker build, benchmark checks |
| Deployment paths | Docker, Render configuration, Vercel/showcase configuration |

## Production hardening still required

| Area | Required next work |
|---|---|
| Security | independent threat model, dependency review, abuse-case tests, rate limits |
| Data governance | approved data classification, retention policy, DPA/vendor review |
| Model governance | model-card selection, evaluation criteria, rollback plan, prompt review |
| Semantic quality | labeled gold sets, retention metrics, false-positive/false-negative triage review |
| Operations | SLOs, dashboards, alerting, incident runbooks, capacity testing |
| Compliance | legal review before any claim of certification or regulated deployment readiness |

## Enterprise reviewer questions this repo should answer

1. What exactly is sent to the model after compression?
2. Can a reviewer reproduce the benchmark artifacts without private data?
3. What data is emitted to telemetry?
4. How does the system behave when compression loses context?
5. Which claims are measured, and which claims are roadmap items?

## Recommended demo path

1. Run the API with `LLM_BACKEND=mock`.
2. Send a synthetic diagnostic note to `/compress` and inspect the frame.
3. Send the same note to `/triage` and inspect rule hits.
4. Run `/analyze` and verify the checksum-linked result.
5. Generate benchmark artifacts and contract-validation reports.
6. Show the React showcase only after the backend behavior is understood.
