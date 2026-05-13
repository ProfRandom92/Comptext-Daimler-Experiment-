# Benchmark Methodology

This project measures the behavior of a semantic compression and analysis pipeline with synthetic inputs. The methodology favors reproducibility, safety, and comparability over optimistic headline metrics.

## Objectives

Benchmarks should answer four questions:

1. How many approximate input tokens were reduced before inference?
2. What latency did the compression or endpoint path add?
3. Did generated artifacts keep the expected report contract?
4. Did a change produce a clear regression against the latest synthetic baseline?

## What is measured

| Metric | Meaning | Caveat |
|---|---|---|
| Original tokens | estimated token count before compression | current estimator is approximate |
| Compressed tokens | estimated token count after KVTC serialization | should be validated against target model tokenizers for production |
| Token reduction | `1 - compressed / original` | not equivalent to semantic quality |
| Latency | wall-clock runtime for compression or endpoint path | noisy on shared CI runners |
| Error rate | failed requests during live load mode | meaningful only with a running target service |
| Report status | whether scripts produced expected Markdown/JSON artifacts | contract health, not model quality |

## Local benchmark flow

```bash
python -m py_compile scripts/run_benchmarks.py scripts/generate_regression_report.py scripts/sanitize_fixtures.py scripts/validate_report_contracts.py
python scripts/run_benchmarks.py
python scripts/generate_regression_report.py
python scripts/sanitize_fixtures.py
python scripts/validate_report_contracts.py
```

`run_benchmarks.py` is CI-friendly. If Locust is unavailable, it still writes an artifact with status `tool_unavailable` so report generation and contract validation can be tested without optional load-testing dependencies.

## Live endpoint mode

Start a local API separately and run:

```bash
LLM_BACKEND=mock uvicorn api:app --port 8000
python scripts/run_benchmarks.py --host http://localhost:8000 --endpoint /analyze
python scripts/generate_regression_report.py
```

Use mock mode for baseline comparisons unless the purpose of the benchmark is explicitly model-backend evaluation.

## Interpreting results

- A high token-reduction percentage is useful only if semantic retention remains sufficient for the task.
- p95 and p99 latency should be compared over repeated runs; single-run tail latency can be misleading.
- Non-zero error rates require inspection before conclusions are drawn.
- Synthetic benchmarks should be labeled as synthetic and should not be generalized to production without representative evaluation.

## Semantic retention evaluation plan

The current repository does not yet include a full gold-set retention harness. A credible next step is to add fixtures with expected retained fields:

| Fixture type | Expected retained signals |
|---|---|
| Diagnostic log | OBD codes, active symptoms, safety-critical words, mileage |
| Shift report | station, deviation type, blocked step, timestamp |
| QA note | defect category, part identifier, severity, disposition |
| Supply-chain update | supplier, part number, delay reason, ETA |

A retention test should fail if required codes or fields disappear from the frame or if deterministic triage changes unexpectedly.

## Safety rules

- Do not benchmark with real customer documents.
- Do not commit raw production logs, secrets, cookies, bearer tokens, VINs, or employee identifiers.
- Sanitize generated artifacts before review.
- Keep benchmark reports small enough for code review.
