#!/usr/bin/env python3
"""Iterative semantic replay-chain evaluation.

This runner measures how operational reasoning continuity survives repeated
compression/replay cycles. It is deterministic, repository-local, and avoids
LLM calls so the same checked-out inputs produce the same chain artifacts.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import replay_eval

ROOT = replay_eval.ROOT
EVALS = ROOT / "evals"
CHAINS = EVALS / "chains"
CHAIN_REPORTS = CHAINS / "reports"
CHAIN_HISTORY = CHAINS / "history"
DETERMINISTIC_GENERATED_AT = "2026-05-13T00:00:00+00:00"
DEFAULT_ITERATIONS = 7

CONSTRAINT_ANCHORS = ["cloud-first", "render", "vercel", "docker", "ci", "evidence", "sanitization"]
ARCHITECTURE_ANCHORS = ["api", "kvtc", "showcase", "telemetry", "validation", "reports"]
GOAL_ANCHORS = ["semantic continuity", "operational memory", "replay consistency", "architectural stability"]
MUTATED_GOAL_MARKERS = ["token reduction benchmark", "synthetic token spam", "production certified"]


@dataclass(frozen=True)
class ChainPaths:
    raw_context: Path = CHAIN_HISTORY / "raw_context.json"
    metrics_summary: Path = CHAIN_REPORTS / "metrics_summary.json"
    continuity_summary: Path = CHAIN_REPORTS / "continuity_trend_summary.md"
    drift_summary: Path = CHAIN_REPORTS / "drift_escalation_summary.md"

    def state(self, iteration: int) -> Path:
        prefix = "compressed_state" if iteration == 1 else "recompressed_state"
        return CHAIN_HISTORY / f"{prefix}_v{iteration}.json"

    def replay(self, iteration: int) -> Path:
        return CHAIN_HISTORY / f"replay_v{iteration}.json"

    def metrics(self, iteration: int) -> Path:
        return CHAIN_HISTORY / f"chain_step_{iteration:02d}_metrics.json"

    def step_report(self, iteration: int) -> Path:
        return CHAIN_REPORTS / f"chain_step_{iteration:02d}.md"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def term_present(term: str, text: str) -> bool:
    return normalize_text(term) in normalize_text(text)


def score_terms(terms: list[str], text: str) -> tuple[list[str], float]:
    retained = [term for term in terms if term_present(term, text)]
    score = round(len(retained) / len(terms), 3) if terms else 1.0
    return retained, score


def load_or_build_base_artifacts() -> tuple[dict[str, Any], dict[str, Any]]:
    paths = replay_eval.RunPaths()
    if paths.dataset.exists():
        dataset = json.loads(paths.dataset.read_text(encoding="utf-8"))
    else:
        dataset = replay_eval.extract_dataset(paths)
    if paths.truths.exists():
        truths = json.loads(paths.truths.read_text(encoding="utf-8"))
    else:
        truths = replay_eval.extract_truths(paths, dataset)
    return dataset, truths


def build_raw_context(paths: ChainPaths) -> dict[str, Any]:
    dataset, truths = load_or_build_base_artifacts()
    corpus = json.dumps({"dataset": dataset, "truths": truths}, sort_keys=True)
    raw_context = {
        "schema_version": 1,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "source_dataset": "evals/datasets/engineering_activity_replay_dataset.json",
        "source_truths": "evals/truths/must_retain_truths.json",
        "corpus_sha256": replay_eval.sha256_text(corpus),
        "positioning": dataset["positioning"],
        "constraints": dataset["constraints"],
        "truths": truths["truths"],
        "questions": replay_eval.QUESTIONS,
        "goal": "Measure how long operational reasoning continuity survives repeated semantic condensation.",
        "not_goal": "token-count vanity metrics",
    }
    write_json(paths.raw_context, raw_context)
    return raw_context


def initial_state(raw_context: dict[str, Any]) -> dict[str, Any]:
    retained_truth_terms = {
        truth["id"]: list(truth["must_retain_terms"])
        for truth in raw_context["truths"]
    }
    return {
        "schema_version": 1,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "iteration": 1,
        "source": "raw_context",
        "positioning": raw_context["positioning"],
        "operational_memory": {
            "workflow": "cloud-first Render Vercel Docker CI deployability with evidence and sanitization",
            "evaluation_goal": "semantic continuity, operational memory retention, replay consistency, architectural stability, and long-context reasoning continuity",
            "not_a_goal": "token-count vanity metrics",
        },
        "retained_truth_terms": retained_truth_terms,
        "architecture_trace": [
            "API, KVTC, showcase, telemetry, validation, and reports remain continuity anchors.",
            "JSON and Markdown artifacts preserve reproducible evidence across replay steps.",
        ],
        "workflow_constraints": raw_context["constraints"],
    }


def replay_answers(state: dict[str, Any], questions: list[dict[str, Any]]) -> dict[str, Any]:
    retained_text = json.dumps(state["retained_truth_terms"], sort_keys=True)
    memory = state["operational_memory"]
    architecture = " ".join(state["architecture_trace"])
    answers = []
    for question in questions:
        question_id = question["id"]
        if question_id == "q_positioning":
            answer = f"Position it as {state['positioning']} with semantic continuity and replay consistency, not token-count vanity metrics."
        elif question_id == "q_cloud_first":
            answer = f"Retain workflow constraints: {memory['workflow']}."
        elif question_id == "q_evidence":
            evidence_terms = ", ".join(term for term in ["benchmark", "evidence", "JSON", "Markdown", "reports"] if term_present(term, retained_text + architecture))
            answer = f"Retain benchmark evidence through {evidence_terms or 'available report anchors'}."
        elif question_id == "q_replay":
            replay_terms = ", ".join(term for term in ["replay", "consistency", "compressed", "contradiction", "retention"] if term_present(term, retained_text + json.dumps(memory)))
            answer = f"Replay remains stable when {replay_terms or 'continuity anchors'} survive without contradiction."
        elif question_id == "q_architecture":
            answer = f"Preserve architectural continuity across {architecture}"
        else:
            answer = "No deterministic replay answer available."
        answers.append({**question, "answer": answer})
    return {
        "schema_version": 1,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "iteration": state["iteration"],
        "source_state_iteration": state["iteration"],
        "answers": answers,
    }


def recompress(previous_state: dict[str, Any], previous_replay: dict[str, Any], raw_context: dict[str, Any], iteration: int) -> dict[str, Any]:
    replay_text = "\n".join(answer["answer"] for answer in previous_replay["answers"])
    retained_truth_terms: dict[str, list[str]] = {}
    for truth in raw_context["truths"]:
        prior_terms = previous_state["retained_truth_terms"].get(truth["id"], [])
        replay_retained = [term for term in prior_terms if term_present(term, replay_text)]
        # Semantic condensation pressure is deterministic: every recompression
        # keeps only the strongest replayed anchors, with slightly increasing
        # pressure after each cycle to expose continuity-collapse thresholds.
        max_terms = max(1, len(truth["must_retain_terms"]) - ((iteration - 1) // 2))
        retained_truth_terms[truth["id"]] = sorted(replay_retained, key=lambda value: value.lower())[:max_terms]

    previous_workflow = previous_state["operational_memory"]["workflow"]
    workflow_terms = [term for term in CONSTRAINT_ANCHORS if term_present(term, replay_text + previous_workflow)]
    workflow_limit = max(1, len(CONSTRAINT_ANCHORS) - (iteration // 2))
    workflow_terms = workflow_terms[:workflow_limit]
    arch_terms = [term.upper() if term in {"api", "kvtc"} else term for term in ARCHITECTURE_ANCHORS if term_present(term, replay_text)]
    arch_limit = max(1, len(ARCHITECTURE_ANCHORS) - ((iteration - 1) // 2))
    arch_terms = arch_terms[:arch_limit]
    return {
        "schema_version": 1,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "iteration": iteration,
        "source": f"replay_v{iteration - 1}",
        "positioning": previous_state["positioning"] if term_present("semantic replay fidelity", replay_text) else "replay continuity under compression",
        "operational_memory": {
            "workflow": " ".join(workflow_terms) or "workflow anchors degraded",
            "evaluation_goal": "semantic continuity, operational memory retention, replay consistency, architectural stability",
            "not_a_goal": "token-count vanity metrics",
        },
        "retained_truth_terms": retained_truth_terms,
        "architecture_trace": [
            f"Continuity anchors retained: {', '.join(arch_terms) if arch_terms else 'architecture anchors degraded'}."
        ],
        "workflow_constraints": [constraint for constraint in raw_context["constraints"] if any(term_present(term, constraint) for term in workflow_terms)],
    }


def detect_contradictions(text: str) -> list[str]:
    lowered = normalize_text(text)
    contradictions = []
    for marker in MUTATED_GOAL_MARKERS:
        if marker not in lowered:
            continue
        if f"not {marker}" in lowered or f"no {marker}" in lowered:
            continue
        contradictions.append(marker)
    return contradictions


def evaluate_step(
    raw_context: dict[str, Any],
    state: dict[str, Any],
    replay: dict[str, Any],
    baseline_truth_score: float,
    cumulative_contradictions: int,
) -> dict[str, Any]:
    replay_text = "\n".join(answer["answer"] for answer in replay["answers"])
    state_text = json.dumps(state, sort_keys=True)
    truth_scores = []
    retained_pairs = set()
    baseline_pairs = {(truth["id"], term.lower()) for truth in raw_context["truths"] for term in truth["must_retain_terms"]}
    for truth in raw_context["truths"]:
        retained, score = score_terms(truth["must_retain_terms"], replay_text)
        retained_pairs.update((truth["id"], term.lower()) for term in retained)
        truth_scores.append({
            "truth_id": truth["id"],
            "category": truth["category"],
            "retained_terms": retained,
            "score": score,
        })

    question_scores = []
    for answer in replay["answers"]:
        retained, score = score_terms(answer["expected_terms"], answer["answer"])
        question_scores.append({"question_id": answer["id"], "retained_terms": retained, "score": score})

    truth_retention_score = round(sum(item["score"] for item in truth_scores) / len(truth_scores), 3)
    replay_consistency_score = round(sum(item["score"] for item in question_scores) / len(question_scores), 3)
    _constraint_terms, constraint_survival_rate = score_terms(CONSTRAINT_ANCHORS, replay_text + state_text)
    _arch_terms, architectural_continuity_score = score_terms(ARCHITECTURE_ANCHORS, replay_text + state_text)
    _goal_terms, goal_score = score_terms(GOAL_ANCHORS, replay_text + state_text)
    contradictions = detect_contradictions(replay_text)
    cumulative = cumulative_contradictions + len(contradictions)
    semantic_drift_growth = round(1 - (len(retained_pairs) / len(baseline_pairs)), 3)
    return {
        "schema_version": 1,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "iteration": state["iteration"],
        "metrics": {
            "truth_retention_score": truth_retention_score,
            "retention_decay": round(max(0.0, baseline_truth_score - truth_retention_score), 3),
            "contradiction_count": len(contradictions),
            "contradiction_accumulation": cumulative,
            "semantic_drift_growth": semantic_drift_growth,
            "constraint_survival_rate": constraint_survival_rate,
            "architectural_continuity_score": architectural_continuity_score,
            "replay_consistency_score": replay_consistency_score,
            "goal_continuity_score": goal_score,
        },
        "truth_scores": truth_scores,
        "question_scores": question_scores,
        "contradictions": contradictions,
        "flags": {
            "constraints_collapsed": constraint_survival_rate < 0.5,
            "architecture_changed": architectural_continuity_score < 0.5,
            "goals_mutated": goal_score < 0.5 or bool(detect_contradictions(state_text + replay_text)),
            "replay_unstable": replay_consistency_score < 0.5 or bool(contradictions),
        },
    }


def write_step_report(paths: ChainPaths, metrics: dict[str, Any]) -> None:
    values = metrics["metrics"]
    flags = metrics["flags"]
    lines = [
        f"# Replay Chain Step {metrics['iteration']:02d}",
        "",
        "This step evaluates one deterministic compression/replay cycle in the iterative replay chain.",
        "",
        "## Metrics",
        "",
    ]
    for key, value in values.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Stability Flags", ""])
    for key, value in flags.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Constraint Retention", ""])
    for item in metrics["truth_scores"]:
        lines.append(f"- `{item['truth_id']}` ({item['category']}): `{item['score']}` via {', '.join(item['retained_terms']) or 'no retained terms'}")
    lines.extend(["", "## Replay Consistency", ""])
    for item in metrics["question_scores"]:
        lines.append(f"- `{item['question_id']}`: `{item['score']}` via {', '.join(item['retained_terms']) or 'no retained terms'}")
    report_path = paths.step_report(metrics["iteration"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def summarize(paths: ChainPaths, all_metrics: list[dict[str, Any]]) -> None:
    first_collapse = next((item["iteration"] for item in all_metrics if item["flags"]["constraints_collapsed"]), None)
    first_arch_change = next((item["iteration"] for item in all_metrics if item["flags"]["architecture_changed"]), None)
    first_goal_mutation = next((item["iteration"] for item in all_metrics if item["flags"]["goals_mutated"]), None)
    first_unstable = next((item["iteration"] for item in all_metrics if item["flags"]["replay_unstable"]), None)
    summary = {
        "schema_version": 1,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "iterations": len(all_metrics),
        "collapse_points": {
            "constraints_collapse_iteration": first_collapse,
            "architecture_change_iteration": first_arch_change,
            "goal_mutation_iteration": first_goal_mutation,
            "replay_unstable_iteration": first_unstable,
        },
        "trend": [{"iteration": item["iteration"], **item["metrics"]} for item in all_metrics],
    }
    write_json(paths.metrics_summary, summary)

    trend_lines = ["# Continuity Trend Summary", "", "| Iteration | Retention | Decay | Drift | Constraints | Architecture | Replay |", "|---:|---:|---:|---:|---:|---:|---:|"]
    for item in all_metrics:
        m = item["metrics"]
        trend_lines.append(
            f"| {item['iteration']} | {m['truth_retention_score']} | {m['retention_decay']} | {m['semantic_drift_growth']} | {m['constraint_survival_rate']} | {m['architectural_continuity_score']} | {m['replay_consistency_score']} |"
        )
    trend_lines.extend([
        "",
        "## Collapse Points",
        "",
        f"- Constraints collapse: `{first_collapse if first_collapse is not None else 'not observed'}`",
        f"- Architecture change: `{first_arch_change if first_arch_change is not None else 'not observed'}`",
        f"- Goal mutation: `{first_goal_mutation if first_goal_mutation is not None else 'not observed'}`",
        f"- Replay unstable: `{first_unstable if first_unstable is not None else 'not observed'}`",
    ])
    paths.continuity_summary.parent.mkdir(parents=True, exist_ok=True)
    paths.continuity_summary.write_text("\n".join(trend_lines) + "\n", encoding="utf-8")

    drift_lines = ["# Drift Escalation Summary", "", "This report highlights where repeated condensation first threatens operational continuity.", ""]
    previous_drift = 0.0
    for item in all_metrics:
        drift = item["metrics"]["semantic_drift_growth"]
        delta = round(drift - previous_drift, 3)
        drift_lines.append(f"- Step {item['iteration']:02d}: drift `{drift}` (delta `{delta}`), retention decay `{item['metrics']['retention_decay']}`.")
        previous_drift = drift
    paths.drift_summary.write_text("\n".join(drift_lines) + "\n", encoding="utf-8")


def run_chain(iterations: int = DEFAULT_ITERATIONS) -> None:
    paths = ChainPaths()
    raw_context = build_raw_context(paths)
    state = initial_state(raw_context)
    all_metrics: list[dict[str, Any]] = []
    baseline_score = 1.0
    cumulative_contradictions = 0
    replay: dict[str, Any] | None = None
    for iteration in range(1, iterations + 1):
        if iteration > 1:
            assert replay is not None
            state = recompress(state, replay, raw_context, iteration)
        write_json(paths.state(iteration), state)
        replay = replay_answers(state, raw_context["questions"])
        write_json(paths.replay(iteration), replay)
        metrics = evaluate_step(raw_context, state, replay, baseline_score, cumulative_contradictions)
        if iteration == 1:
            baseline_score = metrics["metrics"]["truth_retention_score"]
            metrics = evaluate_step(raw_context, state, replay, baseline_score, cumulative_contradictions)
        cumulative_contradictions = metrics["metrics"]["contradiction_accumulation"]
        write_json(paths.metrics(iteration), metrics)
        write_step_report(paths, metrics)
        all_metrics.append(metrics)
    summarize(paths, all_metrics)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic iterative replay-chain evaluation.")
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS, help="Number of compression/replay cycles to evaluate.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.iterations < 1:
        raise SystemExit("--iterations must be at least 1")
    run_chain(args.iterations)


if __name__ == "__main__":
    main()
