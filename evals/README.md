# Replay Evaluation System

This directory contains the repository's primary evaluation focus: **semantic replay fidelity under constrained context budgets**.

The goal is not to prove generic token reduction. The goal is to test whether compressed engineering context preserves the operational memory needed to continue real repository work without semantic drift, contradiction, or architectural discontinuity.

## Directory layout

```text
evals/
├── datasets/    # Real repository activity extracted from git history, docs, and reports
├── truths/      # Must-retain truths derived from the dataset
├── compressed/  # Compressed replay state used for questioning
├── replay/      # Replay questions and deterministic answers
├── reports/     # JSON and Markdown evaluation outputs
├── chains/      # Iterative compression/replay-chain history, metrics, and reports
└── scripts/     # Reproducible evaluation runners
```

## Evaluation flow

```text
raw context
→ semantic compression
→ compressed replay state
→ replay questioning
→ retention/drift evaluation
```

The pipeline is intentionally deterministic and repository-local. It uses real engineering activity available in this checkout:

- git commits and PR references present in local history, including PR #43 when available;
- benchmark and regression report artifacts;
- replay, benchmark, regression, architecture, README, validation, deployment, and showcase documentation;
- validation and evidence pipeline files already committed to the repository.

If an expected PR number or discussion is not present in local git history or repository files, the pipeline records observed evidence only and does **not** fabricate missing content.

## Artifacts

Run the pipeline with:

```bash
python evals/scripts/replay_eval.py all
```

Generated outputs:

- `evals/datasets/engineering_activity_replay_dataset.json`
- `evals/truths/must_retain_truths.json`
- `evals/compressed/compressed_replay_state.json`
- `evals/replay/replay_answers.json`
- `evals/reports/replay_scores.json`
- `evals/reports/semantic_replay_fidelity_report.md`

## What is scored

The system scores:

- **retention**: whether must-retain truths survive compression and replay;
- **replay consistency**: whether questions about the compressed state produce expected continuity terms;
- **contradiction detection**: whether replay outputs accidentally assert forbidden positions or claims;
- **semantic drift**: whether truth categories fall below the retention threshold;
- **architectural continuity**: whether API, KVTC, showcase, telemetry, validation, and report-contract anchors remain represented.

## Must-retain truth examples

The default truth extractor tracks repository-specific continuity constraints, including:

- cloud-first workflow required;
- replay validation exists;
- semantic drift tracking exists;
- benchmark evidence pipeline exists;
- no fake production claims;
- replay consistency matters;
- architectural continuity matters.

## Engineering constraints

The evaluation system follows the same project constraints as the rest of the repository:

- preserve existing functionality;
- maintain CI stability;
- prefer small, focused changes;
- keep generated evidence reproducible;
- avoid fake benchmark generators, synthetic token spam, lorem ipsum, and unsupported production claims.

## Iterative replay-chain evaluation

The chain runner evaluates repeated semantic condensation directly inside this repository:

```text
raw_context
→ compressed_state_v1
→ replay_v1
→ recompressed_state_v2
→ replay_v2
→ recompressed_state_v3
→ replay_v3
...
```

Run it with:

```bash
python evals/scripts/replay_chain_eval.py --iterations 7
```

By default, the runner now executes `--strategy compare`, which emits the original baseline chain plus an adaptive stabilized chain. You can also run `--strategy baseline` or `--strategy adaptive` independently.

Generated outputs are deterministic and reproducible for the same checked-out inputs:

- `evals/chains/history/raw_context.json`
- `evals/chains/history/compressed_state_v1.json`
- `evals/chains/history/recompressed_state_vN.json`
- `evals/chains/history/replay_vN.json`
- `evals/chains/history/chain_step_NN_metrics.json`
- `evals/chains/reports/chain_step_NN.md`
- `evals/chains/reports/metrics_summary.json`
- `evals/chains/reports/continuity_trend_summary.md`
- `evals/chains/reports/drift_escalation_summary.md`
- `evals/chains/adaptive_history/` adaptive stabilized state, replay, and metric artifacts
- `evals/chains/adaptive_reports/` adaptive trend, drift, and step reports
- `evals/chains/comparative_reports/adaptive_stabilization_report.md`
- `evals/chains/comparative_reports/adaptive_stabilization_summary.json`
- `evals/chains/comparative_reports/continuity_heatmap.md`
- `evals/chains/comparative_reports/replay_degradation_curves.md`

The chain metrics focus on operational continuity rather than token-count vanity metrics:

- retention decay;
- contradiction accumulation;
- semantic drift growth;
- constraint survival rate;
- architectural continuity score;
- replay consistency score;
- drift stabilization delta;
- replay recovery score;
- pinned truth retention;
- adaptive continuity score.

Adaptive stabilization adds deterministic constraint anchoring, architecture reinforcement, replay weighting, semantic cluster persistence, drift-triggered context expansion, and high-priority truth pinning. Comparative reports measure contradiction reduction, continuity preservation, drift suppression, and replay longevity between baseline replay chains and adaptive stabilized replay chains. The summary flags when constraints collapse, architecture changes, goals mutate, or replay becomes unstable.
