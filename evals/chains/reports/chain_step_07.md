# Replay Chain Step 07

This step evaluates one deterministic compression/replay cycle in the iterative replay chain.

## Metrics

- truth_retention_score: `0.564`
- retention_decay: `0.217`
- contradiction_count: `0`
- contradiction_accumulation: `0`
- semantic_drift_growth: `0.433`
- constraint_survival_rate: `0.714`
- architectural_continuity_score: `0.667`
- replay_consistency_score: `0.637`
- goal_continuity_score: `1.0`
- drift_stabilization_delta: `0.0`
- replay_recovery_score: `0.662`
- pinned_truth_retention: `0.636`
- adaptive_continuity_score: `0.703`

## Stability Flags

- constraints_collapsed: `False`
- architecture_changed: `False`
- goals_mutated: `False`
- replay_unstable: `False`

## Constraint Retention

- `cloud_first_workflow_required` (workflow_constraint): `0.8` via cloud, Render, Vercel, Docker
- `replay_validation_exists` (replay_continuity): `0.667` via replay, evidence
- `semantic_drift_tracking_exists` (semantic_continuity): `0.333` via semantic
- `benchmark_evidence_pipeline_exists` (evidence_pipeline): `0.4` via benchmark, evidence
- `no_fake_production_claims` (workflow_constraint): `0.25` via evidence
- `replay_consistency_matters` (replay_continuity): `1.0` via replay, consistency, compressed, contradiction
- `architectural_continuity_matters` (architectural_continuity): `0.5` via API, KVTC, showcase

## Replay Consistency

- `q_positioning`: `1.0` via semantic replay fidelity, constrained context budgets
- `q_cloud_first`: `0.333` via cloud-first
- `q_evidence`: `0.25` via benchmark
- `q_replay`: `1.0` via replay, consistency, contradiction, retention
- `q_architecture`: `0.6` via API, KVTC, showcase
