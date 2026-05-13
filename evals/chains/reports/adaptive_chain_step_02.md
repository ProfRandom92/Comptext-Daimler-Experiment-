# Replay Chain Step 02

This step evaluates one deterministic compression/replay cycle in the iterative replay chain.

## Metrics

- truth_retention_score: `0.805`
- retention_decay: `0.0`
- contradiction_count: `0`
- contradiction_accumulation: `0`
- semantic_drift_growth: `0.167`
- constraint_survival_rate: `1.0`
- architectural_continuity_score: `1.0`
- replay_consistency_score: `0.933`
- goal_continuity_score: `1.0`
- drift_stabilization_delta: `0.066`
- replay_recovery_score: `0.167`
- pinned_truth_retention: `1.0`
- adaptive_continuity_score: `0.948`
- contradiction_reduction: `0`

## Stability Flags

- constraints_collapsed: `False`
- architecture_changed: `False`
- goals_mutated: `False`
- replay_unstable: `False`

## Constraint Retention

- `cloud_first_workflow_required` (workflow_constraint): `1.0` via cloud, Render, Vercel, Docker, CI
- `replay_validation_exists` (replay_continuity): `1.0` via replay, validation, evidence
- `semantic_drift_tracking_exists` (semantic_continuity): `0.333` via semantic
- `benchmark_evidence_pipeline_exists` (evidence_pipeline): `0.8` via benchmark, evidence, JSON, Markdown
- `no_fake_production_claims` (workflow_constraint): `0.5` via evidence, sanitization
- `replay_consistency_matters` (replay_continuity): `1.0` via replay, consistency, compressed, contradiction
- `architectural_continuity_matters` (architectural_continuity): `1.0` via architecture, API, KVTC, showcase, telemetry, validation

## Replay Consistency

- `q_positioning`: `1.0` via semantic replay fidelity, constrained context budgets
- `q_cloud_first`: `0.667` via cloud-first, CI
- `q_evidence`: `1.0` via benchmark, JSON, Markdown, reports
- `q_replay`: `1.0` via replay, consistency, contradiction, retention
- `q_architecture`: `1.0` via API, KVTC, showcase, telemetry, validation
