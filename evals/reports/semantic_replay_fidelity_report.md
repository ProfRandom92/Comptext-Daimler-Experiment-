# Semantic Replay Fidelity Report

Positioning: **semantic replay fidelity under constrained context budgets**.

This report evaluates semantic continuity, operational memory retention, replay consistency, architectural stability, and long-context reasoning continuity. It is not a token reduction benchmark.

## Summary

- Truth retention score: `0.94`
- Replay question score: `1.0`
- Contradiction count: `0`
- Drift category count: `0`

## Retention Report

- `cloud_first_workflow_required` (workflow_constraint): 1.0 via cloud, Render, Vercel, Docker, CI
- `replay_validation_exists` (replay_continuity): 1.0 via replay, validation, evidence
- `semantic_drift_tracking_exists` (semantic_continuity): 1.0 via semantic, drift, regression
- `benchmark_evidence_pipeline_exists` (evidence_pipeline): 1.0 via benchmark, evidence, JSON, Markdown, contract
- `no_fake_production_claims` (workflow_constraint): 0.75 via production, claims, evidence
- `replay_consistency_matters` (replay_continuity): 1.0 via replay, consistency, compressed, contradiction
- `architectural_continuity_matters` (architectural_continuity): 0.833 via API, KVTC, showcase, telemetry, validation

## Replay Consistency Report

- `q_positioning`: 1.0 via semantic replay fidelity, constrained context budgets
- `q_cloud_first`: 1.0 via cloud-first, CI, deployability
- `q_evidence`: 1.0 via benchmark, JSON, Markdown, reports
- `q_replay`: 1.0 via replay, consistency, contradiction, retention
- `q_architecture`: 1.0 via API, KVTC, showcase, telemetry, validation

## Contradiction Detection

- No contradiction markers found in replay answers.

## Semantic Drift Report

- No categories fell below the configured retention threshold.

## Architectural Continuity Report

- Continuity anchors: API contracts, KVTC strategies, telemetry, showcase evidence center, benchmark/regression reports, and validation scripts.
- Workflow anchors: cloud-first deployability, CI stability, reproducible JSON/Markdown outputs, and evidence-backed claims.

## Reproducible Artifacts

- Dataset: `evals/datasets/engineering_activity_replay_dataset.json`
- Truths: `evals/truths/must_retain_truths.json`
- Compressed state: `evals/compressed/compressed_replay_state.json`
- Replay answers: `evals/replay/replay_answers.json`
- Scores: `evals/reports/replay_scores.json`
