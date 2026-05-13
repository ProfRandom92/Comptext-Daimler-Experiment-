# Replay Comparison Report

This report records the deterministic compare strategy used to validate baseline replay-chain behavior against adaptive semantic replay stabilization.

## Compare Strategy Decision

- Selected strategy: `adaptive_replay_stabilization`
- Adaptive signal count: `14`
- Baseline signal count: `0`
- Final drift suppression delta: `0.266`
- Final continuity preservation delta: `0.259`

## Preserved Capabilities

- adaptive replay stabilization
- compare strategy
- adaptive continuity metrics
- replay recovery scoring
- pinned truth retention
- stabilization reports
- replay comparison reporting
- semantic reinforcement logic

## Iteration Comparison

| Iteration | Drift suppression | Continuity delta | Replay longevity delta | Baseline retention | Adaptive retention |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.033 | 0.005 | 0.0 | 0.781 | 0.805 |
| 2 | 0.066 | 0.012 | 0.0 | 0.745 | 0.805 |
| 3 | 0.066 | 0.093 | 0.05 | 0.745 | 0.805 |
| 4 | 0.066 | 0.093 | 0.05 | 0.745 | 0.805 |
| 5 | 0.166 | 0.131 | 0.14 | 0.645 | 0.805 |
| 6 | 0.2 | 0.15 | 0.206 | 0.617 | 0.805 |
| 7 | 0.266 | 0.259 | 0.296 | 0.564 | 0.805 |

## Artifact Manifest

- baseline_metrics_summary: `evals/chains/reports/metrics_summary.json`
- adaptive_metrics_summary: `evals/chains/reports/adaptive_metrics_summary.json`
- comparative_stabilization_json: `evals/chains/reports/comparative_stabilization_report.json`
- comparative_stabilization_markdown: `evals/chains/reports/comparative_stabilization_report.md`
- compare_strategy_artifacts: `evals/chains/reports/compare_strategy_artifacts.json`
- replay_comparison_report: `evals/chains/reports/replay_comparison_report.md`
- continuity_heatmap: `evals/chains/reports/continuity_heatmap.md`
- replay_degradation_curves: `evals/chains/reports/replay_degradation_curves.md`
- stabilization_summary: `evals/chains/reports/stabilization_effectiveness_summary.md`
