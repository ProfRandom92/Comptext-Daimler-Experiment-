# Regression Policy

This policy defines how benchmark results in this experiment repository should be reviewed before findings are promoted to `ProfRandom92/Comptextv7`.

## Baseline definition

A baseline is the most recent comparable benchmark report generated with the same endpoint, similar host class, user count, spawn rate, duration, and synthetic payload shape. Baselines must come from `docs/reports/benchmark-report-<timestamp>.md` files and must not rely on real Daimler data.

If no comparable prior run exists, the result has insufficient baseline data. It may still be useful for trend discovery, but it should not fail CI.

## Regression thresholds

Use conservative thresholds because short CI-friendly benchmark runs can be noisy:

- Treat a p95 latency increase of 25% or more against a comparable baseline as a regression candidate.
- Treat an error-rate increase of at least 1 percentage point, when the latest error rate is above 1%, as a regression candidate.
- Treat missing p50, p95, p99, RPS, or error-rate values as insufficient data unless the missing metric itself is the behavior under investigation.
- Prefer repeated confirmation before labeling p99-only changes as regressions because tail latency is sensitive to machine noise.

## When CI should fail

CI should fail only on clear regressions when comparable baseline data exists and the signal is strong enough to outweigh benchmark noise. Examples include repeated p95 degradation above the threshold, a meaningful error-rate increase, or a benchmark status that changes from successful to consistently failing under the same synthetic conditions.

The initial workflow is intentionally report-oriented and conservative. It generates summaries that future maintainers can extend into hard gates once stable baselines exist.

## When CI should warn only

CI should warn, report, or request human review when:

- Locust is unavailable and the benchmark status is `tool unavailable`.
- No live local server is available.
- Fewer than two benchmark reports exist.
- The latest run uses different users, spawn rate, duration, endpoint, or host characteristics.
- Metrics are missing, non-numeric, or clearly affected by CI resource contention.
- The change is limited to documentation, sanitizer rules, or benchmark harness maintenance.

## Reviewing benchmark changes

Reviewers should confirm that:

- Reports use synthetic payloads only.
- No secrets, cookies, bearer tokens, raw customer data, or real Daimler payloads are included.
- Benchmark parameters are documented and comparable to the intended baseline.
- Regression summaries explain whether a failure, warning, or insufficient-baseline state is appropriate.
- Findings that affect runtime behavior are filed or linked back to `ProfRandom92/Comptextv7` with sanitized reproduction steps.

## Avoiding false positives

To avoid false positives:

- Compare like-for-like benchmark runs.
- Prefer p95 and error rate over single outlier values.
- Repeat suspicious runs locally before opening a blocking runtime issue.
- Keep synthetic payloads stable unless the purpose of the change is to test a new scenario.
- Do not treat unavailable optional tools as runtime regressions.
- Avoid network-dependent CI assumptions beyond normal tool and dependency checks.
