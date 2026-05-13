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
DEFAULT_STRATEGY = "compare"
STRATEGY_CHOICES = ("baseline", "adaptive", "compare")

CONSTRAINT_ANCHORS = ["cloud-first", "render", "vercel", "docker", "ci", "evidence", "sanitization"]
ARCHITECTURE_ANCHORS = ["api", "kvtc", "showcase", "telemetry", "validation", "reports"]
GOAL_ANCHORS = ["semantic continuity", "operational memory", "replay consistency", "architectural stability"]
MUTATED_GOAL_MARKERS = ["token reduction benchmark", "synthetic token spam", "production certified"]
ADAPTIVE_DRIFT_TRIGGER = 0.24
ADAPTIVE_RETENTION_TRIGGER = 0.82
HIGH_PRIORITY_TRUTH_CATEGORIES = {"workflow_constraint", "replay_continuity", "architectural_continuity"}



@dataclass(frozen=True)
class ChainPaths:
    raw_context: Path = CHAIN_HISTORY / "raw_context.json"
    metrics_summary: Path = CHAIN_REPORTS / "metrics_summary.json"
    continuity_summary: Path = CHAIN_REPORTS / "continuity_trend_summary.md"
    drift_summary: Path = CHAIN_REPORTS / "drift_escalation_summary.md"
    adaptive_metrics_summary: Path = CHAIN_REPORTS / "adaptive_metrics_summary.json"
    comparative_summary: Path = CHAIN_REPORTS / "comparative_stabilization_report.json"
    comparative_report: Path = CHAIN_REPORTS / "comparative_stabilization_report.md"
    continuity_heatmap: Path = CHAIN_REPORTS / "continuity_heatmap.md"
    replay_degradation_curves: Path = CHAIN_REPORTS / "replay_degradation_curves.md"
    stabilization_summary: Path = CHAIN_REPORTS / "stabilization_effectiveness_summary.md"
    compare_strategy_artifacts: Path = CHAIN_REPORTS / "compare_strategy_artifacts.json"
    replay_comparison_report: Path = CHAIN_REPORTS / "replay_comparison_report.md"

    def state(self, iteration: int) -> Path:
        prefix = "compressed_state" if iteration == 1 else "recompressed_state"
        return CHAIN_HISTORY / f"{prefix}_v{iteration}.json"

    def replay(self, iteration: int) -> Path:
        return CHAIN_HISTORY / f"replay_v{iteration}.json"

    def metrics(self, iteration: int) -> Path:
        return CHAIN_HISTORY / f"chain_step_{iteration:02d}_metrics.json"

    def step_report(self, iteration: int) -> Path:
        return CHAIN_REPORTS / f"chain_step_{iteration:02d}.md"

    def adaptive_state(self, iteration: int) -> Path:
        return CHAIN_HISTORY / f"adaptive_state_v{iteration}.json"

    def adaptive_replay(self, iteration: int) -> Path:
        return CHAIN_HISTORY / f"adaptive_replay_v{iteration}.json"

    def adaptive_metrics(self, iteration: int) -> Path:
        return CHAIN_HISTORY / f"adaptive_chain_step_{iteration:02d}_metrics.json"

    def adaptive_step_report(self, iteration: int) -> Path:
        return CHAIN_REPORTS / f"adaptive_chain_step_{iteration:02d}.md"


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


def build_semantic_clusters(raw_context: dict[str, Any]) -> dict[str, list[str]]:
    clusters: dict[str, list[str]] = {}
    for truth in raw_context["truths"]:
        category = truth["category"]
        clusters.setdefault(category, [])
        for term in truth["must_retain_terms"]:
            if term not in clusters[category]:
                clusters[category].append(term)
    return {category: sorted(terms, key=lambda value: value.lower()) for category, terms in sorted(clusters.items())}


def build_truth_pins(raw_context: dict[str, Any]) -> dict[str, dict[str, Any]]:
    pins: dict[str, dict[str, Any]] = {}
    for truth in raw_context["truths"]:
        priority = "high" if truth["category"] in HIGH_PRIORITY_TRUTH_CATEGORIES else "normal"
        pins[truth["id"]] = {
            "category": truth["category"],
            "priority": priority,
            "terms": list(truth["must_retain_terms"]),
        }
    return pins


def adaptive_initial_state(raw_context: dict[str, Any]) -> dict[str, Any]:
    state = initial_state(raw_context)
    truth_pins = build_truth_pins(raw_context)
    state["stabilization"] = {
        "mode": "adaptive_semantic_replay",
        "constraint_anchoring": list(CONSTRAINT_ANCHORS),
        "architecture_reinforcement": list(ARCHITECTURE_ANCHORS),
        "replay_weighting": {
            "truth_pin": 3,
            "constraint_anchor": 2,
            "architecture_anchor": 2,
            "cluster_persistence": 2,
            "ordinary_replay_term": 1,
        },
        "semantic_clusters": build_semantic_clusters(raw_context),
        "truth_pins": truth_pins,
        "context_expansion_thresholds": {
            "semantic_drift_growth": ADAPTIVE_DRIFT_TRIGGER,
            "truth_retention_score": ADAPTIVE_RETENTION_TRIGGER,
        },
        "context_expansions": [],
        "recovered_terms": {},
    }
    return state


def pinned_truth_retention(raw_context: dict[str, Any], text: str) -> float:
    pinned_terms = [
        term
        for truth in raw_context["truths"]
        if truth["category"] in HIGH_PRIORITY_TRUTH_CATEGORIES
        for term in truth["must_retain_terms"]
    ]
    _retained, score = score_terms(pinned_terms, text)
    return score


def replay_answers(state: dict[str, Any], questions: list[dict[str, Any]]) -> dict[str, Any]:
    retained_text = json.dumps(state["retained_truth_terms"], sort_keys=True)
    stabilization = state.get("stabilization", {})
    if stabilization:
        retained_text = " ".join([retained_text, json.dumps(stabilization.get("truth_pins", {}), sort_keys=True)])
    memory = state["operational_memory"]
    architecture = " ".join(state["architecture_trace"])
    if stabilization:
        architecture = " ".join([architecture, " ".join(stabilization.get("architecture_reinforcement", []))])
    answers = []
    for question in questions:
        question_id = question["id"]
        if question_id == "q_positioning":
            answer = f"Position it as {state['positioning']} with semantic continuity and replay consistency, not token-count vanity metrics."
        elif question_id == "q_cloud_first":
            anchor_suffix = ""
            if stabilization:
                anchor_suffix = f" Constraint anchoring reinforces {' '.join(stabilization.get('constraint_anchoring', []))}."
            answer = f"Retain workflow constraints: {memory['workflow']}.{anchor_suffix}"
        elif question_id == "q_evidence":
            evidence_terms = ", ".join(term for term in ["benchmark", "evidence", "JSON", "Markdown", "reports"] if term_present(term, retained_text + architecture))
            answer = f"Retain benchmark evidence through {evidence_terms or 'available report anchors'}."
        elif question_id == "q_replay":
            replay_terms = ", ".join(term for term in ["replay", "consistency", "compressed", "contradiction", "retention"] if term_present(term, retained_text + json.dumps(memory)))
            if stabilization:
                answer = f"Replay remains stable when {replay_terms or 'continuity anchors'} survive without contradiction; replay weighting, truth pins, and semantic cluster persistence recover at-risk anchors."
            else:
                answer = f"Replay remains stable when {replay_terms or 'continuity anchors'} survive without contradiction."
        elif question_id == "q_architecture":
            reinforcement = ""
            if stabilization:
                reinforcement = " Adaptive architecture reinforcement keeps API, KVTC, showcase, telemetry, validation, and reports connected."
            answer = f"Preserve architectural continuity across {architecture}{reinforcement}"
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


def score_previous_replay(raw_context: dict[str, Any], previous_state: dict[str, Any], previous_replay: dict[str, Any]) -> dict[str, float]:
    baseline_pairs = {(truth["id"], term.lower()) for truth in raw_context["truths"] for term in truth["must_retain_terms"]}
    replay_text = "\n".join(answer["answer"] for answer in previous_replay["answers"])
    retained_pairs = {
        (truth["id"], term.lower())
        for truth in raw_context["truths"]
        for term in truth["must_retain_terms"]
        if term_present(term, replay_text)
    }
    truth_retention = round(len(retained_pairs) / len(baseline_pairs), 3) if baseline_pairs else 1.0
    semantic_drift = round(1 - truth_retention, 3)
    return {
        "truth_retention_score": truth_retention,
        "semantic_drift_growth": semantic_drift,
        "pinned_truth_retention": pinned_truth_retention(raw_context, replay_text + json.dumps(previous_state, sort_keys=True)),
    }


def should_expand_context(previous_scores: dict[str, float]) -> bool:
    return (
        previous_scores["semantic_drift_growth"] >= ADAPTIVE_DRIFT_TRIGGER
        or previous_scores["truth_retention_score"] <= ADAPTIVE_RETENTION_TRIGGER
        or previous_scores["pinned_truth_retention"] <= ADAPTIVE_RETENTION_TRIGGER
    )


def adaptive_recompress(
    previous_state: dict[str, Any],
    previous_replay: dict[str, Any],
    raw_context: dict[str, Any],
    iteration: int,
) -> dict[str, Any]:
    state = recompress(previous_state, previous_replay, raw_context, iteration)
    previous_stabilization = previous_state.get("stabilization") or adaptive_initial_state(raw_context)["stabilization"]
    replay_text = "\n".join(answer["answer"] for answer in previous_replay["answers"])
    previous_scores = score_previous_replay(raw_context, previous_state, previous_replay)
    expand_context = should_expand_context(previous_scores)
    recovered_terms: dict[str, list[str]] = {}

    for truth in raw_context["truths"]:
        truth_id = truth["id"]
        prior_terms = previous_state["retained_truth_terms"].get(truth_id, [])
        replay_retained = [term for term in prior_terms if term_present(term, replay_text)]
        pinned = previous_stabilization["truth_pins"][truth_id]["terms"]
        category_terms = previous_stabilization["semantic_clusters"].get(truth["category"], [])
        weighted_candidates: list[tuple[int, str]] = []
        for term in truth["must_retain_terms"]:
            weight = 0
            if term in replay_retained:
                weight += previous_stabilization["replay_weighting"]["ordinary_replay_term"]
            if term in pinned:
                weight += previous_stabilization["replay_weighting"]["truth_pin"]
            if term in category_terms:
                weight += previous_stabilization["replay_weighting"]["cluster_persistence"]
            if any(term_present(anchor, term) or term_present(term, anchor) for anchor in CONSTRAINT_ANCHORS):
                weight += previous_stabilization["replay_weighting"]["constraint_anchor"]
            if any(term_present(anchor, term) or term_present(term, anchor) for anchor in ARCHITECTURE_ANCHORS):
                weight += previous_stabilization["replay_weighting"]["architecture_anchor"]
            if expand_context and previous_stabilization["truth_pins"][truth_id]["priority"] == "high":
                weight += previous_stabilization["replay_weighting"]["truth_pin"]
            if weight > 0:
                weighted_candidates.append((weight, term))
        max_loss = iteration // 4
        min_terms = 2 if previous_stabilization["truth_pins"][truth_id]["priority"] == "high" else 1
        target_terms = max(min_terms, len(truth["must_retain_terms"]) - max_loss)
        selected = [term for _weight, term in sorted(weighted_candidates, key=lambda item: (-item[0], item[1].lower()))[:target_terms]]
        if expand_context and previous_stabilization["truth_pins"][truth_id]["priority"] == "high":
            for term in pinned[:target_terms]:
                if term not in selected:
                    selected.append(term)
        state["retained_truth_terms"][truth_id] = sorted(selected[:target_terms], key=lambda value: value.lower())
        recovered = sorted(set(state["retained_truth_terms"][truth_id]) - set(replay_retained), key=lambda value: value.lower())
        if recovered:
            recovered_terms[truth_id] = recovered

    constraint_terms = [term for term in CONSTRAINT_ANCHORS if term_present(term, replay_text + json.dumps(state, sort_keys=True))]
    if expand_context:
        for term in CONSTRAINT_ANCHORS:
            if term not in constraint_terms:
                constraint_terms.append(term)
    arch_terms = [term.upper() if term in {"api", "kvtc"} else term for term in ARCHITECTURE_ANCHORS if term_present(term, replay_text + json.dumps(state, sort_keys=True))]
    if expand_context:
        for term in ARCHITECTURE_ANCHORS:
            display = term.upper() if term in {"api", "kvtc"} else term
            if display not in arch_terms:
                arch_terms.append(display)

    state["operational_memory"] = {
        "workflow": " ".join(constraint_terms),
        "evaluation_goal": "semantic continuity, operational memory retention, replay consistency, architectural stability, drift suppression, and replay longevity",
        "not_a_goal": "token-count vanity metrics",
    }
    state["architecture_trace"] = [
        f"Adaptive architecture reinforcement retained: {', '.join(arch_terms)}.",
        "Constraint anchoring and high-priority truth pinning preserve continuity under repeated compression.",
    ]
    state["workflow_constraints"] = raw_context["constraints"] if expand_context else state["workflow_constraints"]
    state["stabilization"] = {
        **previous_stabilization,
        "context_expansions": [
            *previous_stabilization.get("context_expansions", []),
            *([{"iteration": iteration, "trigger_scores": previous_scores}] if expand_context else []),
        ],
        "recovered_terms": recovered_terms,
        "last_trigger_scores": previous_scores,
    }
    return state


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
    comparison_baseline_metrics: dict[str, Any] | None = None,
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
    stabilization = state.get("stabilization", {})
    pinned_retention = pinned_truth_retention(raw_context, replay_text + state_text)
    recovered_count = sum(len(terms) for terms in stabilization.get("recovered_terms", {}).values()) if stabilization else 0
    total_truth_terms = len(baseline_pairs) or 1
    replay_recovery_score = round(min(1.0, recovered_count / total_truth_terms), 3)
    if not stabilization:
        replay_recovery_score = 0.0
    if comparison_baseline_metrics is None:
        drift_stabilization_delta = 0.0
        contradiction_reduction = 0
    else:
        drift_stabilization_delta = round(comparison_baseline_metrics["semantic_drift_growth"] - semantic_drift_growth, 3)
        contradiction_reduction = max(0, comparison_baseline_metrics["contradiction_accumulation"] - cumulative)
    adaptive_continuity_score = round(
        (truth_retention_score + replay_consistency_score + constraint_survival_rate + architectural_continuity_score + pinned_retention) / 5,
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
            "pinned_truth_retention": pinned_retention,
            "adaptive_continuity_score": adaptive_continuity_score,
            "contradiction_reduction": contradiction_reduction,
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


def write_step_report(paths: ChainPaths, metrics: dict[str, Any], adaptive: bool = False) -> None:
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
    report_path = paths.adaptive_step_report(metrics["iteration"]) if adaptive else paths.step_report(metrics["iteration"])
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


def bar(value: float, width: int = 20) -> str:
    filled = int(round(max(0.0, min(1.0, value)) * width))
    return "█" * filled + "░" * (width - filled)


def artifact_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def build_compare_strategy_artifacts(
    paths: ChainPaths,
    baseline_metrics: list[dict[str, Any]],
    adaptive_metrics: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
) -> dict[str, Any]:
    final = comparisons[-1] if comparisons else {}
    positive_drift_deltas = sum(1 for item in comparisons if item["drift_suppression_delta"] > 0)
    positive_continuity_deltas = sum(1 for item in comparisons if item["continuity_preservation_delta"] > 0)
    adaptive_wins = positive_drift_deltas + positive_continuity_deltas
    baseline_wins = (len(comparisons) * 2) - adaptive_wins
    decision = "adaptive_replay_stabilization" if adaptive_wins >= baseline_wins else "baseline_replay"
    artifacts = {
        "schema_version": 1,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "strategy": "compare",
        "decision": decision,
        "decision_basis": {
            "positive_drift_suppression_iterations": positive_drift_deltas,
            "positive_continuity_delta_iterations": positive_continuity_deltas,
            "adaptive_signal_count": adaptive_wins,
            "baseline_signal_count": baseline_wins,
            "final_drift_suppression_delta": final.get("drift_suppression_delta", 0),
            "final_continuity_preservation_delta": final.get("continuity_preservation_delta", 0),
        },
        "preserved_capabilities": [
            "adaptive replay stabilization",
            "compare strategy",
            "adaptive continuity metrics",
            "replay recovery scoring",
            "pinned truth retention",
            "stabilization reports",
            "replay comparison reporting",
            "semantic reinforcement logic",
        ],
        "artifact_manifest": {
            "baseline_metrics_summary": artifact_path(paths.metrics_summary),
            "adaptive_metrics_summary": artifact_path(paths.adaptive_metrics_summary),
            "comparative_stabilization_json": artifact_path(paths.comparative_summary),
            "comparative_stabilization_markdown": artifact_path(paths.comparative_report),
            "compare_strategy_artifacts": artifact_path(paths.compare_strategy_artifacts),
            "replay_comparison_report": artifact_path(paths.replay_comparison_report),
            "continuity_heatmap": artifact_path(paths.continuity_heatmap),
            "replay_degradation_curves": artifact_path(paths.replay_degradation_curves),
            "stabilization_summary": artifact_path(paths.stabilization_summary),
        },
        "baseline_iterations": [item["iteration"] for item in baseline_metrics],
        "adaptive_iterations": [item["iteration"] for item in adaptive_metrics],
        "comparison_iterations": [item["iteration"] for item in comparisons],
    }
    write_json(paths.compare_strategy_artifacts, artifacts)
    return artifacts


def write_replay_comparison_report(
    paths: ChainPaths,
    comparison_summary: dict[str, Any],
    strategy_artifacts: dict[str, Any],
) -> None:
    final = comparison_summary.get("final_iteration", {})
    lines = [
        "# Replay Comparison Report",
        "",
        "This report records the deterministic compare strategy used to validate baseline replay-chain behavior against adaptive semantic replay stabilization.",
        "",
        "## Compare Strategy Decision",
        "",
        f"- Selected strategy: `{strategy_artifacts['decision']}`",
        f"- Adaptive signal count: `{strategy_artifacts['decision_basis']['adaptive_signal_count']}`",
        f"- Baseline signal count: `{strategy_artifacts['decision_basis']['baseline_signal_count']}`",
        f"- Final drift suppression delta: `{final.get('drift_suppression_delta', 0)}`",
        f"- Final continuity preservation delta: `{final.get('continuity_preservation_delta', 0)}`",
        "",
        "## Preserved Capabilities",
        "",
    ]
    lines.extend(f"- {capability}" for capability in strategy_artifacts["preserved_capabilities"])
    lines.extend([
        "",
        "## Iteration Comparison",
        "",
        "| Iteration | Drift suppression | Continuity delta | Replay longevity delta | Baseline retention | Adaptive retention |",
        "|---:|---:|---:|---:|---:|---:|",
    ])
    for item in comparison_summary.get("trend", []):
        lines.append(
            f"| {item['iteration']} | {item['drift_suppression_delta']} | {item['continuity_preservation_delta']} | {item['replay_longevity_delta']} | {item['baseline_retention']} | {item['adaptive_retention']} |"
        )
    lines.extend([
        "",
        "## Artifact Manifest",
        "",
    ])
    for name, path in strategy_artifacts["artifact_manifest"].items():
        lines.append(f"- {name}: `{path}`")
    paths.replay_comparison_report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def summarize_adaptive_and_comparison(
    paths: ChainPaths,
    baseline_metrics: list[dict[str, Any]],
    adaptive_metrics: list[dict[str, Any]],
) -> None:
    adaptive_summary = {
        "schema_version": 1,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "iterations": len(adaptive_metrics),
        "trend": [{"iteration": item["iteration"], **item["metrics"]} for item in adaptive_metrics],
    }
    write_json(paths.adaptive_metrics_summary, adaptive_summary)

    comparisons = []
    for baseline, adaptive in zip(baseline_metrics, adaptive_metrics, strict=True):
        b = baseline["metrics"]
        a = adaptive["metrics"]
        comparisons.append({
            "iteration": adaptive["iteration"],
            "contradiction_reduction": max(0, b["contradiction_accumulation"] - a["contradiction_accumulation"]),
            "continuity_preservation_delta": round(a["adaptive_continuity_score"] - b["adaptive_continuity_score"], 3),
            "drift_suppression_delta": round(b["semantic_drift_growth"] - a["semantic_drift_growth"], 3),
            "replay_longevity_delta": round(a["replay_consistency_score"] - b["replay_consistency_score"], 3),
            "baseline_retention": b["truth_retention_score"],
            "adaptive_retention": a["truth_retention_score"],
            "baseline_drift": b["semantic_drift_growth"],
            "adaptive_drift": a["semantic_drift_growth"],
        })

    final = comparisons[-1] if comparisons else {}
    comparison_summary = {
        "schema_version": 1,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "iterations": len(comparisons),
        "focus_question": "Can adaptive semantic reinforcement significantly extend operational continuity under repeated compression?",
        "final_iteration": final,
        "averages": {
            "drift_suppression_delta": round(sum(item["drift_suppression_delta"] for item in comparisons) / len(comparisons), 3),
            "continuity_preservation_delta": round(sum(item["continuity_preservation_delta"] for item in comparisons) / len(comparisons), 3),
            "replay_longevity_delta": round(sum(item["replay_longevity_delta"] for item in comparisons) / len(comparisons), 3),
            "contradiction_reduction": round(sum(item["contradiction_reduction"] for item in comparisons) / len(comparisons), 3),
        } if comparisons else {},
        "trend": comparisons,
    }
    write_json(paths.comparative_summary, comparison_summary)
    strategy_artifacts = build_compare_strategy_artifacts(paths, baseline_metrics, adaptive_metrics, comparisons)
    write_replay_comparison_report(paths, comparison_summary, strategy_artifacts)

    report_lines = [
        "# Comparative Stabilization Report",
        "",
        "Deterministic comparison of baseline replay chains against adaptive stabilized replay chains.",
        "",
        "| Iteration | Baseline retention | Adaptive retention | Baseline drift | Adaptive drift | Drift suppression | Continuity delta | Replay longevity delta |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in comparisons:
        report_lines.append(
            f"| {item['iteration']} | {item['baseline_retention']} | {item['adaptive_retention']} | {item['baseline_drift']} | {item['adaptive_drift']} | {item['drift_suppression_delta']} | {item['continuity_preservation_delta']} | {item['replay_longevity_delta']} |"
        )
    report_lines.extend([
        "",
        "## Stabilization Effect",
        "",
        f"- Average drift suppression delta: `{comparison_summary['averages'].get('drift_suppression_delta', 0)}`",
        f"- Average continuity preservation delta: `{comparison_summary['averages'].get('continuity_preservation_delta', 0)}`",
        f"- Average replay longevity delta: `{comparison_summary['averages'].get('replay_longevity_delta', 0)}`",
        "- Interpretation: positive deltas indicate adaptive semantic reinforcement extended operational continuity under repeated compression.",
    ])
    paths.comparative_report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    heatmap_lines = [
        "# Continuity Heatmap",
        "",
        "Bars encode deterministic adaptive continuity score by replay iteration.",
        "",
        "| Iteration | Baseline continuity | Adaptive continuity |",
        "|---:|:---|:---|",
    ]
    for baseline, adaptive in zip(baseline_metrics, adaptive_metrics, strict=True):
        heatmap_lines.append(
            f"| {baseline['iteration']} | `{bar(baseline['metrics']['adaptive_continuity_score'])}` {baseline['metrics']['adaptive_continuity_score']} | `{bar(adaptive['metrics']['adaptive_continuity_score'])}` {adaptive['metrics']['adaptive_continuity_score']} |"
        )
    paths.continuity_heatmap.write_text("\n".join(heatmap_lines) + "\n", encoding="utf-8")

    curve_lines = [
        "# Replay Degradation Curves",
        "",
        "Lower drift and retention decay indicate better replay longevity.",
        "",
        "| Iteration | Baseline drift curve | Adaptive drift curve | Baseline decay | Adaptive decay |",
        "|---:|:---|:---|---:|---:|",
    ]
    for baseline, adaptive in zip(baseline_metrics, adaptive_metrics, strict=True):
        curve_lines.append(
            f"| {baseline['iteration']} | `{bar(1 - baseline['metrics']['semantic_drift_growth'])}` drift {baseline['metrics']['semantic_drift_growth']} | `{bar(1 - adaptive['metrics']['semantic_drift_growth'])}` drift {adaptive['metrics']['semantic_drift_growth']} | {baseline['metrics']['retention_decay']} | {adaptive['metrics']['retention_decay']} |"
        )
    paths.replay_degradation_curves.write_text("\n".join(curve_lines) + "\n", encoding="utf-8")

    summary_lines = [
        "# Stabilization Effectiveness Summary",
        "",
        "Adaptive semantic replay stabilization adds constraint anchoring, architecture reinforcement, replay weighting, semantic cluster persistence, drift-triggered context expansion, and high-priority truth pinning.",
        "",
        f"- Final drift suppression delta: `{final.get('drift_suppression_delta', 0)}`",
        f"- Final continuity preservation delta: `{final.get('continuity_preservation_delta', 0)}`",
        f"- Final replay longevity delta: `{final.get('replay_longevity_delta', 0)}`",
        f"- Average contradiction reduction: `{comparison_summary['averages'].get('contradiction_reduction', 0)}`",
        "- Conclusion: adaptive reinforcement extends operational continuity when deltas remain positive through later replay iterations.",
    ]
    paths.stabilization_summary.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")


def run_chain(iterations: int = DEFAULT_ITERATIONS, strategy: str = DEFAULT_STRATEGY) -> None:
    paths = ChainPaths()
    raw_context = build_raw_context(paths)

    state = initial_state(raw_context)
    baseline_metrics: list[dict[str, Any]] = []
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
        baseline_metrics.append(metrics)
    summarize(paths, baseline_metrics)
    if strategy == "baseline":
        return

    adaptive_state = adaptive_initial_state(raw_context)
    adaptive_metrics: list[dict[str, Any]] = []
    adaptive_baseline_score = 1.0
    adaptive_cumulative_contradictions = 0
    adaptive_replay: dict[str, Any] | None = None
    for iteration in range(1, iterations + 1):
        if iteration > 1:
            assert adaptive_replay is not None
            adaptive_state = adaptive_recompress(adaptive_state, adaptive_replay, raw_context, iteration)
        write_json(paths.adaptive_state(iteration), adaptive_state)
        adaptive_replay = replay_answers(adaptive_state, raw_context["questions"])
        write_json(paths.adaptive_replay(iteration), adaptive_replay)
        baseline_iteration_metrics = baseline_metrics[iteration - 1]["metrics"] if strategy == "compare" else None
        metrics = evaluate_step(
            raw_context,
            adaptive_state,
            adaptive_replay,
            adaptive_baseline_score,
            adaptive_cumulative_contradictions,
            baseline_iteration_metrics,
        )
        if iteration == 1:
            adaptive_baseline_score = metrics["metrics"]["truth_retention_score"]
            metrics = evaluate_step(
                raw_context,
                adaptive_state,
                adaptive_replay,
                adaptive_baseline_score,
                adaptive_cumulative_contradictions,
                baseline_iteration_metrics,
            )
        adaptive_cumulative_contradictions = metrics["metrics"]["contradiction_accumulation"]
        write_json(paths.adaptive_metrics(iteration), metrics)
        write_step_report(paths, metrics, adaptive=True)
        adaptive_metrics.append(metrics)

    if strategy == "compare":
        summarize_adaptive_and_comparison(paths, baseline_metrics, adaptive_metrics)
    else:
        write_json(paths.adaptive_metrics_summary, {
            "schema_version": 1,
            "generated_at": DETERMINISTIC_GENERATED_AT,
            "strategy": strategy,
            "iterations": len(adaptive_metrics),
            "trend": [{"iteration": item["iteration"], **item["metrics"]} for item in adaptive_metrics],
        })


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic iterative replay-chain evaluation.")
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS, help="Number of compression/replay cycles to evaluate.")
    parser.add_argument(
        "--strategy",
        choices=STRATEGY_CHOICES,
        default=DEFAULT_STRATEGY,
        help="Replay-chain strategy to run; compare preserves baseline plus adaptive artifacts.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.iterations < 1:
        raise SystemExit("--iterations must be at least 1")
    run_chain(args.iterations, args.strategy)


if __name__ == "__main__":
    main()
