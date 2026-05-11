# Benchmark Workflow

This repository is the experiment, benchmark, forensic replay, and synthetic fixture companion for `ProfRandom92/Comptextv7`. The benchmark workflow exists to measure Comptext runtime behavior with safe synthetic inputs before changes are promoted back to the main application repository.

## Purpose

The workflow provides a deterministic, reviewable way to:

- Exercise a Comptext-compatible endpoint with synthetic benchmark traffic.
- Capture latency, throughput, and error-rate metrics in Markdown reports under `docs/reports/`.
- Keep Daimler-related context safe by excluding real payloads, raw production logs, secrets, cookies, bearer tokens, and proprietary customer data.
- Give future agents a repeatable baseline for regression review without requiring access to real Daimler systems.

## Local setup

Python 3.11 or newer is required. The scripts use the Python standard library by default. Locust is optional and is only needed for live load generation.

```bash
python -m py_compile scripts/run_benchmarks.py scripts/generate_regression_report.py scripts/sanitize_fixtures.py
python scripts/sanitize_fixtures.py
python scripts/generate_regression_report.py
```

To run a live synthetic benchmark against a local Comptextv7 service, start the service separately and then run:

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

## Relationship to `ProfRandom92/Comptextv7`

`ProfRandom92/Comptextv7` is the main application/runtime repository. This repository should not duplicate production data from that runtime. Instead, it should hold synthetic fixtures, benchmark harnesses, forensic replay procedures, and regression reports that can guide safe changes back into Comptextv7.

When a benchmark or replay finding suggests a runtime issue, open or update the matching Comptextv7 issue with sanitized reproduction steps, synthetic input shape, observed metrics, and links to the relevant experiment reports. Do not copy raw Daimler payloads into either repository.

## Expected reports

Benchmark reports are written to `docs/reports/benchmark-report-<timestamp>.md`. Each report includes:

- Host and endpoint.
- User count, spawn rate, and duration.
- Benchmark status.
- p50, p95, and p99 latency values when available.
- Requests per second (RPS) when available.
- Error rate when available.
- Environment notes and safety notes.

The regression summary is written to `docs/reports/regression-summary.md` and summarizes available benchmark runs using a conservative policy.

## Interpreting metrics

- **p50 latency** is the median response time. Half of measured requests were faster, and half were slower.
- **p95 latency** is the 95th percentile response time. It is useful for understanding slower user-visible behavior without focusing only on the worst outliers.
- **p99 latency** is the 99th percentile response time. It highlights tail latency and should be reviewed carefully because it can also be noisy in small runs.
- **RPS** means requests per second and approximates throughput under the selected user count, spawn rate, and duration.
- **Error rate** is the percentage of failed requests. Any non-zero value should be reviewed, but CI should fail only when comparable baseline data shows a clear regression.

## When Locust is unavailable

`run_benchmarks.py` detects whether the `locust` executable is available. If Locust is missing, the script still writes a timestamped Markdown report with status `tool unavailable`. This is intentional for CI-friendly behavior: contributors can validate report generation without installing optional load-testing tools or starting a live server.

To enable live benchmark execution locally, install Locust in your own environment and rerun the benchmark command. Keep dependency installation outside committed reports and never add generated secrets, cookies, or real customer data.
