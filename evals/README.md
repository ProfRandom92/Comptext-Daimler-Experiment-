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
└── scripts/     # Reproducible evaluation runner
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
