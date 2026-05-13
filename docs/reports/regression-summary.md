# Regression Summary

Generated: 2026-05-13T14:12:48+00:00 UTC

## Conservative policy status

**Decision:** no_clear_regression

- p95 comparison unavailable; missing numeric baseline or latest values.
- Error-rate comparison unavailable; missing numeric baseline or latest values.

## Contract-compatible JSON summary

This run also writes `docs/reports/regression-summary.json` for machine-readable contract validation.

## Benchmark runs

| Generated | Status | Host | Endpoint | p50 | p95 | p99 | RPS | Error rate | Report |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-11T09:46:40+00:00 | tool_unavailable | http://localhost:8000 | /analyze | unavailable | unavailable | unavailable | unavailable | unavailable | docs/reports/benchmark-report-20260511T094640Z.md |
| 2026-05-13T14:12:41+00:00 | tool_unavailable | http://localhost:8000 | /analyze | unavailable | unavailable | unavailable | unavailable | unavailable | docs/reports/benchmark-report-20260513T141241Z.md |

## Regression policy

- Fail only on clear regressions when comparable baseline data exists.
- Treat missing baselines, unavailable tools, and non-numeric metrics as insufficient baseline rather than failure.
- Prefer warning and human review when benchmark changes may be caused by CI noise or missing local services.
- Keep all benchmark inputs synthetic and exclude raw payloads, secrets, cookies, and customer data.
