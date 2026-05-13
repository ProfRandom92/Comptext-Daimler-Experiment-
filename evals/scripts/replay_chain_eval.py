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
ADAPTIVE_CHAIN_REPORTS = CHAINS / "adaptive_reports"
ADAPTIVE_CHAIN_HISTORY = CHAINS / "adaptive_history"
COMPARATIVE_CHAIN_REPORTS = CHAINS / "comparative_reports"
DETERMINISTIC_GENERATED_AT = "2026-05-13T00:00:00+00:00"
DEFAULT_ITERATIONS = 7

CONSTRAINT_ANCHORS = ["cloud-first", "render", "vercel", "docker", "ci", "evidence", "sanitization"]
ARCHITECTURE_ANCHORS = ["api", "kvtc", "showcase", "telemetry", "validation", "reports"]
GOAL_ANCHORS = ["semantic continuity", "operational memory", "replay consistency", "architectural stability"]
MUTATED_GOAL_MARKERS = ["token reduction benchmark", "synthetic token spam", "production certified"]
PINNED_TRUTH_CATEGORIES = {"workflow_constraint", "replay_continuity", "architectural_continuity"}
DRIFT_EXPANSION_THRESHOLD = 0.25
CONSISTENCY_EXPANSION_THRESHOLD = 0.7


@dataclass(frozen=True)
class ChainPaths:
    """Filesystem layout for one deterministic replay-chain strategy."""

    history_root: Path = CHAIN_HISTORY
    report_root: Path = CHAIN_REPORTS

    @property
    def raw_context(self) -> Path:
        return self.history_root / "raw_context.json"

    @property
    def metrics_summary(self) -> Path:
        return self.report_root / "metrics_summary.json"

    @property
    def continuity_summary(self) -> Path:
        return self.report_root / "continuity_trend_summary.md"

    @property
    def drift_summary(self) -> Path:
        return self.report_root / "drift_escalation_summary.md"

    def state(self, iteration: int) -> Path:
        prefix = "compressed_state" if iteration == 1 else "recompressed_state"
        return self.history_root / f"{prefix}_v{iteration}.json"

    def replay(self, iteration: int) -> Path:
        return self.history_root / f"replay_v{iteration}.json"

    def metrics(self, iteration: int) -> Path:
        return self.history_root / f"chain_step_{iteration:02d}_metrics.json"

    def step_report(self, iteration: int) -> Path:
        return self.report_root / f"chain_step_{iteration:02d}.md"


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
    replay_basis = {
        "retained_truth_terms": state["retained_truth_terms"],
        "truth_pins": state.get("truth_pins", {}),
        "semantic_clusters": state.get("semantic_clusters", {}),
        "adaptive_context": state.get("adaptive_context", {}),
    }
    retained_text = json.dumps(replay_basis, sort_keys=True)
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



def semantic_clusters(raw_context: dict[str, Any], state: dict[str, Any] | None = None) -> dict[str, list[str]]:
    """Persist truth terms by semantic category for deterministic cluster reinforcement."""

    clusters: dict[str, set[str]] = {}
    retained = state.get("retained_truth_terms", {}) if state else {}
    for truth in raw_context["truths"]:
        category = truth["category"]
        clusters.setdefault(category, set())
        clusters[category].update(truth["must_retain_terms"])
        clusters[category].update(retained.get(truth["id"], []))
    return {category: sorted(values, key=str.lower) for category, values in sorted(clusters.items())}


def truth_pins(raw_context: dict[str, Any]) -> dict[str, list[str]]:
    """Select high-priority truth terms that adaptive replay must keep pinned."""

    pins = {}
    for truth in raw_context["truths"]:
        if truth["category"] in PINNED_TRUTH_CATEGORIES:
            pins[truth["id"]] = list(truth["must_retain_terms"])
    return pins


def weighted_replay_terms(terms: list[str], replay_text: str, pins: list[str], cluster_terms: list[str], limit: int) -> list[str]:
    """Rank anchors deterministically so replayed, pinned, and clustered terms survive pressure."""

    ranked = []
    for term in terms:
        score = 0
        if term_present(term, replay_text):
            score += 4
        if any(term.lower() == pin.lower() for pin in pins):
            score += 3
        if any(term.lower() == clustered.lower() for clustered in cluster_terms):
            score += 2
        if score:
            ranked.append((term, score))
    ranked.sort(key=lambda item: (-item[1], item[0].lower()))
    return [term for term, _score in ranked[:limit]]


def adaptive_recompress(
    previous_state: dict[str, Any],
    previous_replay: dict[str, Any],
    raw_context: dict[str, Any],
    iteration: int,
    previous_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Recompress with adaptive semantic replay stabilization.

    The stabilizer remains deterministic: it only uses checked-in raw context,
    prior replay text, and prior metrics to anchor constraints, reinforce the
    repository architecture, weight replayed pins, persist semantic clusters,
    expand context when drift crosses fixed thresholds, and pin high-priority
    truths.
    """

    replay_text = "\n".join(answer["answer"] for answer in previous_replay["answers"])
    pins = truth_pins(raw_context)
    clusters = semantic_clusters(raw_context, previous_state)
    previous_values = previous_metrics.get("metrics", {}) if previous_metrics else {}
    drift = previous_values.get("semantic_drift_growth", 0.0)
    replay_consistency = previous_values.get("replay_consistency_score", 1.0)
    expansion_active = drift > DRIFT_EXPANSION_THRESHOLD or replay_consistency < CONSISTENCY_EXPANSION_THRESHOLD

    retained_truth_terms: dict[str, list[str]] = {}
    for truth in raw_context["truths"]:
        prior_terms = previous_state["retained_truth_terms"].get(truth["id"], [])
        pin_terms = pins.get(truth["id"], [])
        cluster_terms = clusters.get(truth["category"], [])
        candidate_terms = list(dict.fromkeys([*prior_terms, *pin_terms, *cluster_terms]))
        if expansion_active:
            candidate_terms = list(dict.fromkeys([*candidate_terms, *truth["must_retain_terms"]]))
        pressure_limit = max(2, len(truth["must_retain_terms"]) - max(0, (iteration - 3) // 3))
        retained_truth_terms[truth["id"]] = weighted_replay_terms(candidate_terms, replay_text, pin_terms, cluster_terms, pressure_limit)

    constraint_terms = [term for term in CONSTRAINT_ANCHORS if term_present(term, replay_text + json.dumps(pins, sort_keys=True))]
    if expansion_active:
        constraint_terms = list(dict.fromkeys([*constraint_terms, *CONSTRAINT_ANCHORS]))
    architecture_terms = [term.upper() if term in {"api", "kvtc"} else term for term in ARCHITECTURE_ANCHORS if term_present(term, replay_text + json.dumps(clusters, sort_keys=True))]
    if expansion_active:
        architecture_terms = list(dict.fromkeys([*architecture_terms, "API", "KVTC", "showcase", "telemetry", "validation", "reports"]))

    weighted_profile = {
        "constraint_anchoring": constraint_terms,
        "architecture_reinforcement": architecture_terms,
        "replay_weighting": {truth_id: len(terms) for truth_id, terms in retained_truth_terms.items()},
        "semantic_cluster_persistence": {category: len(terms) for category, terms in clusters.items()},
        "drift_triggered_context_expansion": expansion_active,
        "high_priority_truth_pinning": sorted(pins),
        "previous_semantic_drift_growth": drift,
        "previous_replay_consistency_score": replay_consistency,
    }
    workflow_constraints = [
        constraint
        for constraint in raw_context["constraints"]
        if any(term_present(term, constraint) for term in constraint_terms)
    ]
    if expansion_active and not workflow_constraints:
        workflow_constraints = raw_context["constraints"][:]

    return {
        "schema_version": 1,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "iteration": iteration,
        "source": f"adaptive_replay_v{iteration - 1}",
        "positioning": previous_state["positioning"],
        "operational_memory": {
            "workflow": " ".join(constraint_terms) or previous_state["operational_memory"]["workflow"],
            "evaluation_goal": "semantic continuity, operational memory retention, replay consistency, architectural stability, and adaptive continuity under repeated compression",
            "not_a_goal": "token-count vanity metrics",
        },
        "retained_truth_terms": retained_truth_terms,
        "architecture_trace": [
            f"Adaptive architecture reinforcement retained: {', '.join(architecture_terms) if architecture_terms else 'architecture anchors degraded'}.",
            "Constraint anchoring, replay weighting, semantic cluster persistence, context expansion, and truth pinning are active stabilization controls.",
        ],
        "workflow_constraints": workflow_constraints,
        "truth_pins": pins,
        "semantic_clusters": clusters,
        "adaptive_context": weighted_profile,
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
    pin_source = state.get("truth_pins") or truth_pins(raw_context)
    pinned_pairs = {(truth_id, term.lower()) for truth_id, terms in pin_source.items() for term in terms}
    pinned_retained = retained_pairs & pinned_pairs
    pinned_truth_retention = round(len(pinned_retained) / len(pinned_pairs), 3) if pinned_pairs else 1.0
    contradictions = detect_contradictions(replay_text)
    cumulative = cumulative_contradictions + len(contradictions)
    semantic_drift_growth = round(1 - (len(retained_pairs) / len(baseline_pairs)), 3)
    previous_drift = state.get("adaptive_context", {}).get("previous_semantic_drift_growth", semantic_drift_growth)
    drift_stabilization_delta = round(max(0.0, previous_drift - semantic_drift_growth), 3)
    replay_recovery_score = round((pinned_truth_retention + constraint_survival_rate + replay_consistency_score) / 3, 3)
    adaptive_continuity_score = round(
        (truth_retention_score + replay_consistency_score + constraint_survival_rate + architectural_continuity_score + goal_score + pinned_truth_retention) / 6,
        3,
    )
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
            "drift_stabilization_delta": drift_stabilization_delta,
            "replay_recovery_score": replay_recovery_score,
            "pinned_truth_retention": pinned_truth_retention,
            "adaptive_continuity_score": adaptive_continuity_score,
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


def summarize(paths: ChainPaths, all_metrics: list[dict[str, Any]], label: str = "baseline") -> None:
    first_collapse = next((item["iteration"] for item in all_metrics if item["flags"]["constraints_collapsed"]), None)
    first_arch_change = next((item["iteration"] for item in all_metrics if item["flags"]["architecture_changed"]), None)
    first_goal_mutation = next((item["iteration"] for item in all_metrics if item["flags"]["goals_mutated"]), None)
    first_unstable = next((item["iteration"] for item in all_metrics if item["flags"]["replay_unstable"]), None)
    summary = {
        "schema_version": 1,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "strategy": label,
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


def run_chain(iterations: int = DEFAULT_ITERATIONS, strategy: str = "baseline", paths: ChainPaths | None = None) -> list[dict[str, Any]]:
    paths = paths or ChainPaths()
    raw_context = build_raw_context(paths)
    state = initial_state(raw_context)
    if strategy == "adaptive":
        state = {
            **state,
            "source": "adaptive_raw_context",
            "truth_pins": truth_pins(raw_context),
            "semantic_clusters": semantic_clusters(raw_context),
            "adaptive_context": {
                "constraint_anchoring": CONSTRAINT_ANCHORS,
                "architecture_reinforcement": ARCHITECTURE_ANCHORS,
                "replay_weighting": "pinned replay terms receive deterministic priority",
                "semantic_cluster_persistence": "truth terms are persisted by category",
                "drift_triggered_context_expansion": False,
                "high_priority_truth_pinning": sorted(truth_pins(raw_context)),
                "previous_semantic_drift_growth": 0.0,
                "previous_replay_consistency_score": 1.0,
            },
        }
    all_metrics: list[dict[str, Any]] = []
    baseline_score = 1.0
    cumulative_contradictions = 0
    replay: dict[str, Any] | None = None
    previous_metrics: dict[str, Any] | None = None
    for iteration in range(1, iterations + 1):
        if iteration > 1:
            assert replay is not None
            if strategy == "adaptive":
                state = adaptive_recompress(state, replay, raw_context, iteration, previous_metrics)
            else:
                state = recompress(state, replay, raw_context, iteration)
        write_json(paths.state(iteration), state)
        replay = replay_answers(state, raw_context["questions"])
        write_json(paths.replay(iteration), replay)
        metrics = evaluate_step(raw_context, state, replay, baseline_score, cumulative_contradictions)
        metrics["strategy"] = strategy
        if iteration == 1:
            baseline_score = metrics["metrics"]["truth_retention_score"]
            metrics = evaluate_step(raw_context, state, replay, baseline_score, cumulative_contradictions)
            metrics["strategy"] = strategy
        cumulative_contradictions = metrics["metrics"]["contradiction_accumulation"]
        write_json(paths.metrics(iteration), metrics)
        write_step_report(paths, metrics)
        all_metrics.append(metrics)
        previous_metrics = metrics
    summarize(paths, all_metrics, strategy)
    return all_metrics


def heat(value: float) -> str:
    if value >= 0.85:
        return "🟩"
    if value >= 0.65:
        return "🟨"
    if value >= 0.45:
        return "🟧"
    return "🟥"


def write_comparative_reports(baseline: list[dict[str, Any]], adaptive: list[dict[str, Any]]) -> None:
    COMPARATIVE_CHAIN_REPORTS.mkdir(parents=True, exist_ok=True)
    paired = list(zip(baseline, adaptive, strict=True))
    rows = []
    for base, adap in paired:
        bm = base["metrics"]
        am = adap["metrics"]
        rows.append({
            "iteration": base["iteration"],
            "contradiction_reduction": bm["contradiction_accumulation"] - am["contradiction_accumulation"],
            "continuity_preservation_delta": round(am["adaptive_continuity_score"] - bm["adaptive_continuity_score"], 3),
            "drift_suppression": round(bm["semantic_drift_growth"] - am["semantic_drift_growth"], 3),
            "replay_longevity_delta": round(am["replay_consistency_score"] - bm["replay_consistency_score"], 3),
            "baseline": bm,
            "adaptive": am,
        })
    summary = {
        "schema_version": 1,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "iterations": len(rows),
        "research_question": "Can adaptive semantic reinforcement significantly extend operational continuity under repeated compression?",
        "aggregate": {
            "mean_contradiction_reduction": round(sum(row["contradiction_reduction"] for row in rows) / len(rows), 3),
            "mean_continuity_preservation_delta": round(sum(row["continuity_preservation_delta"] for row in rows) / len(rows), 3),
            "mean_drift_suppression": round(sum(row["drift_suppression"] for row in rows) / len(rows), 3),
            "mean_replay_longevity_delta": round(sum(row["replay_longevity_delta"] for row in rows) / len(rows), 3),
            "final_drift_stabilization_delta": rows[-1]["drift_suppression"],
            "final_replay_recovery_score_delta": round(rows[-1]["adaptive"]["replay_recovery_score"] - rows[-1]["baseline"]["replay_recovery_score"], 3),
            "final_pinned_truth_retention_delta": round(rows[-1]["adaptive"]["pinned_truth_retention"] - rows[-1]["baseline"]["pinned_truth_retention"], 3),
            "final_adaptive_continuity_score_delta": rows[-1]["continuity_preservation_delta"],
        },
        "comparisons": rows,
    }
    write_json(COMPARATIVE_CHAIN_REPORTS / "adaptive_stabilization_summary.json", summary)

    report_lines = [
        "# Adaptive Replay Stabilization Comparative Report",
        "",
        "This deterministic report compares baseline replay chains with adaptive stabilized replay chains under repeated compression.",
        "",
        "## Stabilization Controls",
        "",
        "- Constraint anchoring keeps workflow requirements represented.",
        "- Architecture reinforcement keeps API, KVTC, showcase, telemetry, validation, and reports present.",
        "- Replay weighting prioritizes replayed, pinned, and clustered terms.",
        "- Semantic cluster persistence carries category-level truth groups forward.",
        "- Drift-triggered context expansion restores raw truth terms after fixed drift or consistency thresholds.",
        "- High-priority truth pinning protects workflow, replay, and architecture truths.",
        "",
        "## Comparative Metrics",
        "",
        "| Iteration | Contradiction Reduction | Continuity Δ | Drift Suppression | Replay Longevity Δ | Pinned Truth Δ |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        report_lines.append(
            f"| {row['iteration']} | {row['contradiction_reduction']} | {row['continuity_preservation_delta']} | {row['drift_suppression']} | {row['replay_longevity_delta']} | {round(row['adaptive']['pinned_truth_retention'] - row['baseline']['pinned_truth_retention'], 3)} |"
        )
    report_lines.extend([
        "",
        "## Stabilization Effectiveness Summary",
        "",
        f"- Mean contradiction reduction: `{summary['aggregate']['mean_contradiction_reduction']}`.",
        f"- Mean continuity preservation delta: `{summary['aggregate']['mean_continuity_preservation_delta']}`.",
        f"- Mean drift suppression: `{summary['aggregate']['mean_drift_suppression']}`.",
        f"- Mean replay longevity delta: `{summary['aggregate']['mean_replay_longevity_delta']}`.",
        f"- Final drift stabilization delta: `{summary['aggregate']['final_drift_stabilization_delta']}`.",
        f"- Final replay recovery score delta: `{summary['aggregate']['final_replay_recovery_score_delta']}`.",
        f"- Final pinned truth retention delta: `{summary['aggregate']['final_pinned_truth_retention_delta']}`.",
        f"- Final adaptive continuity score delta: `{summary['aggregate']['final_adaptive_continuity_score_delta']}`.",
    ])
    (COMPARATIVE_CHAIN_REPORTS / "adaptive_stabilization_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    heatmap_lines = [
        "# Continuity Heatmap",
        "",
        "Legend: 🟩 >= 0.85, 🟨 >= 0.65, 🟧 >= 0.45, 🟥 < 0.45.",
        "",
        "| Strategy | Iteration | Truth | Constraint | Architecture | Replay | Adaptive Continuity |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for label, metrics_list in (("baseline", baseline), ("adaptive", adaptive)):
        for item in metrics_list:
            m = item["metrics"]
            heatmap_lines.append(
                f"| {label} | {item['iteration']} | {heat(m['truth_retention_score'])} {m['truth_retention_score']} | {heat(m['constraint_survival_rate'])} {m['constraint_survival_rate']} | {heat(m['architectural_continuity_score'])} {m['architectural_continuity_score']} | {heat(m['replay_consistency_score'])} {m['replay_consistency_score']} | {heat(m['adaptive_continuity_score'])} {m['adaptive_continuity_score']} |"
            )
    (COMPARATIVE_CHAIN_REPORTS / "continuity_heatmap.md").write_text("\n".join(heatmap_lines) + "\n", encoding="utf-8")

    curve_lines = [
        "# Replay Degradation Curves",
        "",
        "| Iteration | Baseline Drift | Adaptive Drift | Baseline Retention | Adaptive Retention | Baseline Replay | Adaptive Replay |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for base, adap in paired:
        bm = base["metrics"]
        am = adap["metrics"]
        curve_lines.append(
            f"| {base['iteration']} | {bm['semantic_drift_growth']} | {am['semantic_drift_growth']} | {bm['truth_retention_score']} | {am['truth_retention_score']} | {bm['replay_consistency_score']} | {am['replay_consistency_score']} |"
        )
    (COMPARATIVE_CHAIN_REPORTS / "replay_degradation_curves.md").write_text("\n".join(curve_lines) + "\n", encoding="utf-8")


def run_comparison(iterations: int = DEFAULT_ITERATIONS) -> None:
    baseline = run_chain(iterations, "baseline", ChainPaths())
    adaptive = run_chain(iterations, "adaptive", ChainPaths(ADAPTIVE_CHAIN_HISTORY, ADAPTIVE_CHAIN_REPORTS))
    write_comparative_reports(baseline, adaptive)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic iterative replay-chain evaluation.")
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS, help="Number of compression/replay cycles to evaluate.")
    parser.add_argument(
        "--strategy",
        choices=["baseline", "adaptive", "compare"],
        default="compare",
        help="Replay-chain strategy to run; compare generates baseline, adaptive, and comparative reports.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.iterations < 1:
        raise SystemExit("--iterations must be at least 1")
    if args.strategy == "compare":
        run_comparison(args.iterations)
    else:
        paths = ChainPaths(ADAPTIVE_CHAIN_HISTORY, ADAPTIVE_CHAIN_REPORTS) if args.strategy == "adaptive" else ChainPaths()
        run_chain(args.iterations, args.strategy, paths)


if __name__ == "__main__":
    main()
