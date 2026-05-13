# Benchmark Workflow

This repository is the experiment, benchmark, forensic replay, and synthetic fixture environment for CompText semantic-compression research. The benchmark workflow exists to measure runtime behavior with safe synthetic inputs before changes are presented for review or promoted into downstream applications.

## Purpose

The workflow provides a deterministic, reviewable way to:

- Exercise a Comptext-compatible endpoint with synthetic benchmark traffic.
- Capture latency, throughput, and error-rate metrics in Markdown reports under `docs/reports/`.
- Keep Daimler-related context safe by excluding real payloads, raw production logs, secrets, cookies, bearer tokens, and proprietary customer data.
- Give future agents a repeatable baseline for regression review without requiring access to real Daimler systems.

## Local setup

Python 3.11 or newer is required. The scripts use the Python standard library by default. Locust is optional and is only needed for live load generation.

```bash
python -m py_compile scripts/run_benchmarks.py scripts/generate_regression_report.py scripts/sanitize_fixtures.py scripts/validate_report_contracts.py
python scripts/run_benchmarks.py
python scripts/generate_regression_report.py
python scripts/sanitize_fixtures.py
python scripts/validate_report_contracts.py
```

To run a live synthetic benchmark against a local service, start the service separately and then run:

```bash
python scripts/run_benchmarks.py --host http://localhost:8000 --endpoint /analyze
python scripts/generate_regression_report.py
```

Custom benchmark parameters are supported:

```bash
python scripts/run_benchmarks.py \
  --host http://localhost:8000 \
  --users 50 \
  --spawn-rate 10 \
  --duration 15s \
  --endpoint /analyze \
  --output-dir docs/reports
```

## Relationship to downstream runtimes

This repository should not duplicate production data from any runtime system. It should hold synthetic fixtures, benchmark harnesses, forensic replay procedures, and regression reports that can guide safe changes into downstream applications.

When a benchmark or replay finding suggests a runtime issue, document sanitized reproduction steps, synthetic input shape, observed metrics, and links to the relevant experiment reports. Do not copy raw Daimler payloads, customer documents, or proprietary logs into this repository.

## Expected reports

Benchmark reports are written to `docs/reports/benchmark-report-<timestamp>.md`. Each report includes:

- Host and endpoint.
- User count, spawn rate, and duration.
- Benchmark status.
- p50, p95, and p99 latency values when available.
- Requests per second (RPS) when available.
- Error rate when available.
- Environment notes and safety notes.

The workflow also writes contract-compatible JSON summaries aligned with downstream machine-readable report contracts, without importing runtime code or requiring a separate checkout:

- `docs/reports/benchmark-summary.json` contains the latest synthetic endpoint metrics, status, payload size, and notes.
- `docs/reports/regression-summary.json` contains baseline availability, compared runs, thresholds, decision, and notes.
- `docs/reports/sanitization-summary.json` contains scanned path names, masked-finding counts, status, and safety notes.

The regression Markdown summary is written to `docs/reports/regression-summary.md` and summarizes available benchmark runs using a conservative policy. Validate all JSON summaries with:

```bash
python scripts/validate_report_contracts.py
```

Validation writes `docs/reports/report-contract-validation-report.md`.

## Interpreting metrics

- **p50 latency** is the median response time. Half of measured requests were faster, and half were slower.
- **p95 latency** is the 95th percentile response time. It is useful for understanding slower user-visible behavior without focusing only on the worst outliers.
- **p99 latency** is the 99th percentile response time. It highlights tail latency and should be reviewed carefully because it can also be noisy in small runs.
- **RPS** means requests per second and approximates throughput under the selected user count, spawn rate, and duration.
- **Error rate** is the percentage of failed requests. Any non-zero value should be reviewed, but CI should fail only when comparable baseline data shows a clear regression.

## When Locust is unavailable

`run_benchmarks.py` detects whether the `locust` executable is available. If Locust is missing, the script still writes a timestamped Markdown report and `docs/reports/benchmark-summary.json` with status `tool_unavailable`. This is intentional for CI-friendly behavior: contributors can validate report generation without installing optional load-testing tools or starting a live server.

To enable live benchmark execution locally, install Locust in your own environment and rerun the benchmark command. Keep dependency installation outside committed reports and never add generated secrets, cookies, or real customer data.


## Synthetic-only compatibility policy

Contract-compatible summaries are synthetic-safe handoff artifacts. They must not contain real Daimler data, customer identifiers, secrets, cookies, bearer tokens, raw production logs, or proprietary documents. Keep summaries small and structural so downstream validation can consume them without runtime coupling.
